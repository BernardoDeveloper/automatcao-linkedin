"""The publish run: approvals from the review file, then posting what is due."""

import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from linkedin_ia import check, drafts, little
from linkedin_ia.config import Config
from linkedin_ia.linkedin_api import ApiError, NoAnswer, post_url

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif")
# 128 bits on the review-file line: forging a tick by collision costs about 2^64 hashes.
VERSION_LENGTH = 32
COMMENT_MAX_LENGTH = 1250
UNSAFE_IN_NAME = set("[]|#^")


def plain(text: str) -> bool:
    """No control, format or line-separator character: nothing that can start a new line."""
    return not any(unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") for c in text)


def queue(config: Config) -> list[drafts.Draft]:
    """Drafts whose file name is safe to write as a wikilink line in the review file."""
    return [
        d
        for d in drafts.queue(config)
        if plain(d.path.stem) and not UNSAFE_IN_NAME & set(d.path.stem) and not d.path.is_symlink()
    ]


@dataclass
class State:
    approvals: dict[str, str] = field(default_factory=dict)
    publishing: dict[str, str] = field(default_factory=dict)
    notified: set[str] = field(default_factory=set)
    published: set[str] = field(default_factory=set)


def load_state(path: Path) -> State:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return State()
    return State(
        dict(data.get("aprovacoes", {})),
        dict(data.get("publicando", {})),
        set(data.get("avisados", [])),
        set(data.get("publicados", [])),
    )


def save_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "aprovacoes": state.approvals,
        "publicando": state.publishing,
        "avisados": sorted(state.notified),
        "publicados": sorted(state.published),
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _text(draft: drafts.Draft, key: str) -> str:
    value = draft.meta.get(key, "")
    return value if isinstance(value, str) else ", ".join(value)


def mentions(draft: drafts.Draft) -> list[str]:
    value = draft.meta.get("mencoes", [])
    names = value if isinstance(value, list) else [value]
    return [n for n in names if n.strip()]


def image_name(draft: drafts.Draft) -> str:
    return _text(draft, "imagem").strip()


def valid_image_name(name: str) -> bool:
    """A bare file name with an image extension: nothing outside the images folder."""
    return (
        Path(name).name == name
        and not name.startswith(".")
        and "\\" not in name
        and plain(name)
        and Path(name).suffix.lower() in IMAGE_SUFFIXES
    )


def find_image(config: Config, draft: drafts.Draft) -> Path | None:
    """The draft's image in the images folder; another extension of the same stem counts."""
    name = image_name(draft)
    if not name or not valid_image_name(name):
        return None
    for candidate in (name, *(Path(name).stem + suffix for suffix in IMAGE_SUFFIXES)):
        path = config.images_dir / candidate
        if path.is_file() and not path.is_symlink():
            return path
    return None


@dataclass(frozen=True)
class Snapshot:
    """One read of a draft: what is checked, fingerprinted and sent all comes from it."""

    draft: drafts.Draft
    body: str
    comment: str
    image_name: str
    image: bytes | None
    fingerprint: str


def snapshot(config: Config, draft: drafts.Draft) -> Snapshot:
    text = draft.path.read_text(encoding="utf-8")
    current = drafts.Draft(draft.path, drafts.frontmatter(text))
    body = drafts.post_body(text)
    comment = _text(current, "primeiro_comentario").strip()
    when = _text(current, "publicar_em").strip()
    name = image_name(current)
    found = find_image(config, current)
    image = found.read_bytes() if found is not None else None
    digest = hashlib.sha256(json.dumps([body, comment, when, name]).encode())
    digest.update(image or b"")
    return Snapshot(current, body, comment, name, image, digest.hexdigest())


def fingerprint(config: Config, draft: drafts.Draft) -> str:
    """What an approval vouches for: post body, first comment, date and image."""
    return snapshot(config, draft).fingerprint


def version(fingerprint: str) -> str:
    """The short form of a fingerprint written on each review-file line."""
    return fingerprint[:VERSION_LENGTH]


def blockers_of(config: Config, snap: Snapshot) -> list[str]:
    """What keeps a draft from going out (R2.5), in the words of the review file."""
    found = []
    if not snap.body.strip():
        found.append("post vazio")
    elif len(snap.body) > check.MAX_LENGTH:
        found.append(f"post com {len(snap.body)} caracteres, máximo {check.MAX_LENGTH}")
    path = snap.draft.path
    # The pattern checks only run on text of a postable length, so they stay fast.
    if len(snap.body) <= check.MAX_LENGTH:
        findings = len(check.text_findings(snap.body, path, config))
        if findings:
            found.append(f"{findings} achado(s) no checar")
    if len(snap.comment) > COMMENT_MAX_LENGTH:
        found.append(f"primeiro comentário com mais de {COMMENT_MAX_LENGTH} caracteres")
    elif snap.comment and check.text_findings(snap.comment, path, config):
        found.append("primeiro comentário com achado no checar")
    if any(not plain(c) for c in (snap.body + snap.comment).replace("\n", "")):
        found.append("caractere de controle no texto")
    if snap.image_name and not valid_image_name(snap.image_name):
        found.append("nome de imagem inválido")
    elif snap.image_name and snap.image is None:
        found.append("falta a imagem")
    return found


def blockers(config: Config, draft: drafts.Draft) -> list[str]:
    return blockers_of(config, snapshot(config, draft))


def approved(config: Config, state: State, draft: drafts.Draft) -> Snapshot | None:
    """The draft as approved, read once, or None when no approval covers what it holds now."""
    snap = snapshot(config, draft)
    current = snap.draft
    if (
        mentions(current)
        or current.group not in ("rascunho", "aprovado")
        or state.approvals.get(draft.path.stem) != snap.fingerprint
    ):
        return None
    return snap


def is_approved(config: Config, state: State, draft: drafts.Draft) -> bool:
    return approved(config, state, draft) is not None


def reconcile(
    config: Config, state: State, ticks: dict[str, tuple[bool, str]], write: bool = True
) -> list[tuple[str, str]]:
    """Apply the review file's ticks and void approvals whose draft changed.

    A tick only approves the version written on its line, which is what Bernardo read: a
    draft changed after the review file was written is not approved by an old tick.
    """
    events = []
    candidates = {d.path.stem: d for d in queue(config)}
    for stem in list(state.approvals):
        if stem not in candidates or candidates[stem].group not in ("rascunho", "aprovado"):
            del state.approvals[stem]
    for stem, draft in candidates.items():
        if draft.group not in ("rascunho", "aprovado"):
            continue
        if mentions(draft):
            state.approvals.pop(stem, None)
            continue
        current = fingerprint(config, draft)
        ticked, seen = ticks.get(stem, (None, ""))
        if stem in state.approvals:
            if state.approvals[stem] != current:
                kind = "alterado"
            elif ticked is False:
                kind = "desaprovado"
            else:
                continue
            del state.approvals[stem]
            events.append((kind, stem))
            if write:
                drafts.update(draft.path, {"status": "rascunho"})
        elif ticked and seen != version(current):
            events.append(("alterado", stem))
            if write and draft.group == "aprovado":
                drafts.update(draft.path, {"status": "rascunho"})
        elif ticked and current in state.published:
            events.append(("ja_publicado", stem))
        elif ticked:
            state.approvals[stem] = current
            events.append(("aprovado", stem))
            if write:
                drafts.update(draft.path, {"status": "aprovado"})
    return events


class Publisher(Protocol):
    def upload_image(self, owner: str, image: bytes) -> str: ...
    def create_post(self, author: str, commentary: str, image: str | None = None) -> str: ...
    def comment(self, post: str, actor: str, text: str) -> None: ...


def is_due(draft: drafts.Draft, today: date) -> bool:
    when = str(draft.meta.get("publicar_em") or "").strip()
    try:
        return not when or date.fromisoformat(when) <= today
    except ValueError:
        return False


def publish_due(
    config: Config,
    state: State,
    client: Publisher,
    author: str,
    today: date,
    now: datetime,
    write: bool = True,
) -> list[tuple[str, str, str]]:
    """Publish every approved draft whose date has come (R2), once."""
    events = []
    for draft in queue(config):
        stem = draft.path.stem
        if stem in state.publishing:
            if draft.group == "publicado" or stem not in state.approvals:
                del state.publishing[stem]
            else:
                events.append(("verificar", stem, ""))
            continue
        snap = approved(config, state, draft)
        if snap is None or not is_due(snap.draft, today):
            continue
        blocked = blockers_of(config, snap)
        if blocked:
            events.append(("bloqueado", stem, "; ".join(blocked)))
            continue
        if not write:
            events.append(("publicaria", stem, ""))
            continue
        events.extend(_publish(config, state, snap, client, author, now))
    return events


def _publish(
    config: Config, state: State, snap: Snapshot, client: Publisher, author: str, now: datetime
) -> list[tuple[str, str, str]]:
    draft, stem = snap.draft, snap.draft.path.stem
    try:
        image = client.upload_image(author, snap.image) if snap.image is not None else None
    except (ApiError, NoAnswer, KeyError, ValueError) as error:
        return [("erro", stem, str(error))]

    state.publishing[stem] = now.isoformat()
    save_state(config.publish_state_file, state)
    try:
        urn = client.create_post(author, little.commentary(snap.body), image)
    except ApiError as error:
        del state.publishing[stem]
        save_state(config.publish_state_file, state)
        return [("erro", stem, str(error))]
    except NoAnswer as error:
        return [("sem_resposta", stem, str(error))]

    link = post_url(urn)
    drafts.update(draft.path, {"status": "publicado", "link": link})
    del state.publishing[stem]
    state.approvals.pop(stem, None)
    state.published.add(snap.fingerprint)
    save_state(config.publish_state_file, state)
    events = [("publicado", stem, link)]

    if snap.comment:
        try:
            client.comment(urn, author, snap.comment)
        except (ApiError, NoAnswer) as error:
            events.append(("comentario_falhou", stem, str(error)))
    return events
