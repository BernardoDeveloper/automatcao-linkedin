"""The review file: where Bernardo ticks the drafts that may be published."""

import re
from datetime import datetime
from pathlib import Path

from linkedin_ia import drafts, publishing
from linkedin_ia.config import Config

TICK = re.compile(
    r"^\s*- \[([ xX])\] \[\[([^\]|]+)(?:\|[^\]]*)?\]\](?: · v:([0-9a-f]{32})(?= |$))?"
)
PREVIEW = 70


def ticks(text: str) -> dict[str, tuple[bool, str]]:
    """Each checkbox line's draft stem: whether it is ticked, and the version it shows."""
    found = {}
    for line in text.split("\n"):
        match = TICK.match(line)
        if match:
            found[match.group(2).strip()] = (match.group(1) != " ", match.group(3) or "")
    return found


def _clean(text: str) -> str:
    """One line of plain text: anything that could start a new line becomes a space."""
    return "".join(c if publishing.plain(c) else " " for c in text)


def _when(draft: drafts.Draft) -> str:
    return _clean(str(draft.meta.get("publicar_em") or "").strip())


def _shown(config: Config, path: Path) -> str:
    try:
        return path.relative_to(config.second_brain).as_posix()
    except ValueError:
        return str(path)


MARKUP = set("\\`*_[]()<>!%#|~=$&{}")


def _quote(text: str) -> str:
    """A preview Obsidian shows as plain text: no link, embed, comment or tag in it."""
    line = " ".join(_clean(text).split())
    cut = line[:PREVIEW] + ("…" if len(line) > PREVIEW else "")
    return "“" + "".join(f"\\{c}" if c in MARKUP else c for c in cut) + "”"


def _image(config: Config, draft: drafts.Draft) -> str:
    name = _clean(publishing.image_name(draft))
    if not name:
        return "só texto"
    if not publishing.valid_image_name(publishing.image_name(draft)):
        return f"**nome de imagem inválido** `{name}`"
    found = publishing.find_image(config, draft)
    if found is not None:
        return f"imagem: `{found.name}`"
    return f"**falta a imagem** `{_shown(config, config.images_dir)}/{name}`"


def render(config: Config, state: publishing.State, now: datetime) -> str:
    """The whole review file, rewritten on every publish run."""
    waiting, approved, manual, published = [], [], [], []
    for draft in publishing.queue(config):
        stem = draft.path.stem
        if draft.group == "publicado":
            published.append(draft)
        elif draft.group not in ("rascunho", "aprovado"):
            continue
        elif publishing.mentions(draft):
            names = _clean(", ".join(publishing.mentions(draft)))
            manual.append(f"- [[{stem}]] · marcar: {names}")
        else:
            snap = publishing.snapshot(config, draft)
            blocked = publishing.blockers_of(config, snap)
            image_notes = ("falta a imagem", "nome de imagem inválido")
            notes = [
                _quote(snap.body),
                *([f"comentário: {_quote(snap.comment)}"] if snap.comment else []),
                _image(config, draft),
                *(f"**{b}**" for b in blocked if b not in image_notes),
            ]
            head = f"[[{stem}]] · v:{publishing.version(snap.fingerprint)}"
            when = _when(draft)
            if state.approvals.get(stem) == snap.fingerprint:
                notes.insert(0, f"sai em {when}" if when else "sai na próxima rodada")
                approved.append((when or "0000", f"- [x] {head} · {' · '.join(notes)}"))
            else:
                notes.insert(0, f"publicar em {when or 'sem data'}")
                waiting.append((when or "9999", f"- [ ] {head} · {' · '.join(notes)}"))

    published.sort(key=lambda d: _when(d), reverse=True)
    folder = _shown(config, config.images_dir)
    lines = [
        "---",
        "tipo: revisao",
        "area: Carreira",
        f"atualizado: {now:%Y-%m-%d %H:%M}",
        "tags: [linkedin, revisao]",
        "---",
        "# Revisão de posts do LinkedIn",
        "",
        "Marque `[x]` para aprovar: o post sai sozinho no `publicar_em` (vazio = na próxima "
        "rodada, de hora em hora das 9h às 18h). Desmarque para tirar da fila. A marca vale "
        "para a versão `v:` da linha: se o post mudar antes ou depois de marcar, ele volta "
        "para cá.",
        f"Imagens vão em `{folder}/`, com o nome que aparece na linha. Coloque a imagem antes "
        "de marcar: trocar a imagem de um post aprovado também devolve ele para cá.",
        "",
        "## Para revisar",
        *([line for _, line in sorted(waiting)] or ["_nada_"]),
        "",
        "## Aprovados",
        *([line for _, line in sorted(approved)] or ["_nada_"]),
        "",
        "## Publicar manualmente (marcação de pessoas)",
        *(manual or ["_nada_"]),
        "",
        "## Publicados",
        *(
            [
                f"- [[{d.path.stem}]] · {_when(d) or 'sem data'}"
                + (f" · [link]({_clean(str(d.meta['link']))})" if d.meta.get("link") else "")
                for d in published[:10]
            ]
            or ["_nada_"]
        ),
        "",
        "## Relacionado",
        "- [[LinkedIn]]",
        "",
    ]
    return "\n".join(lines)
