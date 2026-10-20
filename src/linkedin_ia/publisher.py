"""One publish run: ticks, approvals, posting, the review file and notifications."""

import fcntl
from collections.abc import Callable
from datetime import datetime

from linkedin_ia import credentials, drafts, linkedin_api, publishing, review
from linkedin_ia.config import Config
from linkedin_ia.notify import Notifier

TOKEN_WARNING_DAYS = 7


def _title(stem: str) -> str:
    return stem.split(" - ", 1)[-1]


class _Once:
    """Notifications already sent are keys in the state; each is sent one time."""

    def __init__(self, state: publishing.State, notifier: Notifier, write: bool) -> None:
        self.state, self.notifier, self.write = state, notifier, write

    def __call__(self, key: str | None, text: str) -> None:
        if key is not None and key in self.state.notified:
            return
        if key is not None:
            self.state.notified.add(key)
        if self.write:
            self.notifier(text)


def _review_text(config: Config) -> str:
    try:
        return config.review_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _awaiting_review(config: Config, state: publishing.State) -> list[str]:
    return [
        d.path.stem
        for d in publishing.queue(config)
        if d.group in ("rascunho", "aprovado")
        and not publishing.mentions(d)
        and not publishing.is_approved(config, state, d)
    ]


def _prune(state: publishing.State, config: Config, today: str) -> None:
    stems = {d.path.stem for d in drafts.queue(config)}
    state.notified = {
        key
        for key in state.notified
        if key.split(":", 1)[0] in stems or (key.startswith("token:") and key.endswith(today))
    }


def run(
    config: Config,
    now: datetime,
    notifier: Notifier,
    transport: linkedin_api.Transport,
    write: bool = True,
    out: Callable[[str], None] = print,
) -> int:
    config.publish_state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config.publish_state_file.with_suffix(".lock"), "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            out("outra rodada de publicação em andamento")
            return 0
        return _run(config, now, notifier, transport, write, out)


def _run(
    config: Config,
    now: datetime,
    notifier: Notifier,
    transport: linkedin_api.Transport,
    write: bool,
    out: Callable[[str], None],
) -> int:
    today = now.date().isoformat()
    state = publishing.load_state(config.publish_state_file)
    once = _Once(state, notifier, write)

    for kind, stem in publishing.reconcile(
        config, state, review.ticks(_review_text(config)), write
    ):
        out(f"{kind}: {stem}")
        if kind == "alterado":
            once(None, f"{_title(stem)} mudou depois de aprovado e voltou para revisão")

    token = credentials.load(config.token_file)
    if token is None or token.days_left(now) <= 0:
        out("sem token válido: rode `uv run linkedin login`")
        once(f"token:ausente:{today}", "Sem token do LinkedIn: rode `linkedin login` para publicar")
    else:
        if token.days_left(now) <= TOKEN_WARNING_DAYS:
            once(
                f"token:expira:{today}",
                f"O token do LinkedIn vence em {token.expires_at:%d/%m}: rode `linkedin login`",
            )
        client = linkedin_api.Client(token.access_token, config.api_version, transport)
        events = publishing.publish_due(
            config, state, client, token.person_urn, now.date(), now, write
        )
        for kind, stem, detail in events:
            out(f"{kind}: {stem}" + (f" — {detail}" if detail else ""))
            title = _title(stem)
            if kind == "publicado":
                once(None, f"Publicado: {title}")
            elif kind == "comentario_falhou":
                once(None, f"{title} saiu sem o primeiro comentário: comente à mão")
            elif kind == "bloqueado":
                once(f"{stem}:bloqueado:{detail}", f"{title} não saiu: {detail}")
            elif kind == "erro":
                once(f"{stem}:erro:{detail}", f"{title} não saiu, tento de novo: {detail}")
            elif kind in ("sem_resposta", "verificar"):
                once(
                    f"{stem}:verificar:",
                    f"Confira no LinkedIn se {title} saiu. Saiu: status publicado. "
                    "Não saiu: desmarque e marque de novo na revisão",
                )

    fresh = [s for s in _awaiting_review(config, state) if f"{s}:revisar:" not in state.notified]
    if fresh:
        for stem in fresh:
            state.notified.add(f"{stem}:revisar:")
        names = ", ".join(_title(s) for s in fresh)
        once(None, f"{len(fresh)} post(s) para revisar em {config.review_file.stem}: {names}")

    if write:
        _prune(state, config, today)
        config.review_file.parent.mkdir(parents=True, exist_ok=True)
        config.review_file.write_text(review.render(config, state, now), encoding="utf-8")
        publishing.save_state(config.publish_state_file, state)
    return 0
