"""Member status constants."""


class Status:
    JOINED = "joined"
    PROMPT_SENT = "prompt_sent"
    APPROVED = "approved"
    PENDING_RETRY = "pending_retry"
    REMOVED_TIMEOUT = "removed_timeout"
    REMOVED_MANUAL = "removed_manual"
    LEFT = "left"
    ERROR = "error"

    PENDING = {JOINED, PROMPT_SENT}
    RESPONDABLE = {JOINED, PROMPT_SENT, PENDING_RETRY}
