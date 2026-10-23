import logging
import re
import json
import asyncio
import shutil
from typing import Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

from backend.models.enums import PRFetchSource
from backend.models.pr_model import PRMetadata, PRFileChange


class GitHubService:
    IGNORE_EXTENSIONS = (
        ".lock",
        "-lock.json",
        ".lockb",
        ".min.js",
        ".min.css",
        ".map",
        ".svg",
        ".png",
        ".jpg",
        ".jpeg",
        ".ico",
    )
    MAX_DIFF_CHARS = 45000  # Token-friendly budget

    @staticmethod
    def parse_pr_url(url: str) -> Optional[Tuple[str, str, int]]:
        """
        Trích xuất (owner, repo, pr_number) từ URL GitHub PR.
        Hỗ trợ:
        - https://github.com/owner/repo/pull/123
        - https://github.com/owner/repo/pull/123/files
        """
        if not url:
            return None

        pattern = r"github\.com[/:]([\w.-]+)/([\w.-]+)/pull/(\d+)"
        match = re.search(pattern, url.strip())
        if not match:
            return None

        owner, repo, number = match.groups()
        return owner, repo, int(number)

    async def fetch_pr(self, url: str, github_token: Optional[str] = None) -> Optional[PRMetadata]:
        parsed = self.parse_pr_url(url)
        if not parsed:
            return None

        owner, repo, number = parsed

        # Ưu tiên sử dụng gh CLI nếu đã cài đặt
        gh_path = shutil.which("gh")
        if gh_path:
            meta = await self._fetch_via_gh_cli(owner, repo, number, url)
            if meta:
                return meta

        # Fallback qua GitHub REST API
        return await self._fetch_via_api(owner, repo, number, url, github_token)

    async def _fetch_via_gh_cli(
        self, owner: str, repo: str, number: int, url: str
    ) -> Optional[PRMetadata]:
        repo_slug = f"{owner}/{repo}"
        try:
            # Lấy thông tin PR dưới dạng JSON
            proc = await asyncio.create_subprocess_exec(
                "gh",
                "pr",
                "view",
                str(number),
                "--repo",
                repo_slug,
                "--json",
                "title,body,author,baseRefName,headRefName,commits,files,additions,deletions",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                err_text = stderr.decode("utf-8", errors="replace").strip()
                logger.warning("gh CLI exited with code %d for %s/%s#%d: %s", proc.returncode, owner, repo, number, err_text)
                return None

            data = json.loads(stdout.decode("utf-8"))

            # Lấy diff
            diff_proc = await asyncio.create_subprocess_exec(
                "gh",
                "pr",
                "diff",
                str(number),
                "--repo",
                repo_slug,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            diff_stdout, _ = await diff_proc.communicate()
            raw_diff = diff_stdout.decode("utf-8", errors="replace")

            # Parse files
            files_list = []
            for f in data.get("files", []):
                files_list.append(
                    PRFileChange(
                        path=f.get("path", ""),
                        additions=f.get("additions", 0),
                        deletions=f.get("deletions", 0),
                    )
                )

            # Lọc diff thông minh
            cleaned_diff = self._filter_diff(raw_diff)

            commit_msgs = [c.get("messageHeadline", "") for c in data.get("commits", []) if c.get("messageHeadline")]

            return PRMetadata(
                owner=owner,
                repo=repo,
                number=number,
                title=data.get("title", ""),
                author=data.get("author", {}).get("login", ""),
                base_branch=data.get("baseRefName", ""),
                head_branch=data.get("headRefName", ""),
                url=url,
                body=data.get("body", "") or "",
                commits=commit_msgs,
                files=files_list,
                total_additions=data.get("additions", 0),
                total_deletions=data.get("deletions", 0),
                diff_text=cleaned_diff,
                fetch_source=PRFetchSource.GH_CLI,
            )
        except Exception as exc:
            logger.warning("gh CLI fetch failed for %s/%s#%d: %s", owner, repo, number, exc)
            return None

    async def _fetch_via_api(
        self, owner: str, repo: str, number: int, url: str, token: Optional[str] = None
    ) -> Optional[PRMetadata]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Auto-PR-Generator-App",
        }
        if token:
            headers["Authorization"] = f"token {token}"

        api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.get(api_base, headers=headers)
                if res.status_code != 200:
                    logger.warning(
                        "GitHub API returned %d for %s/%s#%d (token=%s)",
                        res.status_code, owner, repo, number, "yes" if token else "no"
                    )
                    return None

                data = res.json()

                # Lấy diff
                diff_headers = dict(headers)
                diff_headers["Accept"] = "application/vnd.github.v3.diff"
                diff_res = await client.get(api_base, headers=diff_headers)
                raw_diff = diff_res.text if diff_res.status_code == 200 else ""

                # Lấy commits
                commits_res = await client.get(f"{api_base}/commits", headers=headers)
                commit_msgs = []
                if commits_res.status_code == 200:
                    for c in commits_res.json():
                        msg = c.get("commit", {}).get("message", "").split("\n")[0]
                        if msg:
                            commit_msgs.append(msg)

                # Lấy danh sách files
                files_res = await client.get(f"{api_base}/files", headers=headers)
                files_list = []
                if files_res.status_code == 200:
                    for f in files_res.json():
                        files_list.append(
                            PRFileChange(
                                path=f.get("filename", ""),
                                additions=f.get("additions", 0),
                                deletions=f.get("deletions", 0),
                                change_type=f.get("status", "modified"),
                            )
                        )

                cleaned_diff = self._filter_diff(raw_diff)

                return PRMetadata(
                    owner=owner,
                    repo=repo,
                    number=number,
                    title=data.get("title", ""),
                    author=data.get("user", {}).get("login", ""),
                    base_branch=data.get("base", {}).get("ref", ""),
                    head_branch=data.get("head", {}).get("ref", ""),
                    url=url,
                    body=data.get("body", "") or "",
                    commits=commit_msgs,
                    files=files_list,
                    total_additions=data.get("additions", 0),
                    total_deletions=data.get("deletions", 0),
                    diff_text=cleaned_diff,
                    fetch_source=PRFetchSource.GITHUB_API,
                )
        except Exception as exc:
            logger.warning("GitHub API fetch failed for %s/%s#%d: %s", owner, repo, number, exc)
            return None

    def _filter_diff(self, diff: str) -> str:
        """Loại bỏ file khóa, bundle lớn và cắt bớt nếu vượt quá giới hạn"""
        if not diff:
            return ""

        chunks = diff.split("diff --git ")
        kept_chunks = []

        for chunk in chunks:
            if not chunk.strip():
                continue

            first_line = chunk.split("\n", 1)[0]
            # Kiểm tra xem có thuộc danh sách bỏ qua không
            should_skip = any(ext in first_line for ext in self.IGNORE_EXTENSIONS)
            if should_skip:
                continue

            kept_chunks.append("diff --git " + chunk)

        result = "".join(kept_chunks)
        if len(result) > self.MAX_DIFF_CHARS:
            return result[: self.MAX_DIFF_CHARS] + "\n\n... [Diff truncated for AI token budget] ..."

        return result
