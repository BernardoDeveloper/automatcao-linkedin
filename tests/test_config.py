import shutil
from pathlib import Path

from linkedin_ia import config

REPO = Path(__file__).resolve().parents[1]


def test_falls_back_to_the_example_on_a_fresh_clone(tmp_path):
    shutil.copy(REPO / "config.example.toml", tmp_path / "config.example.toml")
    cfg = config.load(root=tmp_path)
    assert cfg.second_brain == Path("~/Documents/second-brain").expanduser()
    assert "claude" in cfg.keywords


def test_config_toml_wins_over_the_example(tmp_path, make_config):
    shutil.copy(REPO / "config.example.toml", tmp_path / "config.example.toml")
    cfg = make_config(max_items=7)
    assert cfg.max_items == 7
    assert cfg.repo_roots == (tmp_path / "dev",)


def test_drafts_dir_is_inside_the_second_brain(make_config, tmp_path):
    cfg = make_config()
    assert cfg.drafts_dir == tmp_path / "sb" / "LinkedIn" / "Posts"
    assert cfg.digest_dir == tmp_path / "dossies"
