from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.models.enums import ResponseStatus
from backend.models.pr_model import (
    PRSummarizeRequest,
    PRSummarizeResponse,
    PRParseRequest,
    PRParseResponse,
)
from backend.services.github_service import GitHubService
from backend.services.ai_service import AIService
from backend.services.history_service import HistoryService

router = APIRouter(prefix="/api", tags=["Pull Request"])

github_service = GitHubService()
ai_service = AIService()
history_service = HistoryService()


class UpdatePRRequest(BaseModel):
    pr_url: str
    body_markdown: str


@router.get("/models")
async def get_models():
    """Lấy danh sách các mô hình AI được hỗ trợ"""
    models = ai_service.get_supported_models()
    return {"status": ResponseStatus.SUCCESS, "models": models}


@router.post("/pr/parse", response_model=PRParseResponse)
async def parse_pr(req: PRParseRequest):
    """Trích xuất thông tin sơ bộ của Pull Request từ URL"""
    if not req.pr_url or not req.pr_url.strip():
        return PRParseResponse(
            status=ResponseStatus.ERROR,
            error_message="Vui lòng cung cấp đường dẫn GitHub Pull Request hợp lệ.",
        )

    parsed = github_service.parse_pr_url(req.pr_url)
    if not parsed:
        return PRParseResponse(
            status=ResponseStatus.ERROR,
            error_message="Định dạng URL không hợp lệ. Ví dụ chuẩn: https://github.com/owner/repo/pull/123",
        )

    pr_metadata = await github_service.fetch_pr(req.pr_url, req.github_token)
    if not pr_metadata:
        return PRParseResponse(
            status=ResponseStatus.ERROR,
            error_message="Không thể tìm thấy PR hoặc không có quyền truy cập repo (hãy kiểm tra repo private/gh auth).",
        )

    return PRParseResponse(
        status=ResponseStatus.SUCCESS,
        metadata=pr_metadata,
    )


@router.post("/summarize", response_model=PRSummarizeResponse)
async def summarize_pr(req: PRSummarizeRequest):
    """Tóm tắt Pull Request và sinh Description chuẩn Markdown bằng AI"""
    if not req.pr_url or not req.pr_url.strip():
        return PRSummarizeResponse(
            status=ResponseStatus.ERROR,
            pr_url="",
            pr_title="",
            error_message="Vui lòng nhập đường dẫn GitHub Pull Request.",
        )

    # 1. Trích xuất PR data
    pr_metadata = await github_service.fetch_pr(req.pr_url, req.github_token)
    if not pr_metadata:
        return PRSummarizeResponse(
            status=ResponseStatus.ERROR,
            pr_url=req.pr_url,
            pr_title="",
            error_message="Không thể tải dữ liệu PR từ GitHub. Vui lòng kiểm tra lại URL hoặc kết nối mạng.",
        )

    # 2. Gọi AI tóm tắt
    success, summary_markdown, elapsed = await ai_service.generate_pr_summary(
        pr=pr_metadata,
        model=req.model,
        provider=req.provider,
        custom_notes=req.custom_notes,
    )

    if not success:
        return PRSummarizeResponse(
            status=ResponseStatus.ERROR,
            pr_url=req.pr_url,
            pr_title=pr_metadata.title,
            execution_time_seconds=elapsed,
            error_message=summary_markdown,
            metadata=pr_metadata,
        )

    # 3. Lưu lịch sử
    history_service.save_item(
        pr_url=req.pr_url,
        pr_title=pr_metadata.title,
        model_used=req.model.value,
        summary_markdown=summary_markdown,
    )

    return PRSummarizeResponse(
        status=ResponseStatus.SUCCESS,
        pr_url=req.pr_url,
        pr_title=pr_metadata.title,
        summary_markdown=summary_markdown,
        model_used=req.model.value,
        execution_time_seconds=elapsed,
        metadata=pr_metadata,
    )


@router.get("/history")
async def get_history():
    """Lấy danh sách các PR đã tóm tắt gần đây"""
    items = history_service.get_recent(limit=20)
    return {"status": ResponseStatus.SUCCESS, "history": items}


@router.delete("/history")
async def clear_history():
    """Xóa toàn bộ lịch sử tóm tắt"""
    success = history_service.clear()
    if not success:
        raise HTTPException(status_code=500, detail="Không thể xóa lịch sử.")
    return {"status": ResponseStatus.SUCCESS, "message": "Đã xóa lịch sử tóm tắt thành công."}
