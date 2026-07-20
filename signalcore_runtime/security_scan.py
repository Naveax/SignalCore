from __future__ import annotations

import base64
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

_ANSI = re.compile(r"\x1b(?:[@-_][0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)

_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("generic-assignment", re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|authorization|password|passwd|secret|bearer|"
        r"private[_-]?key|client[_-]?secret|session[_-]?id|cookie)\b\s*[:=]\s*([^\s,;]+)"
    )),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,255}|github_pat_[A-Za-z0-9_]{20,255})\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("database-uri", re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s]+")),
    ("private-key", re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----.*?-----END(?: [A-Z0-9]+)? PRIVATE KEY-----", re.S)),
)

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?is)(ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions|"
        r"do\s+not\s+follow\s+(?:the\s+)?(?:system|developer)|"
        r"reveal\s+(?:the\s+)?(?:system\s+)?prompt|"
        r"you\s+are\s+(?:chatgpt|an?\s+assistant)|"
        r"<\/?(?:system|assistant|developer|tool)>|"
        r"system\s+message\s*:|developer\s+message\s*:)")
    ,
    re.compile(
        r"(?is)(önceki\s+(?:tüm\s+)?talimatları\s+(?:yoksay|unut)|"
        r"sistem\s+istemini\s+(?:göster|açıkla)|"
        r"geliştirici\s+mesajını\s+(?:göster|ifşa\s+et))")
    ,
    re.compile(
        r"(?is)(ignora\s+(?:todas\s+)?las\s+instrucciones\s+anteriores|"
        r"忽略(?:之前|所有).*指令|"
        r"以前の指示を.*無視)")
    ,
)

# Assignment delimiters are intentionally allowed immediately before the token.
_BASE64_TOKEN = re.compile(r"(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{40,}={0,2}(?![A-Za-z0-9+/_-])")


@dataclass(frozen=True)
class SecurityScan:
    normalized_text: str
    redacted_text: str
    secret_types: tuple[str, ...]
    injection_risk: bool
    injection_reasons: tuple[str, ...]
    encoded_payloads_checked: int

    @property
    def secrets_found(self) -> int:
        return len(self.secret_types)


def normalize_untrusted_text(text: str) -> str:
    value = _ANSI.sub("", text)
    value = unicodedata.normalize("NFKC", value).translate(_ZERO_WIDTH)
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _redact_pattern(text: str, name: str, pattern: re.Pattern[str]) -> tuple[str, bool]:
    found = False

    def replace(match: re.Match[str]) -> str:
        nonlocal found
        found = True
        if name == "generic-assignment" and match.lastindex and match.lastindex >= 1:
            return f"{match.group(1)}=<redacted:{name}>"
        if name == "private-key":
            return "-----BEGIN PRIVATE KEY-----<redacted:private-key>-----END PRIVATE KEY-----"
        return f"<redacted:{name}>"

    return pattern.sub(replace, text), found


def _decode_candidates(text: str, *, limit: int = 16) -> Iterable[str]:
    checked = 0
    for match in _BASE64_TOKEN.finditer(text):
        if checked >= limit:
            break
        token = match.group(0)
        checked += 1
        padded = token + "=" * ((4 - len(token) % 4) % 4)
        for altchars in (None, b"-_"):
            try:
                raw = base64.b64decode(padded, altchars=altchars, validate=False)
                decoded = raw.decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                continue
            if 8 <= len(decoded) <= 8192:
                yield decoded
                break


def scan_text(text: str, *, inspect_encoded: bool = True) -> SecurityScan:
    normalized = normalize_untrusted_text(text)
    redacted = normalized
    secret_types: list[str] = []
    for name, pattern in _SECRET_PATTERNS:
        redacted, found = _redact_pattern(redacted, name, pattern)
        if found:
            secret_types.append(name)

    reasons: list[str] = []
    for index, pattern in enumerate(_INJECTION_PATTERNS):
        if pattern.search(normalized):
            reasons.append(f"direct-pattern-{index + 1}")

    checked = 0
    if inspect_encoded:
        for decoded in _decode_candidates(normalized):
            checked += 1
            normalized_decoded = normalize_untrusted_text(decoded)
            if any(pattern.search(normalized_decoded) for pattern in _INJECTION_PATTERNS):
                reasons.append("encoded-instruction")
                break

    return SecurityScan(
        normalized,
        redacted,
        tuple(dict.fromkeys(secret_types)),
        bool(reasons),
        tuple(dict.fromkeys(reasons)),
        checked,
    )


def scan_bytes(data: bytes, *, max_scan_bytes: int = 2 * 1024 * 1024) -> SecurityScan:
    sample = data[:max_scan_bytes].decode("utf-8", errors="replace")
    return scan_text(sample)


def redact_text(text: str) -> str:
    return scan_text(text, inspect_encoded=False).redacted_text
