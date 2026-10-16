from linkedin_ia import check

HEADER = "---\nstatus: rascunho\n---\n# Título com PROJ-1\n\n## Post\n\n"
FOOTER = "\n\n## Checklist antes de postar\n\n- [ ] JURA106.prw fora do post\n"


def draft(tmp_path, body, name="post.md"):
    path = tmp_path / name
    path.write_text(HEADER + body + FOOTER, encoding="utf-8")
    return path


def rules(findings):
    return [(f.line, f.rule, f.text) for f in findings]


def test_a_clean_post_has_no_findings(tmp_path, make_config):
    path = draft(tmp_path, "Usei o Claude Opus 5.5 e o GPT-5 para revisar código.")
    assert check.check(path, make_config()) == []


def test_issue_keys_are_reported_with_their_line(tmp_path, make_config):
    path = draft(tmp_path, "Primeira linha\nResolvi a PROJ-1234 ontem")
    assert rules(check.check(path, make_config())) == [(9, "issue", "PROJ-1234")]


def test_allowed_terms_are_not_issue_keys(tmp_path, make_config):
    path = draft(tmp_path, "GPT-5 é bom, mas ABC-12 não")
    assert rules(check.check(path, make_config())) == [(8, "issue", "ABC-12")]


def test_protheus_sources_are_reported(tmp_path, make_config):
    path = draft(tmp_path, "Mexi no JURA106.tlpp e no MATA410.PRW e no x.ch, y.aph, z.prx")
    found = [t for _, r, t in rules(check.check(path, make_config())) if r == "fonte"]
    assert found == ["JURA106.tlpp", "MATA410.PRW", "x.ch", "y.aph", "z.prx"]


def test_emails_and_ips_are_reported(tmp_path, make_config):
    path = draft(tmp_path, "Fale com joao.silva@empresa.com.br no 10.0.12.7")
    assert rules(check.check(path, make_config())) == [
        (8, "email", "joao.silva@empresa.com.br"),
        (8, "ip", "10.0.12.7"),
    ]


def test_internal_domains_and_their_subdomains_are_reported(tmp_path, make_config):
    path = draft(
        tmp_path,
        "Veja https://intranet.empresa.com/wiki\n"
        "e http://jira.intranet.empresa.com/x\n"
        "mas https://naointranet.empresa.com.evil.io e https://github.com/x são públicos",
    )
    assert [(line, r) for line, r, _ in rules(check.check(path, make_config()))] == [
        (8, "dominio-interno"),
        (9, "dominio-interno"),
    ]


def test_credential_shaped_tokens_are_reported(tmp_path, make_config):
    path = draft(
        tmp_path,
        "sk-ant-api03-abcdefghijklmnopqrstuv\n"
        "ghp_abcdefghijklmnopqrstuvwxyz0123456789\n"
        "AKIAABCDEFGHIJKLMNOP\n"
        "xoxb-1234567890-abcdefghij\n"
        "github_pat_11ABCDEFG0123456789_abcdef\n"
        "o sk-learn e o skill não são segredos",
    )
    found = rules(check.check(path, make_config()))
    assert [(line, r) for line, r, _ in found] == [(n, "credencial") for n in range(8, 13)]


def test_forbidden_terms_ignore_case_and_accents(tmp_path, make_config):
    path = draft(tmp_path, "Projeto no cliente acmé\nO SISTEMA INTERNO caiu\nAcmetal é outro")
    assert rules(check.check(path, make_config())) == [
        (8, "termo-proibido", "cliente acmé"),
        (9, "termo-proibido", "SISTEMA INTERNO"),
    ]


def test_long_posts_are_reported(tmp_path, make_config):
    path = draft(tmp_path, "a" * 3001)
    assert [r for _, r, _ in rules(check.check(path, make_config()))] == ["tamanho"]
    assert check.check(draft(tmp_path, "a" * 3000), make_config()) == []


