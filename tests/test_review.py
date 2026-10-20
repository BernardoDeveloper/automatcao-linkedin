from datetime import datetime

from linkedin_ia import publishing, review

NOW = datetime(2026, 10, 20, 9, 0)


def write(cfg, stem, status="rascunho", body="Texto do post", when="2026-10-22", extra=""):
    cfg.drafts_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.drafts_dir / f"{stem}.md"
    path.write_text(
        f"---\ntipo: publicacao\npublicar_em: {when}\nstatus: {status}\n{extra}---\n"
        f"# T\n\n## Post\n\n{body}\n",
        encoding="utf-8",
    )
    return path


def section(text, title):
    start = text.index(f"## {title}\n") + len(title) + 4
    end = text.find("\n## ", start)
    return text[start:end].strip()


def test_drafts_awaiting_review_are_unticked_with_date_and_image(make_config):
    cfg = make_config()
    write(cfg, "2026-10-16 - Só texto")
    write(cfg, "2026-10-16 - Com imagem", when="", extra="imagem: foto.png\n")

    text = review.render(cfg, publishing.State(), NOW)

    waiting = section(text, "Para revisar")
    assert "- [ ] [[2026-10-16 - Só texto]] · publicar em 2026-10-22 · só texto" in waiting
    assert (
        "- [ ] [[2026-10-16 - Com imagem]] · publicar em sem data · **falta a imagem** "
        "`02-Areas/Carreira/LinkedIn/Posts/imagens/foto.png`" in waiting
    )
    assert section(text, "Aprovados") == "_nada_"


def test_approved_drafts_are_ticked_with_when_they_go_out(make_config):
    cfg = make_config()
    write(cfg, "2026-10-16 - Um")
    state = publishing.State()
    publishing.reconcile(cfg, state, {"2026-10-16 - Um": True})

    text = review.render(cfg, state, NOW)

    assert section(text, "Aprovados") == "- [x] [[2026-10-16 - Um]] · sai em 2026-10-22 · só texto"
    assert section(text, "Para revisar") == "_nada_"


def test_ticks_read_back_from_the_rendered_file_keep_the_approvals(make_config):
    cfg = make_config()
    write(cfg, "2026-10-16 - Um")
    write(cfg, "2026-10-16 - Dois")
    state = publishing.State()
    publishing.reconcile(cfg, state, {"2026-10-16 - Um": True})

    rendered = review.ticks(review.render(cfg, state, NOW))

    assert rendered == {"2026-10-16 - Um": True, "2026-10-16 - Dois": False}
    assert publishing.reconcile(cfg, state, rendered) == []


def test_a_forged_aprovado_status_is_listed_for_review(make_config):
    cfg = make_config()
    write(cfg, "2026-10-16 - Forjado", status="aprovado")
    text = review.render(cfg, publishing.State(), NOW)
    assert "- [ ] [[2026-10-16 - Forjado]]" in section(text, "Para revisar")


def test_drafts_with_mentions_are_manual_without_a_checkbox(make_config):
    cfg = make_config()
    write(cfg, "2026-10-19 - Orfanato", extra="mencoes: [Fernanda Almeida]\n")
    text = review.render(cfg, publishing.State(), NOW)
    assert section(text, "Publicar manualmente (marcação de pessoas)") == (
        "- [[2026-10-19 - Orfanato]] · marcar: Fernanda Almeida"
    )
    assert "Orfanato" not in section(text, "Para revisar")


def test_blockers_show_on_the_line(make_config):
    cfg = make_config()
    write(cfg, "2026-10-16 - Vazado", body="Veja ABC-1234")
    write(cfg, "2026-10-16 - Vazio", body="")
    text = section(review.render(cfg, publishing.State(), NOW), "Para revisar")
    assert (
        "[[2026-10-16 - Vazado]] · publicar em 2026-10-22 · só texto · **1 achado(s) no checar**"
        in text
    )
    assert "**post vazio**" in text


def test_published_drafts_are_listed_with_their_link_and_others_are_left_out(make_config):
    cfg = make_config()
    write(cfg, "2026-10-16 - Feito", status="publicado", extra="link: https://l/1/\n")
    write(cfg, "2026-10-16 - Ideia", status="ideia")
    text = review.render(cfg, publishing.State(), NOW)
    assert (
        section(text, "Publicados")
        == "- [[2026-10-16 - Feito]] · 2026-10-22 · [link](https://l/1/)"
    )
    assert "Ideia" not in text
