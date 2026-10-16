from linkedin_ia import cli, drafts


def write(folder, name, status, body="Texto limpo", when="2026-10-20"):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(
        f"---\ntipo: publicacao\nstatus: {status}\npublicar_em: {when}\n"
        f'tags: [linkedin, ia]\nfontes: ["[[Nota A]]", "git: agente"]\n---\n'
        f"# T\n\n## Post\n\n{body}\n\n## Checklist antes de postar\n",
        encoding="utf-8",
    )
    return path


def test_frontmatter_reads_values_and_inline_lists(tmp_path):
    path = write(tmp_path, "2026-10-16 - Primeiro post.md", "rascunho")
    draft = drafts.load(path)
    assert draft.status == "rascunho"
    assert draft.title == "Primeiro post"
    assert draft.meta["tags"] == ["linkedin", "ia"]
    assert draft.meta["fontes"] == ["[[Nota A]]", "git: agente"]


def test_a_note_without_frontmatter_has_no_meta():
    assert drafts.frontmatter("# só título\n") == {}
    assert drafts.frontmatter("---\n---\n# vazio\n") == {}
    assert drafts.frontmatter("---\r\nstatus: rascunho\r\n---\r\n") == {"status": "rascunho"}


def test_fila_groups_by_status_and_marks_failing_drafts(make_config, capsys):
    cfg = make_config()
    write(cfg.drafts_dir, "2026-10-16 - Limpo.md", "rascunho")
    write(cfg.drafts_dir, "2026-10-16 - Vazado.md", "rascunho", body="ABC-12")
    write(cfg.drafts_dir, "2026-10-01 - Antigo.md", "publicado", body="ABC-12")

    assert cli.main(["fila"], config=cfg) == 0

    out = capsys.readouterr().out
    assert out.index("rascunho (2)") < out.index("publicado (1)")
    assert "2026-10-20  Limpo\n" in out
    assert "Vazado  ✗ 1 achado(s)" in out
    assert "Antigo  ✗ 1 achado(s)" in out


def test_fila_exits_2_when_an_approved_draft_fails(make_config, capsys):
    cfg = make_config()
    write(cfg.drafts_dir, "2026-10-16 - Aprovado.md", "aprovado", body="Veja JURA106.prw")
    assert cli.main(["fila"], config=cfg) == 2


def test_fila_normalises_status_and_lists_unknown_ones(make_config, capsys):
    cfg = make_config()
    write(cfg.drafts_dir, "2026-10-16 - Maiusculo.md", "Aprovado", body="ABC-12")
    write(cfg.drafts_dir, "2026-10-16 - Estranho.md", "revisao", body="ABC-12")

    assert cli.main(["fila"], config=cfg) == 2

    out = capsys.readouterr().out
    assert "aprovado (1)\n  2026-10-20  Maiusculo  ✗" in out
    assert "outro (1)\n  2026-10-20  Estranho  [revisao]  ✗" in out


def test_fila_warns_when_rules_are_disabled(make_config, capsys):
    import dataclasses

    cfg = dataclasses.replace(make_config(), forbidden_terms=(), internal_domains=())
    cli.main(["fila"], config=cfg)
    err = capsys.readouterr().err
    assert "termos_proibidos vazio" in err and "dominios_internos vazio" in err


def test_fila_without_drafts_folder(make_config, capsys):
    assert cli.main(["fila"], config=make_config()) == 0
    out = capsys.readouterr().out
    assert f"pasta: {make_config().drafts_dir}\n" in out
    assert "nenhum rascunho" in out
