from linkedin_ia import drafts, publishing, review


def yes(cfg, stem):
    """A tick on the line Bernardo saw: the draft's current version."""
    draft = drafts.load(cfg.drafts_dir / f"{stem}.md")
    return {stem: (True, publishing.version(publishing.fingerprint(cfg, draft)))}


def write(cfg, stem, status="rascunho", body="Texto do post", extra=""):
    cfg.drafts_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.drafts_dir / f"{stem}.md"
    path.write_text(
        f"---\ntipo: publicacao\npublicar_em: 2026-10-20\nstatus: {status}\nlink:\n{extra}---\n"
        f"# T\n\n## Post\n\n{body}\n\n## Checklist antes de postar\n- [ ] x\n",
        encoding="utf-8",
    )
    return path


def status(path):
    return drafts.load(path).status


def test_ticks_are_read_by_draft_stem():
    text = (
        "## Para revisar\n"
        "- [x] [[2026-10-16 - Um]] · v:0123456789abcdef0123456789abcdef · 2026-10-20\n"
        "- [ ] [[2026-10-16 - Dois]] · v:fedcba9876543210fedcba9876543210 · sem data\n"
        "- [X] [[2026-10-16 - Três|apelido]]\n"
        "- [x] [[2026-10-16 - Falso]] · publicar em x · v:0123456789abcdef0123456789abcdef\n"
        "- [[2026-10-19 - Manual]] · marcar: Fulana\n"
        "texto solto [x] [[Nada]]\n"
    )
    assert review.ticks(text) == {
        "2026-10-16 - Um": (True, "0123456789abcdef0123456789abcdef"),
        "2026-10-16 - Dois": (False, "fedcba9876543210fedcba9876543210"),
        "2026-10-16 - Três": (True, ""),
        "2026-10-16 - Falso": (True, ""),
    }


def test_a_tick_records_an_approval_and_marks_the_draft_approved(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    state = publishing.State()

    events = publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))

    assert events == [("aprovado", "2026-10-16 - Um")]
    assert state.approvals["2026-10-16 - Um"] == publishing.fingerprint(cfg, drafts.load(path))
    assert status(path) == "aprovado"


def test_without_a_tick_nothing_is_approved(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    assert publishing.reconcile(cfg, state, {"2026-10-16 - Um": (False, "")}) == []
    assert publishing.reconcile(cfg, state, {}) == []
    assert state.approvals == {}
    assert status(path) == "rascunho"


def test_status_aprovado_written_into_a_draft_approves_nothing(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Forjado", status="aprovado")
    state = publishing.State()
    assert publishing.reconcile(cfg, state, {}) == []
    assert state.approvals == {}
    assert not publishing.is_approved(cfg, state, drafts.load(path))


def test_unticking_drops_the_approval(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))

    events = publishing.reconcile(cfg, state, {"2026-10-16 - Um": (False, "")})

    assert events == [("desaprovado", "2026-10-16 - Um")]
    assert state.approvals == {}
    assert status(path) == "rascunho"


def test_an_edit_after_approval_sends_the_draft_back_to_review(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))
    path.write_text(
        path.read_text(encoding="utf-8").replace("Texto do post", "Texto trocado"),
        encoding="utf-8",
    )

    events = publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))

    assert events == [("alterado", "2026-10-16 - Um")]
    assert state.approvals == {}
    assert status(path) == "rascunho"
    assert not publishing.is_approved(cfg, state, drafts.load(path))


def test_frontmatter_outside_the_fingerprint_does_not_void_the_approval(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))
    drafts.update(path, {"pilar": "bastidor", "tags": "[a, b]"})
    assert publishing.reconcile(cfg, state, {}) == []
    assert publishing.is_approved(cfg, state, drafts.load(path))


def test_a_changed_date_voids_the_approval(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))
    drafts.update(path, {"publicar_em": ""})
    assert publishing.reconcile(cfg, state, {}) == [("alterado", "2026-10-16 - Um")]


