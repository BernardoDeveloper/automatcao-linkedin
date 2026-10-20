import fcntl
from dataclasses import replace
from datetime import datetime, timedelta

from linkedin_ia import credentials, drafts, publisher, publishing
from linkedin_ia.linkedin_api import Response

NOW = datetime(2026, 10, 20, 9, 0).astimezone()


class Transport:
    def __init__(self):
        self.urls = []

    def __call__(self, request):
        self.urls.append(request.full_url)
        return Response(201, {"x-restli-id": "urn:li:share:9"}, b"{}")


def setup(make_config, tmp_path, token_days=60):
    cfg = replace(make_config(), token_file=tmp_path / "tok" / "token.json")
    if token_days is not None:
        credentials.save(
            cfg.token_file,
            credentials.Token("tok", "urn:li:person:p", "B", NOW + timedelta(days=token_days)),
        )
    return cfg


def write(cfg, stem, body="Texto do post", when="2026-10-20"):
    cfg.drafts_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.drafts_dir / f"{stem}.md"
    path.write_text(
        f"---\ntipo: publicacao\npublicar_em: {when}\nstatus: rascunho\nlink:\n---\n"
        f"# T\n\n## Post\n\n{body}\n",
        encoding="utf-8",
    )
    return path


def tick(cfg, stem):
    text = cfg.review_file.read_text(encoding="utf-8")
    cfg.review_file.write_text(
        text.replace(f"- [ ] [[{stem}]]", f"- [x] [[{stem}]]"), encoding="utf-8"
    )


def go(cfg, sent, transport=None, now=NOW, write=True):
    return publisher.run(cfg, now, sent.append, transport or Transport(), write, out=lambda s: None)


def test_a_new_draft_notifies_once_and_lands_in_the_review_file(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    write(cfg, "2026-10-16 - Um")
    sent = []
    go(cfg, sent)
    go(cfg, sent)
    assert sent == ["1 post(s) para revisar em Revisão de posts: Um"]
    assert "- [ ] [[2026-10-16 - Um]]" in cfg.review_file.read_text(encoding="utf-8")


def test_ticking_in_the_review_file_publishes_on_the_next_run(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    path = write(cfg, "2026-10-16 - Um")
    sent, transport = [], Transport()
    go(cfg, sent, transport)
    tick(cfg, "2026-10-16 - Um")

    go(cfg, sent, transport)

    assert transport.urls == ["https://api.linkedin.com/rest/posts"]
    assert drafts.load(path).status == "publicado"
    assert sent[-1] == "Publicado: Um"
    assert "[[2026-10-16 - Um]] · 2026-10-20 · [link](" in cfg.review_file.read_text(
        encoding="utf-8"
    )


def test_without_a_token_nothing_is_published_and_it_warns_once_a_day(make_config, tmp_path):
    cfg = setup(make_config, tmp_path, token_days=None)
    path = write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, {"2026-10-16 - Um": True})
    publishing.save_state(cfg.publish_state_file, state)
    sent, transport = [], Transport()

    go(cfg, sent, transport)
    go(cfg, sent, transport)
    go(cfg, sent, transport, now=NOW + timedelta(days=1))

    assert transport.urls == []
    assert drafts.load(path).status == "aprovado"
    warnings = [s for s in sent if "linkedin login" in s]
    assert len(warnings) == 2
    assert cfg.review_file.exists()


def test_an_expired_token_counts_as_none(make_config, tmp_path):
    cfg = setup(make_config, tmp_path, token_days=-1)
    sent = []
    go(cfg, sent)
    assert sent == ["Sem token do LinkedIn: rode `linkedin login` para publicar"]


def test_a_token_about_to_expire_warns_once_a_day_and_still_publishes(make_config, tmp_path):
    cfg = setup(make_config, tmp_path, token_days=5)
    sent = []
    go(cfg, sent)
    go(cfg, sent)
    assert sent == [
        f"O token do LinkedIn vence em {(NOW + timedelta(days=5)):%d/%m}: rode `linkedin login`"
    ]


def test_a_blocked_draft_is_notified_once(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    write(cfg, "2026-10-16 - Vazado", body="Veja ABC-1234")
    sent = []
    go(cfg, sent)
    tick(cfg, "2026-10-16 - Vazado")
    go(cfg, sent)
    go(cfg, sent)
    assert sent.count("Vazado não saiu: 1 achado(s) no checar") == 1


def test_an_edit_after_approval_notifies(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    path = write(cfg, "2026-10-16 - Um", when="2026-10-30")
    sent = []
    go(cfg, sent)
    tick(cfg, "2026-10-16 - Um")
    go(cfg, sent)
    path.write_text(path.read_text(encoding="utf-8").replace("Texto", "Novo"), encoding="utf-8")
    go(cfg, sent)
    assert "Um mudou depois de aprovado e voltou para revisão" in sent


def test_a_run_in_progress_makes_the_next_one_do_nothing(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    write(cfg, "2026-10-16 - Um")
    cfg.publish_state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg.publish_state_file.with_suffix(".lock"), "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        sent = []
        assert go(cfg, sent) == 0
    assert sent == []
    assert not cfg.review_file.exists()


def test_dry_run_notifies_nothing_and_writes_nothing(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    write(cfg, "2026-10-16 - Um")
    sent, transport = [], Transport()
    go(cfg, sent, transport, write=False)
    assert sent == [] and transport.urls == []
    assert not cfg.review_file.exists()
    assert not cfg.publish_state_file.exists()


def test_cli_simular_prints_what_would_happen_and_changes_nothing(
    make_config, tmp_path, capsys, monkeypatch
):
    from linkedin_ia import cli

    cfg = setup(make_config, tmp_path)
    write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, {"2026-10-16 - Um": True})
    publishing.save_state(cfg.publish_state_file, state)
    before = cfg.publish_state_file.read_text(encoding="utf-8")
    monkeypatch.setattr(cli.notify, "desktop", lambda text: (_ for _ in ()).throw(AssertionError))
    transport = Transport()

    assert cli.main(["publicar", "--simular"], config=cfg, transport=transport) == 0

    assert "publicaria: 2026-10-16 - Um" in capsys.readouterr().out
    assert transport.urls == []
    assert cfg.publish_state_file.read_text(encoding="utf-8") == before
    assert not cfg.review_file.exists()


def test_a_title_with_a_colon_is_still_notified_once(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    write(cfg, "2026-10-16 - Dica: Python", body="Veja ABC-1234")
    sent = []
    go(cfg, sent)
    tick(cfg, "2026-10-16 - Dica: Python")
    go(cfg, sent)
    go(cfg, sent)
    go(cfg, sent)
    assert sent.count("Dica: Python não saiu: 1 achado(s) no checar") == 1
    assert len([s for s in sent if "para revisar" in s]) == 1


def test_dry_run_does_not_even_create_the_state_folder(make_config, tmp_path):
    cfg = setup(make_config, tmp_path)
    go(cfg, [], write=False)
    assert not cfg.publish_state_file.parent.exists()
