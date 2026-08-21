import ipaddress
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agentx.tools.schemas import ToolSecurityError

# Regex patterns matching prompt injection and instruction override attempts
INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
    re.compile(r"admin\s+override\s*:", re.IGNORECASE),
    re.compile(r"<\s*\|\s*(im_start|im_end|system|user|assistant)\s*\|\s*>", re.IGNORECASE),
    re.compile(r"\[\s*INST\s*\].*?\[\s*/INST\s*\]", re.IGNORECASE | re.DOTALL),
]

# Regex patterns matching sensitive credentials, tokens, and private keys for automated redaction
SENSITIVE_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("GOOGLE_API_KEY", re.compile(r"AIza[0-9A-Za-z-_]{30,45}")),
    ("GITHUB_PAT", re.compile(r"(?:ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})")),
    ("AWS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("BEARER_JWT", re.compile(r"Bearer\s+([A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)")),
    (
        "PRIVATE_KEY",
        re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"),
    ),
]

# Sensitive files and directories strictly forbidden from direct tool operations
DEFAULT_FORBIDDEN_PATTERNS: list[str] = [
    ".git",
    ".env",
    "id_rsa",
    "id_ed25519",
    "service_account.json",
    "credentials.json",
    "etc/shadow",
    "etc/passwd",
    "System32",
]

# Forbidden hostname targets for SSRF defense (loopback, metadata, link-local)
FORBIDDEN_HOSTNAMES: set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
}


def wrap_untrusted_content(
    content: str,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Wraps external, unverified content into strict untrusted data boundaries.

    Neutralizes prompt injection keywords, strips escape tags, and encloses the content
    within deterministic XML demarcation tags to prevent LLM system instruction overrides.
    """
    sanitized = content

    # 1. Neutralize injection patterns
    for pat in INJECTION_PATTERNS:
        sanitized = pat.sub("[REDACTED_PROMPT_INJECTION_ATTEMPT]", sanitized)

    # 2. Escape XML closure delimiters to prevent tag breakout
    sanitized = sanitized.replace("</untrusted_content>", "<\\/untrusted_content>")

    meta_str = ""
    if metadata:
        meta_items = [
            f'{k}="{v}"' for k, v in sorted(metadata.items()) if isinstance(v, (str, int, float))
        ]
        if meta_items:
            meta_str = " " + " ".join(meta_items)

    return f'<untrusted_content source="{source}"{meta_str}>\n{sanitized}\n</untrusted_content>'


def sanitize_path(
    path_str: str,
    allowed_paths: list[str] | None = None,
    forbidden_paths: list[str] | None = None,
) -> Path:
    """Validates and canonicalizes a file system path against sandbox boundary rules.

    Raises ToolSecurityError if path traversal or forbidden paths are accessed.
    """
    if not path_str or not path_str.strip():
        raise ToolSecurityError(tool_name="filesystem", message="Path cannot be empty")

    # Canonicalize
    raw_path = Path(path_str).expanduser()
    try:
        resolved = raw_path.resolve()
    except Exception as e:
        raise ToolSecurityError(
            tool_name="filesystem", message=f"Path resolution failed: {str(e)}"
        ) from e

    resolved_str = str(resolved)
    norm_resolved = resolved_str.lower().replace("\\", "/")

    # Check forbidden patterns
    all_forbidden = list(DEFAULT_FORBIDDEN_PATTERNS) + (forbidden_paths or [])
    for forb in all_forbidden:
        norm_forb = forb.lower().replace("\\", "/")
        if norm_forb in norm_resolved or forb.lower() in resolved_str.lower():
            raise ToolSecurityError(
                tool_name="filesystem",
                message=f"Access to forbidden path '{resolved_str}' containing '{forb}' is blocked",
            )

    # Check allowed paths if configured
    if allowed_paths:
        is_allowed = False
        for allowed in allowed_paths:
            allowed_res = Path(allowed).resolve()
            try:
                # Check if resolved path is relative to / inside allowed root
                _ = resolved.relative_to(allowed_res)
                is_allowed = True
                break
            except ValueError:
                continue

        if not is_allowed:
            raise ToolSecurityError(
                tool_name="filesystem",
                message=f"Path '{resolved_str}' is outside allowed workspace boundaries: {allowed_paths}",
            )

    return resolved


def validate_url_for_ssrf(url_str: str) -> str:
    """Validates destination URL against SSRF attack vectors.

    Blocks private RFC 1918 subnets, cloud instance metadata endpoints (169.254.169.254),
    loopback addresses (127.0.0.1, ::1), and non-HTTP(S) schemes.
    """
    if not url_str or not url_str.strip():
        raise ToolSecurityError(tool_name="network", message="URL cannot be empty")

    parsed = urlparse(url_str.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise ToolSecurityError(
            tool_name="network",
            message=f"Disallowed URL scheme '{parsed.scheme}'. Only http and https are permitted.",
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ToolSecurityError(tool_name="network", message=f"Invalid URL hostname in '{url_str}'")

    if hostname in FORBIDDEN_HOSTNAMES:
        raise ToolSecurityError(
            tool_name="network",
            message=f"Access to blocked internal/metadata destination '{hostname}' is denied (SSRF Defense)",
        )

    # Check IP addresses against private / loopback / link-local subnets
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast:
            raise ToolSecurityError(
                tool_name="network",
                message=f"Direct access to private or internal IP range '{hostname}' is denied (SSRF Defense)",
            )
    except ValueError:
        # Hostname is a domain name (not a raw IP literal)
        pass

    return url_str


def redact_sensitive_tokens(text: str) -> str:
    """Redacts API keys, bearer JWT tokens, GitHub PATs, and private keys from logs and text."""
    if not text:
        return ""

    redacted = text
    for token_name, pattern in SENSITIVE_SECRET_PATTERNS:
        redacted = pattern.sub(f"[REDACTED_{token_name}]", redacted)

    return redacted
