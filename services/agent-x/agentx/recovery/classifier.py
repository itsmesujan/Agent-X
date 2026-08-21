"""Agent-X Error Classifier for Mapping Raw Exceptions to the 9 Failure Categories."""

from agentx.recovery.schemas import FailureCategory

# Regex and pattern definitions for deterministic failure classification
CLASSIFICATION_RULES: list[tuple[FailureCategory, list[str]]] = [
    (
        FailureCategory.PERMISSION,
        [
            "permission denied",
            "permissionerror",
            "unauthorized",
            "401",
            "403",
            "access denied",
            "forbidden",
            "roles/secretmanager",
            "roles/resourcemanager",
            "invalid_grant",
        ],
    ),
    (
        FailureCategory.RESOURCE,
        [
            "budget exhausted",
            "budgetexhaustederror",
            "token budget exceeded",
            "out of memory",
            "quota exceeded",
            "insufficient quota",
            "resource limit reached",
        ],
    ),
    (
        FailureCategory.TRANSIENT,
        [
            "timeout",
            "timed out",
            "connection reset",
            "connection refused",
            "connectionerror",
            "timeouterror",
            "502 bad gateway",
            "503 service unavailable",
            "504 gateway timeout",
            "429 too many requests",
            "resource_exhausted",
            "rate limit",
            "econnreset",
            "etimedout",
        ],
    ),
    (
        FailureCategory.ENVIRONMENT,
        [
            "modulenotfounderror",
            "importerror",
            "missing environment variable",
            "command not found",
            "executable not found",
            "nosuchfileorexception",
            "env var not set",
        ],
    ),
    (
        FailureCategory.TOOL,
        [
            "toolexecutionerror",
            "tool failed",
            "tool crashed",
            "subprocess failed",
            "calledprocesserror",
            "tool error",
        ],
    ),
    (
        FailureCategory.DATA,
        [
            "validationerror",
            "jsondecodeerror",
            "invalid json",
            "schema mismatch",
            "keyerror",
            "typeerror",
            "malformed data",
            "extra inputs are not permitted",
        ],
    ),
    (
        FailureCategory.MODEL,
        [
            "prompt injection",
            "promptinjectionerror",
            "model refused",
            "safety filter",
            "context length exceeded",
            "malformed model output",
            "blocked by safety settings",
        ],
    ),
    (
        FailureCategory.LOGIC,
        [
            "assertionerror",
            "assertion failed",
            "test failed",
            "invariant broken",
            "zerodivisionerror",
            "indexerror",
            "valueerror",
        ],
    ),
]


class ErrorClassifier:
    """Classifies runtime errors and exceptions into one of the 9 canonical FailureCategories."""

    @classmethod
    def classify(cls, error: Exception | str) -> tuple[FailureCategory, str]:
        """Classify an exception or error string into (FailureCategory, error_type_name)."""
        if isinstance(error, Exception):
            err_type = type(error).__name__
            err_msg = f"{err_type}: {str(error)}"
        else:
            err_type = "RawErrorString"
            err_msg = str(error)

        normalized_msg = err_msg.lower()

        for category, patterns in CLASSIFICATION_RULES:
            for pattern in patterns:
                if pattern in normalized_msg:
                    return category, err_type

        return FailureCategory.UNKNOWN, err_type
