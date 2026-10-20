"""The confidentiality check: what must never reach a public post."""

import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from linkedin_ia.config import Config

MAX_LENGTH = 3000

ZERO_WIDTH = re.compile("[\u00ad\u200b-\u200d\u2060\ufeff]")
DASHES = re.compile("[\u2010-\u2015\u2212\ufe58\ufe63\uff0d]")
OBFUSCATED_DOT = re.compile(r"\[\.\]|\(\.\)")
TERM_SEPARATOR = r"[\s_-]+"

# Uppercase keys tolerate a spaced hyphen or a space; any-case keys need a plain hyphen and
# 3+ digits, so prose like "top-10", "Etapa - 1" or "llama-3" stays clean.
ISSUE_PATTERNS = (
    re.compile(r"(?<![\w-])[A-Z][A-Z0-9]{1,9}\s?-\s?\d{1,6}(?!\w)"),
    re.compile(r"(?<![\w-])[A-Za-z]{2}[A-Za-z0-9]{0,8}-\d{3,6}(?!\w)"),
    re.compile(r"\b[A-Z][A-Z0-9]{2,9} \d{4,6}\b"),
)
SOURCE_FILE = re.compile(r"\b[\w-]+\.(?:prw|prx|tlpp|aph|ch)\b|\bU_\w+", re.IGNORECASE)
EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63})+")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
CREDENTIAL = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}"
    r"|xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[A-Z0-9]{16}|AIza[0-9A-Za-z_-]{30,}"
    r"|[sr]k_(?:live|test)_[0-9A-Za-z]{16,}|eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]+)"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|hooks\.slack\.com/services/\S+"
    r"|(?i:\b(?:password|passwd|senha|secret|token|api[_-]?key)\s*[:=]\s*[\"']?"
    r"(?=[^\s\"']*\d)[^\s\"']{6,})"
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    text: str


def post_bodies(text: str) -> list[tuple[int, list[str]]]:
    """Every `## Post` section: the number of its first line, and its lines."""
    lines = text.splitlines()
    sections = []
    for index, line in enumerate(lines):
        if line.strip() == "## Post":
            body = []
            for following in lines[index + 1 :]:
                if following.startswith("## "):
                    break
                body.append(following)
            sections.append((index + 2, body))
    return sections


def normalize(line: str) -> str:
    """Undo the reformatting that hides a pattern: zero-width characters, dash variants, [.]"""
    line = unicodedata.normalize("NFKC", ZERO_WIDTH.sub("", line))
    return OBFUSCATED_DOT.sub(".", DASHES.sub("-", line))


def fold(text: str) -> str:
    """Drop accents one character at a time, so spans in the result match the original."""
    folded = []
    for char in text:
        base = "".join(
            c for c in unicodedata.normalize("NFKD", char) if not unicodedata.combining(c)
        )
        folded.append(base if len(base) == 1 else char)
    return "".join(folded)


def _mask(text: str, terms: tuple[str, ...]) -> str:
    """Blank out allowed terms, matching `ISO-8601` as `iso 8601` or `ISO - 8601` too."""
    for term in terms:
        parts = [re.escape(p) for p in re.split(r"[\s-]+", term) if p]
        pattern = r"\s?-?\s?".join(parts)
        text = re.sub(pattern, lambda m: " " * len(m.group(0)), text, flags=re.IGNORECASE)
    return text


def _domain(domain: str) -> re.Pattern[str]:
    host = re.escape(domain.strip(".").lower())
    return re.compile(rf"(?<![\w.-])(?:[\w-]+\.)*{host}(?![\w-]|\.[\w-])", re.IGNORECASE)


def _term(term: str) -> re.Pattern[str]:
    words = [re.escape(w) + "s?" for w in fold(term).split()]
    return re.compile(rf"\b{TERM_SEPARATOR.join(words)}\b", re.IGNORECASE)


def _matches(text: str, config: Config) -> Iterator[tuple[int, int, str]]:
    masked = _mask(text, config.allowed_terms)
    issues = {m.span() for pattern in ISSUE_PATTERNS for m in pattern.finditer(masked)}
    for start, end in sorted(issues):
        yield start, end, "issue"
    for rule, pattern in (("fonte", SOURCE_FILE), ("email", EMAIL), ("ip", IPV4)):
        for match in pattern.finditer(text):
            yield match.start(), match.end(), rule
    for domain in config.internal_domains:
        for match in _domain(domain).finditer(text):
            yield match.start(), match.end(), "dominio-interno"
    for match in CREDENTIAL.finditer(text):
        yield match.start(), match.end(), "credencial"
    folded = fold(text)
    for term in config.forbidden_terms:
        for match in _term(term).finditer(folded):
            yield match.start(), match.end(), "termo-proibido"


def _section_findings(
    path: Path, first: int, lines: list[str], config: Config
) -> Iterator[Finding]:
    normalized = [normalize(line) for line in lines]
    for offset, line in enumerate(normalized):
        for start, end, rule in _matches(line, config):
            yield Finding(path, first + offset, rule, line[start:end])
        if offset + 1 < len(normalized):
            # A pattern split across a line break: report only matches that cross it.
            joined = f"{line} {normalized[offset + 1]}"
            for start, end, rule in _matches(joined, config):
                if start < len(line) and end > len(line) + 1:
                    yield Finding(path, first + offset, rule, joined[start:end])
    length = len("\n".join(lines).strip())
    if length > MAX_LENGTH:
        yield Finding(path, first - 1, "tamanho", f"{length} caracteres")


def check(path: Path, config: Config) -> list[Finding]:
    sections = post_bodies(path.read_text(encoding="utf-8"))
    if not sections:
        return [Finding(path, 1, "formato", "sem seção ## Post")]
    findings: list[Finding] = []
    for first, lines in sections:
        findings += _section_findings(path, first, lines, config)
    return sorted(findings, key=lambda f: f.line)


def text_findings(text: str, path: Path, config: Config) -> list[Finding]:
    """The rules applied to a piece of text that is not a `## Post` section."""
    return list(_section_findings(path, 1, text.splitlines(), config))


def disabled_rules(config: Config) -> list[str]:
    """Rules that cannot fire because their list in config.toml is empty."""
    empty = []
    if not config.forbidden_terms:
        empty.append("termos_proibidos")
    if not config.internal_domains:
        empty.append("dominios_internos")
    return empty
