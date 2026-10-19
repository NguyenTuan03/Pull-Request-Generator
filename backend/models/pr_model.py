from typing import List, Optional
from pydantic import BaseModel, Field
from backend.models.enums import AIModel, AIProvider, ResponseStatus, PRFetchSource


class PRFileChange(BaseModel):
    path: str
    additions: int = 0
    deletions: int = 0
    change_type: str = "modified"


class PRMetadata(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    author: str = ""
    base_branch: str = ""
    head_branch: str = ""
    url: str
    body: str = ""
    commits: List[str] = Field(default_factory=list)
    files: List[PRFileChange] = Field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    diff_text: str = ""
    fetch_source: PRFetchSource = PRFetchSource.GH_CLI


class PRSummarizeRequest(BaseModel):
    pr_url: str
    model: AIModel = AIModel.CLAUDE_SONNET_4_6
    provider: AIProvider = AIProvider.ANTIGRAVITY
    custom_notes: Optional[str] = None
    github_token: Optional[str] = None


class PRSummarizeResponse(BaseModel):
    status: ResponseStatus
    pr_url: str
    pr_title: str
    summary_markdown: str = ""
    model_used: str = ""
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Optional[PRMetadata] = None


class PRParseRequest(BaseModel):
    pr_url: str
    github_token: Optional[str] = None


class PRParseResponse(BaseModel):
    status: ResponseStatus
    metadata: Optional[PRMetadata] = None
    error_message: Optional[str] = None


class HistoryItem(BaseModel):
    id: str
    created_at: str
    pr_url: str
    pr_title: str
    model_used: str
    summary_markdown: str