def test_a_draft_without_a_post_section_is_reported(tmp_path, make_config):
    path = tmp_path / "x.md"
    path.write_text("# Só título\n\nTexto solto com PROJ-1\n")
    assert [r for _, r, _ in rules(check.check(path, make_config()))] == ["formato"]


def test_only_the_post_body_is_checked(tmp_path, make_config):
    path = draft(tmp_path, "Corpo limpo")
    assert check.check(path, make_config()) == []


def test_findings_carry_the_file(tmp_path, make_config):
    path = draft(tmp_path, "ABC-1")
    assert check.check(path, make_config())[0].path == path


def test_issue_keys_survive_reformatting(tmp_path, make_config):
    path = draft(
        tmp_path,
        "minúscula proj-1234\n"
        "travessão PROJ – 1234\n"
        "hífen inseparável PROJ‑1234\n"
        "espaço PROJ 1234\n"
        "zero-width PR​OJ-1234\n"
        "quebrada PROJ-\n"
        "1234 no meio",
    )
    lines = [line for line, rule, _ in rules(check.check(path, make_config())) if rule == "issue"]
    assert lines == [8, 9, 10, 11, 12, 13]


def test_allowed_terms_are_masked_ignoring_case(tmp_path, make_config):
    path = draft(tmp_path, "o gpt-5 e o GPT-5 respondem")
    assert check.check(path, make_config()) == []


def test_internal_hosts_are_reported_in_any_prose_form(tmp_path, make_config):
    path = draft(
        tmp_path,
        "Vi em https://intranet.empresa.com.\n"
        "(https://intranet.empresa.com)\n"
        "<HTTPS://Intranet.Empresa.com/x>\n"
        "sem esquema intranet.empresa.com/wiki\n"
        "subdomínio jira.intranet.empresa.com\n"
        "parecido naointranet.empresa.com e intranet.empresa.com.evil.io",
    )
    lines = [
        line for line, r, _ in rules(check.check(path, make_config())) if r == "dominio-interno"
    ]
    assert lines == [8, 9, 10, 11, 12]


def test_configured_domains_match_regardless_of_their_case(tmp_path, make_config):
    import dataclasses

    cfg = dataclasses.replace(make_config(), internal_domains=("Intranet.Empresa.COM",))
    path = draft(tmp_path, "https://intranet.empresa.com/x")
    assert [r for _, r, _ in rules(check.check(path, cfg))] == ["dominio-interno"]


def test_forbidden_terms_survive_spacing_hyphens_plurals_and_wraps(tmp_path, make_config):
    path = draft(
        tmp_path,
        "o cliente  acme\no Cliente-Acme\nos clientes acmes não\no cliente\nacme de novo",
    )
    lines = [
        line for line, r, _ in rules(check.check(path, make_config())) if r == "termo-proibido"
    ]
    assert lines == [8, 9, 10, 11]


def test_more_credential_shapes_are_reported(tmp_path, make_config):
    path = draft(
        tmp_path,
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghij\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "AIzaSyA1234567890abcdefghijklmnopqrstuv\n"
        "sk_live_abcdefghijklmnopqrstuvwx\n"
        "https://hooks.slack.com/services/T000/B000/XXXX\n"
        "senha=hunter2",
    )
    lines = [line for line, r, _ in rules(check.check(path, make_config())) if r == "credencial"]
    assert lines == [8, 9, 10, 11, 12, 13]


def test_user_functions_and_obfuscated_ips_are_reported(tmp_path, make_config):
    path = draft(tmp_path, "Chamei a U_MINHAFUNC\nno 10[.]0[.]0[.]1")
    assert [(line, r) for line, r, _ in rules(check.check(path, make_config()))] == [
        (8, "fonte"),
        (9, "ip"),
    ]


def test_every_post_section_is_checked(tmp_path, make_config):
    path = draft(tmp_path, "limpo\n\n## Post\n\nsegunda versão com PROJ-1")
    assert [r for _, r, _ in rules(check.check(path, make_config()))] == ["issue"]
