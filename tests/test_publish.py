from datetime import date, datetime

from linkedin_ia import drafts, publishing
from linkedin_ia.linkedin_api import ApiError, NoAnswer

TODAY = date(2026, 10, 20)
NOW = datetime(2026, 10, 20, 9, 0).astimezone()
AUTHOR = "urn:li:person:p"


class FakeClient:
    def __init__(self, post=None, comment=None, image=None, on_post=None):
        self.post_result = post or "urn:li:share:1"
        self.comment_result = comment
        self.image_result = image
        self.on_post = on_post
        self.posts, self.comments, self.images = [], [], []

    def upload_image(self, owner, data):
        if isinstance(self.image_result, Exception):
            raise self.image_result
        self.images.append((owner, data))
        return "urn:li:image:I"

    def create_post(self, author, commentary, image=None):
        if self.on_post:
            self.on_post()
        if isinstance(self.post_result, Exception):
            raise self.post_result
        self.posts.append((author, commentary, image))
        return self.post_result

    def comment(self, post, actor, text):
        if isinstance(self.comment_result, Exception):
            raise self.comment_result
        self.comments.append((post, actor, text))


def approved(cfg, stem, body="Post #IA", when="2026-10-20", extra=""):
    cfg.drafts_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.drafts_dir / f"{stem}.md"
    path.write_text(
        f"---\ntipo: publicacao\npublicar_em: {when}\nstatus: rascunho\nlink:\n{extra}---\n"
        f"# T\n\n## Post\n\n{body}\n\n## Checklist antes de postar\n",
        encoding="utf-8",
    )
    state = publishing.State()
    publishing.reconcile(cfg, state, {stem: True})
    return path, state


def meta(path):
    return drafts.load(path).meta


def run(cfg, state, client, write=True):
    return publishing.publish_due(cfg, state, client, AUTHOR, TODAY, NOW, write=write)


def test_a_due_approved_draft_is_published_and_recorded(make_config):
    cfg = make_config()
    path, state = approved(cfg, "2026-10-16 - Um")
    client = FakeClient(post="urn:li:share:77")

    events = run(cfg, state, client)

    assert client.posts == [(AUTHOR, "Post {hashtag|\\#|IA}", None)]
    assert events == [
        ("publicado", "2026-10-16 - Um", "https://www.linkedin.com/feed/update/urn:li:share:77/")
    ]
    assert meta(path)["status"] == "publicado"
    assert meta(path)["link"] == "https://www.linkedin.com/feed/update/urn:li:share:77/"
    assert state.approvals == {} and state.publishing == {}


def test_published_once_even_when_run_again(make_config):
    cfg = make_config()
    _, state = approved(cfg, "2026-10-16 - Um")
    client = FakeClient()
    run(cfg, state, client)
    assert run(cfg, state, client) == []
    assert len(client.posts) == 1


def test_an_empty_date_is_due_and_a_future_date_waits(make_config):
    cfg = make_config()
    _, state = approved(cfg, "2026-10-16 - Sem data", when="")
    _, other = approved(cfg, "2026-10-16 - Futuro", when="2026-10-21")
    state.approvals.update(other.approvals)
    client = FakeClient()
    events = run(cfg, state, client)
    assert [e[1] for e in events] == ["2026-10-16 - Sem data"]
    assert "2026-10-16 - Futuro" in state.approvals


def test_a_draft_without_an_approval_is_never_published(make_config):
    cfg = make_config()
    path, _ = approved(cfg, "2026-10-16 - Forjado")
    drafts.update(path, {"status": "aprovado"})
    client = FakeClient()
    assert run(cfg, publishing.State(), client) == []
    assert client.posts == []


def test_a_draft_edited_after_approval_is_not_published(make_config):
    cfg = make_config()
    path, state = approved(cfg, "2026-10-16 - Um")
    path.write_text(path.read_text(encoding="utf-8").replace("Post", "Outro"), encoding="utf-8")
    client = FakeClient()
    assert run(cfg, state, client) == []
    assert client.posts == []


def test_the_image_is_uploaded_and_attached(make_config):
    cfg = make_config()
    _, state = approved(cfg, "2026-10-16 - Um", extra="imagem: foto.png\n")
    cfg.images_dir.mkdir(parents=True)
    (cfg.images_dir / "foto.jpg").write_bytes(b"JPG")
    state.approvals.clear()
    publishing.reconcile(cfg, state, {"2026-10-16 - Um": True})
    client = FakeClient()

    run(cfg, state, client)

    assert client.images == [(AUTHOR, b"JPG")]
    assert client.posts[0][2] == "urn:li:image:I"


