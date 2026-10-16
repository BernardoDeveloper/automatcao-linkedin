from datetime import datetime, timedelta

from linkedin_ia import cli, digest, state
from linkedin_ia.sources import Item

NOW = datetime.now().astimezone()


def test_digest_names_missing_sources_and_still_writes(make_config, tmp_path, capsys):
    cfg = make_config()
    (tmp_path / "sb").mkdir()
    (tmp_path / "sb/Nota.md").write_text("# Estudei RAG com Claude\n" + "texto " * 50)

    assert cli.main(["coletar"], config=cfg) == 0

    path = tmp_path / "dossies" / f"{NOW:%Y-%m-%d}.md"
    assert capsys.readouterr().out.strip() == str(path)
    text = path.read_text()
    assert "## Second brain (1)" in text
    assert "`Nota.md`" in text
    assert f"- ai-memory: `{tmp_path / 'aim'}` não existe" in text
    assert "- git: " in text and "- claude: " in text


def test_a_successful_run_is_recorded(make_config):
    cfg = make_config()
    cli.main(["coletar"], config=cfg)
    assert abs(state.last_run(cfg) - NOW) < timedelta(minutes=1)


def test_items_are_capped_most_recent_first(make_config, monkeypatch):
    cfg = make_config(max_items=2)
    fake = [Item("second-brain", NOW - timedelta(days=d), f"n{d}.md", "IA") for d in range(5)]
    monkeypatch.setattr(digest.sources, "second_brain", lambda c, s: fake)
    cfg.second_brain.mkdir()

    collection = digest.collect(cfg, NOW - timedelta(days=7), NOW)

    assert [i.origin for i in collection.items["second-brain"]] == ["n0.md", "n1.md"]


def test_excerpts_are_cut_to_the_configured_length(make_config):
    cfg = make_config()
    collection = digest.Collection(NOW, NOW, {"git": [Item("git", NOW, "r", "x" * 500)]})
    excerpt = digest.render(collection, cfg).split("> ")[1].strip()
    assert len(excerpt) == 80 and excerpt.endswith("…")
