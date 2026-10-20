"""The review file: where Bernardo ticks the drafts that may be published."""

import re
from datetime import datetime

from linkedin_ia import drafts, publishing
from linkedin_ia.config import Config

TICK = re.compile(r"^\s*- \[([ xX])\] \[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def ticks(text: str) -> dict[str, bool]:
    """Each checkbox line's draft stem, and whether it is ticked."""
    found = {}
    for line in text.split("\n"):
        match = TICK.match(line)
        if match:
            found[match.group(2).strip()] = match.group(1) != " "
    return found


def _clean(text: str) -> str:
    """One line of plain text: anything that could start a new line becomes a space."""
    return "".join(c if publishing.plain(c) else " " for c in text)


def _when(draft: drafts.Draft) -> str:
    return _clean(str(draft.meta.get("publicar_em") or "").strip())


def _image(config: Config, draft: drafts.Draft) -> str:
    name = _clean(publishing.image_name(draft))
    if not name:
        return "só texto"
    if not publishing.valid_image_name(publishing.image_name(draft)):
        return f"**nome de imagem inválido** `{name}`"
    found = publishing.find_image(config, draft)
    if found is not None:
        return f"imagem: `{found.name}`"
    folder = config.images_dir.relative_to(config.second_brain).as_posix()
    return f"**falta a imagem** `{folder}/{name}`"


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
            blocked = publishing.blockers(config, draft)
            image_notes = ("falta a imagem", "nome de imagem inválido")
            notes = [_image(config, draft), *(f"**{b}**" for b in blocked if b not in image_notes)]
            if publishing.is_approved(config, state, draft):
                when = _when(draft)
                notes.insert(0, f"sai em {when}" if when else "sai na próxima rodada")
                approved.append((when or "0000", f"- [x] [[{stem}]] · {' · '.join(notes)}"))
            else:
                notes.insert(0, f"publicar em {_when(draft) or 'sem data'}")
                waiting.append((_when(draft) or "9999", f"- [ ] [[{stem}]] · {' · '.join(notes)}"))

    published.sort(key=lambda d: _when(d), reverse=True)
    folder = config.images_dir.relative_to(config.second_brain).as_posix()
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
        "rodada, de hora em hora das 9h às 18h). Desmarque para tirar da fila. Editar um post "
        "aprovado devolve ele para cá.",
        f"Imagens vão em `{folder}/`, com o nome que aparece na linha.",
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