def test_the_first_comment_goes_on_the_post(make_config):
    cfg = make_config()
    _, state = approved(cfg, "2026-10-16 - Um", extra="primeiro_comentario: Link: https://livro\n")
    client = FakeClient(post="urn:li:share:5")
    run(cfg, state, client)
    assert client.comments == [("urn:li:share:5", AUTHOR, "Link: https://livro")]


def test_a_rejected_comment_keeps_the_post_published(make_config):
    cfg = make_config()
    path, state = approved(cfg, "2026-10-16 - Um", extra="primeiro_comentario: Link\n")
    client = FakeClient(comment=ApiError(403, "no permission"))
    events = run(cfg, state, client)
    assert meta(path)["status"] == "publicado"
    assert ("comentario_falhou", "2026-10-16 - Um", "HTTP 403: no permission") in events


def test_blocked_drafts_are_not_published(make_config):
    cfg = make_config()
    _, state = approved(cfg, "2026-10-16 - Vazado", body="Veja ABC-1234")
    _, other = approved(cfg, "2026-10-16 - Sem imagem", extra="imagem: falta.png\n")
    state.approvals.update(other.approvals)
    _, other = approved(cfg, "2026-10-16 - Longo", body="x" * 3001)
    state.approvals.update(other.approvals)
    client = FakeClient()

    events = run(cfg, state, client)

    assert client.posts == []
    assert sorted(events) == [
        (
            "bloqueado",
            "2026-10-16 - Longo",
            "post com 3001 caracteres, máximo 3000; 1 achado(s) no checar",
        ),
        ("bloqueado", "2026-10-16 - Sem imagem", "falta a imagem"),
        ("bloqueado", "2026-10-16 - Vazado", "1 achado(s) no checar"),
    ]
    assert len(state.approvals) == 3


def test_an_error_status_keeps_the_draft_approved_for_the_next_run(make_config):
    cfg = make_config()
    path, state = approved(cfg, "2026-10-16 - Um")
    events = run(cfg, state, FakeClient(post=ApiError(500, "boom")))
    assert events == [("erro", "2026-10-16 - Um", "HTTP 500: boom")]
    assert "2026-10-16 - Um" in state.approvals and state.publishing == {}
    assert meta(path)["status"] == "aprovado"
    client = FakeClient()
    run(cfg, state, client)
    assert len(client.posts) == 1


def test_a_failed_image_upload_publishes_nothing_and_retries(make_config):
    cfg = make_config()
    _, state = approved(cfg, "2026-10-16 - Um", extra="imagem: foto.png\n")
    cfg.images_dir.mkdir(parents=True)
    (cfg.images_dir / "foto.png").write_bytes(b"P")
    state.approvals.clear()
    publishing.reconcile(cfg, state, {"2026-10-16 - Um": True})
    client = FakeClient(image=NoAnswer("timeout"))
    assert run(cfg, state, client)[0][0] == "erro"
    assert client.posts == [] and state.publishing == {}


def test_no_answer_is_never_retried(make_config):
    cfg = make_config()
    path, state = approved(cfg, "2026-10-16 - Um")
    events = run(cfg, state, FakeClient(post=NoAnswer("timed out")))
    assert events == [("sem_resposta", "2026-10-16 - Um", "timed out")]
    assert "2026-10-16 - Um" in state.publishing

    client = FakeClient()
    events = run(cfg, state, client)
    assert client.posts == []
    assert events == [("verificar", "2026-10-16 - Um", "")]
    assert meta(path)["status"] == "aprovado"


def test_the_in_flight_marker_is_saved_before_the_post_request(make_config):
    cfg = make_config()
    _, state = approved(cfg, "2026-10-16 - Um")
    seen = []
    client = FakeClient(
        on_post=lambda: seen.append(publishing.load_state(cfg.publish_state_file).publishing)
    )
    run(cfg, state, client)
    assert list(seen[0]) == ["2026-10-16 - Um"]


def test_dry_run_sends_nothing_and_changes_nothing(make_config):
    cfg = make_config()
    path, state = approved(cfg, "2026-10-16 - Um")
    before = path.read_text(encoding="utf-8")
    client = FakeClient()
    assert run(cfg, state, client, write=False) == [("publicaria", "2026-10-16 - Um", "")]
    assert client.posts == []
    assert path.read_text(encoding="utf-8") == before
    assert not cfg.publish_state_file.exists()
