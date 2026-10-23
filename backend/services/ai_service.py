import asyncio
import os
import re
import shutil
import time
from typing import Optional, Tuple
from backend.models.enums import AIModel, AIProvider
from backend.models.pr_model import PRMetadata
from backend.services.prompt_builder import PromptBuilder


class AIService:
    @staticmethod
    def get_supported_models():
        return [
            {
                "id": AIModel.CLAUDE_SONNET_4_6.value,
                "name": "Claude Sonnet 4.6 (Thinking)",
                "provider": AIProvider.ANTIGRAVITY.value,
                "badge": "Khuyên dùng - Chi tiết cao",
                "recommended": True,
            },
            {
                "id": AIModel.CLAUDE_OPUS_4_6.value,
                "name": "Claude Opus 4.6 (Thinking)",
                "provider": AIProvider.ANTIGRAVITY.value,
                "badge": "Chuyên sâu - Lý luận mạnh",
                "recommended": False,
            },
            {
                "id": AIModel.GEMINI_3_8_FLASH_HIGH.value,
                "name": "Gemini 3.8 Flash (High)",
                "provider": AIProvider.ANTIGRAVITY.value,
                "badge": "Tốc độ cao - Chuẩn xác",
                "recommended": False,
            },
            {
                "id": AIModel.GEMINI_3_8_FLASH_MEDIUM.value,
                "name": "Gemini 3.8 Flash (Medium)",
                "provider": AIProvider.ANTIGRAVITY.value,
                "badge": "Cực nhanh",
                "recommended": False,
            },
        ]

    async def generate_pr_summary(
        self,
        pr: PRMetadata,
        model: AIModel = AIModel.CLAUDE_SONNET_4_6,
        provider: AIProvider = AIProvider.ANTIGRAVITY,
        custom_notes: Optional[str] = None,
    ) -> Tuple[bool, str, float]:
        start_time = time.time()

        prompt = PromptBuilder.build_summary_prompt(pr, custom_notes)

        # Kiểm tra provider
        if provider == AIProvider.ANTIGRAVITY:
            claude_err = ""
            success = False
            # Ưu tiên token Claude CLI cho model Claude; lỗi/không có thì fallback sang Antigravity
            if model.value.startswith("claude"):
                success, output = await self._call_claude_cli(prompt, model.value)
                if not success:
                    claude_err = output
            if not success:
                success, output = await self._call_agy_cli(prompt, model.value)
                if not success and claude_err:
                    output = f"{claude_err}\n{output}"
            elapsed = round(time.time() - start_time, 2)
            if not success:
                return False, output, elapsed
            cleaned = self._clean_markdown(output)
            return True, cleaned, elapsed

        # Fallback provider khác nếu người dùng cung cấp API Key
        elapsed = round(time.time() - start_time, 2)
        return False, f"Provider {provider.value} hiện chưa được cấu hình key.", elapsed

    async def _call_agy_cli(self, prompt: str, model_name: str) -> Tuple[bool, str]:
        agy_path = shutil.which("agy")
        if not agy_path:
            # Tìm trong các thư mục mặc định của hệ thống
            fallback_paths = [
                "/Users/tuan.1495icloud.com/.local/bin/agy",
                os.path.expanduser("~/.local/bin/agy"),
                "/usr/local/bin/agy",
            ]
            for p in fallback_paths:
                if os.path.exists(p):
                    agy_path = p
                    break

        if not agy_path:
            return False, "Không tìm thấy công cụ Antigravity CLI (agy) trên hệ thống."

        # Chạy agy -p <prompt> --model <model_name>
        return await self._run_cli([agy_path, "-p", prompt, "--model", model_name], "Antigravity AI")

    async def _call_claude_cli(self, prompt: str, model_name: str) -> Tuple[bool, str]:
        claude_path = shutil.which("claude") or next(
            (p for p in [os.path.expanduser("~/.claude/local/claude"), "/opt/homebrew/bin/claude"] if os.path.exists(p)),
            None,
        )
        if not claude_path:
            return False, "Không tìm thấy Claude CLI (claude) trên hệ thống."

        # Claude CLI dùng model id chuẩn, không có hậu tố "-thinking" của Antigravity
        return await self._run_cli(
            [claude_path, "-p", prompt, "--model", model_name.removesuffix("-thinking")], "Claude CLI"
        )

    async def _run_cli(self, cmd: list, label: str) -> Tuple[bool, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                err_text = stderr.decode("utf-8", errors="replace").strip()
                return False, f"Lỗi thực thi {label} (Exit {proc.returncode}): {err_text}"

            result = stdout.decode("utf-8", errors="replace").strip()
            if not result:
                return False, "Mô hình AI trả về nội dung rỗng."

            return True, result
        except Exception as e:
            return False, f"Ngoại lệ khi gọi AI: {str(e)}"

    def _clean_markdown(self, text: str) -> str:
        """Loại bỏ bọc code block ```markdown nếu mô hình sinh ra"""
        cleaned = text.strip()
        if cleaned.startswith("```markdown"):
            cleaned = cleaned[len("```markdown") :].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```") :].strip()

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        return cleaned
