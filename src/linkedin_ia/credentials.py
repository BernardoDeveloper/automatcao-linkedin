"""The LinkedIn access token, kept in one 0600 file outside the repository."""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Token:
    access_token: str
    person_urn: str
    name: str
    expires_at: datetime

    def days_left(self, now: datetime) -> float:
        return (self.expires_at - now).total_seconds() / 86400


def save(path: Path, token: Token) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    data = {
        "access_token": token.access_token,
        "person_urn": token.person_urn,
        "name": token.name,
        "expires_at": token.expires_at.isoformat(),
    }
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.unlink(missing_ok=True)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(data, file)
    temporary.replace(path)


def load(path: Path) -> Token | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Token(
            access_token=data["access_token"],
            person_urn=data["person_urn"],
            name=data.get("name", ""),
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        return None
