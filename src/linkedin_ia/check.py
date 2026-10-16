"""The confidentiality check: what must never reach a public post."""

import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from linkedin_ia.config import Config

MAX_LENGTH = 3000

ISSUE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d{1,6}\b")
SOURCE_FILE = re.compile(r"\b[\w-]+\.(?:prw|prx|tlpp|aph|ch)\b", re.IGNORECASE)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
URL = re.compile(r"https?://([^/\s:?#]+)\S*")
CREDENTIAL = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}"
    r"|xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[A-Z0-9]{16})"
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    text: str


def post_body(text: str) -> tuple[int, list[str]] | None:
    """The `## Post` section: the number of its first line, and its lines."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## Post":
            body = []
            for following in lines[index + 1 :]:
                if following.startswith("## "):
                    break
                body.append(following)
            return index + 2, body
    return None


def fold(text: str) -> str:
    """Drop accents one character at a time, so spans in the result match the original."""
    folded = []
    for char in text:
        base = "".join(
            c for c in unicodedata.normalize("NFKD", char) if not unicodedata.combining(c)
        )
        folded.append(base if len(base) == 1 else char)
    return "".join(folded)


def _mask(line: str, terms: tuple[str, ...]) -> str:
    for term in terms:
        line = line.replace(term, " " * len(term))
    return line


def _line_findings(line: str, config: Config) -> Iterator[tuple[str, str]]:
    for match in ISSUE.finditer(_mask(line, config.allowed_terms)):
        yield "issue", match.group(0)
    for rule, pattern in (("fonte", SOURCE_FILE), ("email", EMAIL), ("ip", IPV4)):
        for match in pattern.finditer(line):
            yield rule, match.group(0)
    for match in URL.finditer(line):
        host = match.group(1).lower()
        if any(host == d or host.endswith("." + d) for d in config.internal_domains):
            yield "dominio-interno", match.group(0)
    for match in CREDENTIAL.finditer(line):
        yield "credencial", match.group(0)
    folded = fold(line)
    for term in config.forbidden_terms:
        for match in re.finditer(rf"\b{re.escape(fold(term))}\b", folded, re.IGNORECASE):
            yield "termo-proibido", line[match.start() : match.end()]


def check(path: Path, config: Config) -> list[Finding]:
    section = post_body(path.read_text(encoding="utf-8"))
    if section is None:
        return [Finding(path, 1, "formato", "sem seção ## Post")]
    first, lines = section
    findings = [
        Finding(path, first + offset, rule, text)
        for offset, line in enumerate(lines)
        for rule, text in _line_findings(line, config)
    ]
    length = len("\n".join(lines).strip())
    if length > MAX_LENGTH:
        findings.append(Finding(path, first - 1, "tamanho", f"{length} caracteres"))
    return findings
