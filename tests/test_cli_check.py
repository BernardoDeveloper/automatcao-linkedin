from linkedin_ia import cli


def write(path, body):
    path.write_text(f"---\nstatus: rascunho\n---\n# T\n\n## Post\n\n{body}\n", encoding="utf-8")
    return path


def test_checar_exits_2_and_prints_each_finding(tmp_path, make_config, capsys):
    bad = write(tmp_path / "a.md", "Fechei a ABC-12")
    good = write(tmp_path / "b.md", "Tudo certo")

    assert cli.main(["checar", str(good), str(bad)], config=make_config()) == 2
    assert capsys.readouterr().out == f"{bad}:8: issue: ABC-12\n"


def test_checar_exits_0_when_clean(tmp_path, make_config, capsys):
    good = write(tmp_path / "b.md", "Tudo certo")
    assert cli.main(["checar", str(good)], config=make_config()) == 0
    assert "sem achados" in capsys.readouterr().out