def test_a_tick_on_an_older_version_approves_nothing(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    seen = yes(cfg, "2026-10-16 - Um")
    path.write_text(path.read_text(encoding="utf-8").replace("Texto", "Trocado"), encoding="utf-8")
    state = publishing.State()

    events = publishing.reconcile(cfg, state, seen)

    assert events == [("alterado", "2026-10-16 - Um")]
    assert state.approvals == {}
    assert status(path) == "rascunho"


def test_a_tick_without_a_version_approves_nothing(make_config):
    cfg = make_config()
    write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, {"2026-10-16 - Um": (True, "")})
    assert state.approvals == {}


def test_a_changed_first_comment_or_image_voids_the_approval(make_config):
    cfg = make_config()
    path = write(
        cfg, "2026-10-16 - Um", extra="primeiro_comentario: Link: https://a\nimagem: um.png\n"
    )
    cfg.images_dir.mkdir(parents=True)
    (cfg.images_dir / "um.png").write_bytes(b"A")
    state = publishing.State()
    publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))

    (cfg.images_dir / "um.png").write_bytes(b"B")
    assert publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um")) == [
        ("alterado", "2026-10-16 - Um")
    ]

    publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um"))
    drafts.update(path, {"primeiro_comentario": "Link: https://b"})
    assert publishing.reconcile(cfg, state, yes(cfg, "2026-10-16 - Um")) == [
        ("alterado", "2026-10-16 - Um")
    ]


def test_a_draft_with_mentions_is_never_approved(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-19 - Manual", extra="mencoes: [Fernanda Almeida]\n")
    state = publishing.State()
    assert publishing.reconcile(cfg, state, yes(cfg, "2026-10-19 - Manual")) == []
    assert state.approvals == {}
    assert status(path) == "rascunho"


def test_dry_run_changes_no_file(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    before = path.read_text(encoding="utf-8")
    events = publishing.reconcile(cfg, publishing.State(), yes(cfg, "2026-10-16 - Um"), write=False)
    assert events == [("aprovado", "2026-10-16 - Um")]
    assert path.read_text(encoding="utf-8") == before


def test_state_round_trips(tmp_path):
    state = publishing.State({"a": "f"}, {"b": "2026-10-20T09:00"}, {"a:x:"})
    publishing.save_state(tmp_path / "e" / "s.json", state)
    assert publishing.load_state(tmp_path / "e" / "s.json") == state
    assert publishing.load_state(tmp_path / "nada.json") == publishing.State()


def test_text_cannot_move_between_body_and_comment_unnoticed(make_config):
    cfg = make_config()
    a = write(cfg, "2026-10-16 - A", body="a\0b")
    b = write(cfg, "2026-10-16 - B", body="a", extra="primeiro_comentario: b\0\n")
    assert publishing.fingerprint(cfg, drafts.load(a)) != publishing.fingerprint(
        cfg, drafts.load(b)
    )


def test_a_version_already_published_is_never_approved_again(make_config):
    cfg = make_config()
    path = write(cfg, "2026-10-16 - Um")
    seen = yes(cfg, "2026-10-16 - Um")
    state = publishing.State(published={publishing.fingerprint(cfg, drafts.load(path))})
    assert publishing.reconcile(cfg, state, seen) == [("ja_publicado", "2026-10-16 - Um")]
    assert state.approvals == {}


def test_the_version_on_the_line_is_128_bits():
    assert len(publishing.version("f" * 64)) == 32


def test_symlinked_and_unreadable_drafts_are_left_out(make_config, tmp_path):
    cfg = make_config()
    write(cfg, "2026-10-16 - Um")
    target = tmp_path / "fora.md"
    target.write_text("---\nstatus: rascunho\n---\n## Post\n\nx\n", encoding="utf-8")
    (cfg.drafts_dir / "2026-10-16 - Link.md").symlink_to(target)
    (cfg.drafts_dir / "2026-10-16 - Binário.md").write_bytes(b"\xff\xfe---")
    assert [d.path.stem for d in publishing.queue(cfg)] == ["2026-10-16 - Um"]
