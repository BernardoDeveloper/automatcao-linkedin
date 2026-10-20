"""The publish run: approvals from the review file, then posting what is due."""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from linkedin_ia import check, drafts
from linkedin_ia.config import Config

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif")


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


def find_image(config: Config, draft: drafts.Draft) -> Path | None:
    """The draft's image in the images folder; another extension of the same stem counts."""
    name = image_name(draft)
    if not name:
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
    if image_name(draft) and find_image(config, draft) is None:
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
    queue = {d.path.stem: d for d in drafts.queue(config)}
    for stem in list(state.approvals):
        if stem not in queue or queue[stem].group not in ("rascunho", "aprovado"):
            del state.approvals[stem]
    for stem, draft in queue.items():
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
