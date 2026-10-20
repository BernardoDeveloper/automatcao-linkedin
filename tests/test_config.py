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


def test_publishing_settings_default_when_the_config_predates_them(make_config, tmp_path):
    cfg = make_config()
    assert cfg.review_file == tmp_path / "sb" / "02-Areas/Carreira/LinkedIn/Revisão de posts.md"
    assert cfg.images_dir == tmp_path / "sb" / "02-Areas/Carreira/LinkedIn/Imagens"
    assert cfg.api_version == "202610"
    assert cfg.token_file == Path("~/.config/linkedin-ia/token.json").expanduser()
    assert cfg.publish_state_file == tmp_path / ".estado" / "publicacao.json"


def test_publishing_settings_come_from_the_config(make_config, tmp_path):
    path = tmp_path / "config.toml"
    make_config()
    text = path.read_text(encoding="utf-8").replace(
        '[rascunhos]\npasta = "LinkedIn/Posts"',
        '[rascunhos]\npasta = "LinkedIn/Posts"\nrevisao = "LinkedIn/Rev.md"\nimagens = "img"',
    )
    text += f'\n[linkedin]\nversao = "202701"\ntoken = "{tmp_path}/tok.json"\n'
    path.write_text(text, encoding="utf-8")
    cfg = config.load(root=tmp_path)
    assert cfg.review_file == tmp_path / "sb" / "LinkedIn" / "Rev.md"
    assert cfg.images_dir == tmp_path / "sb" / "img"
    assert cfg.api_version == "202701"
    assert cfg.token_file == tmp_path / "tok.json"
