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
UNSAFE_IN_NAME = set("[]|#^")


def plain(text: str) -> bool:
    """No control, format or line-separator character: nothing that can start a new line."""
    return not any(unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") for c in text)


def queue(config: Config) -> list[drafts.Draft]:
    """Drafts whose file name is safe to write as a wikilink line in the review file."""
    return [
        d
        for d in drafts.queue(config)
        if plain(d.path.stem) and not UNSAFE_IN_NAME & set(d.path.stem)
    ]


@dataclass
class State:
    approvals: dict[str, str] = field(default_factory=dict)
    publishing: dict[str, str] = field(default_factory=dict)
    notified: set[str] = field(default_factory=set)


def load_state(path: Path) -> State:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return State()
    return State(
        dict(data.get("aprovacoes", {})),
        dict(data.get("publicando", {})),
        set(data.get("avisados", [])),
    )


def save_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "aprovacoes": state.approvals,
        "publicando": state.publishing,
        "avisados": sorted(state.notified),
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
    exact = config.images_dir / name
    if exact.is_file():
        return exact
    for suffix in IMAGE_SUFFIXES:
        other = config.images_dir / (Path(name).stem + suffix)
        if other.is_file():
            return other
    return None


def blockers(config: Config, draft: drafts.Draft) -> list[str]:
    """What keeps an approved draft from going out (R2.5), in the words of the review file."""
    found = []
    body = drafts.post_body(draft.path.read_text(encoding="utf-8"))
    if not body.strip():
        found.append("post vazio")
    elif len(body) > check.MAX_LENGTH:
        found.append(f"post com {len(body)} caracteres, máximo {check.MAX_LENGTH}")
    findings = check.check(draft.path, config)
    if findings:
        found.append(f"{len(findings)} achado(s) no checar")
    if image_name(draft) and not valid_image_name(image_name(draft)):
        found.append("nome de imagem inválido")
    elif image_name(draft) and find_image(config, draft) is None:
        found.append("falta a imagem")
    return found


def fingerprint(config: Config, draft: drafts.Draft) -> str:
    """What an approval vouches for: the post body, the first comment and the image."""
    digest = hashlib.sha256()
    digest.update(drafts.post_body(draft.path.read_text(encoding="utf-8")).encode())
    digest.update(b"\0" + _text(draft, "primeiro_comentario").strip().encode() + b"\0")
    digest.update(image_name(draft).encode() + b"\0")
    image = find_image(config, draft)
    if image is not None:
        digest.update(image.read_bytes())
    return digest.hexdigest()


def is_approved(config: Config, state: State, draft: drafts.Draft) -> bool:
    recorded = state.approvals.get(draft.path.stem)
    return (
        recorded is not None
        and not mentions(draft)
        and draft.group in ("rascunho", "aprovado")
        and recorded == fingerprint(config, draft)
    )


def reconcile(
    config: Config, state: State, ticks: dict[str, bool], write: bool = True
) -> list[tuple[str, str]]:
    """Apply the review file's ticks and void approvals whose draft changed."""
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
        if stem in state.approvals:
            if state.approvals[stem] != fingerprint(config, draft):
                kind = "alterado"
            elif ticks.get(stem) is False:
                kind = "desaprovado"
            else:
                continue
            del state.approvals[stem]
            events.append((kind, stem))
            if write:
                drafts.update(draft.path, {"status": "rascunho"})
        elif ticks.get(stem):
            state.approvals[stem] = fingerprint(config, draft)
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
        if not is_approved(config, state, draft) or not is_due(draft, today):
            continue
        blocked = blockers(config, draft)
        if blocked:
            events.append(("bloqueado", stem, "; ".join(blocked)))
            continue
        if not write:
            events.append(("publicaria", stem, ""))
            continue
        events.extend(_publish(config, state, draft, client, author, now))
    return events


def _publish(
    config: Config, state: State, draft: drafts.Draft, client: Publisher, author: str, now: datetime
) -> list[tuple[str, str, str]]:
    stem = draft.path.stem
    body = drafts.post_body(draft.path.read_text(encoding="utf-8"))
    try:
        image_path = find_image(config, draft)
        image = client.upload_image(author, image_path.read_bytes()) if image_path else None
    except (ApiError, NoAnswer) as error:
        return [("erro", stem, str(error))]

    state.publishing[stem] = now.isoformat()
    save_state(config.publish_state_file, state)
    try:
        urn = client.create_post(author, little.commentary(body), image)
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
    save_state(config.publish_state_file, state)
    events = [("publicado", stem, link)]

    comment = _text(draft, "primeiro_comentario").strip()
    if comment:
        try:
            client.comment(urn, author, comment)
        except (ApiError, NoAnswer) as error:
            events.append(("comentario_falhou", stem, str(error)))
    return events
