from enum import Enum


class AIProvider(str, Enum):
    ANTIGRAVITY = "antigravity"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class AIModel(str, Enum):
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_OPUS_4_6 = "claude-opus-4-6-thinking"
    GEMINI_3_8_FLASH_HIGH = "gemini-3.8-flash-high"
    GEMINI_3_8_FLASH_MEDIUM = "gemini-3.8-flash-medium"


class ChangeType(str, Enum):
    BUGFIX = "Bugfix"
    FEATURE = "Feature"
    PERFORMANCE = "Performance"
    SECURITY = "Security"
    DATABASE_CHANGES = "Database changes"
    BREAKING_CHANGE = "BREAKING CHANGE"
    BOTH_FE_AND_BE = "Both FE and BE (note different deployment time)"


class PRFetchSource(str, Enum):
    GH_CLI = "gh_cli"
    GITHUB_API = "github_api"
    MANUAL = "manual"


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
