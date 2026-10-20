import json
import stat
from dataclasses import replace
from datetime import datetime, timedelta

from linkedin_ia import cli, credentials
from linkedin_ia.linkedin_api import Response

NOW = datetime(2026, 10, 20, 9, 0).astimezone()


def test_saved_token_is_readable_only_by_the_user_and_loads_back(tmp_path):
    path = tmp_path / "cfg" / "token.json"
    token = credentials.Token("tok", "urn:li:person:p", "Bernardo", NOW + timedelta(days=60))
    credentials.save(path, token)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert credentials.load(path) == token


def test_missing_or_broken_token_file_is_no_token(tmp_path):
    assert credentials.load(tmp_path / "nada.json") is None
    (tmp_path / "ruim.json").write_text("{", encoding="utf-8")
    assert credentials.load(tmp_path / "ruim.json") is None


def test_days_left():
    token = credentials.Token("t", "u", "n", NOW + timedelta(days=7))
    assert token.days_left(NOW) == 7


def fake_userinfo(status=200, body=None):
    def transport(request):
        transport.request = request
        payload = body if body is not None else {"sub": "abc", "name": "Bernardo"}
        return Response(status, {}, json.dumps(payload).encode())

    return transport


def test_login_stores_the_pasted_token_with_its_member(make_config, monkeypatch, capsys, tmp_path):
    cfg = make_config()
    cfg = replace(cfg, token_file=tmp_path / "t" / "token.json")
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "  segredo-123  ")
    transport = fake_userinfo()

    assert cli.main(["login"], config=cfg, transport=transport) == 0

    stored = credentials.load(cfg.token_file)
    assert stored.access_token == "segredo-123"
    assert stored.person_urn == "urn:li:person:abc"
    assert 59 < stored.days_left(datetime.now().astimezone()) <= 60
    assert transport.request.get_header("Authorization") == "Bearer segredo-123"
    out = capsys.readouterr()
    assert "segredo-123" not in out.out + out.err


def test_login_with_a_rejected_token_stores_nothing(make_config, monkeypatch, capsys, tmp_path):
    cfg = make_config()
    cfg = replace(cfg, token_file=tmp_path / "t" / "token.json")
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "segredo-123")
    transport = fake_userinfo(401, {"message": "Invalid access token"})

    assert cli.main(["login"], config=cfg, transport=transport) == 2

    assert not cfg.token_file.exists()
    out = capsys.readouterr()
    assert "segredo-123" not in out.out + out.err


def test_overwriting_a_loose_token_file_leaves_it_private(tmp_path):
    path = tmp_path / "token.json"
    path.write_text("{}", encoding="utf-8")
    path.chmod(0o644)
    credentials.save(path, credentials.Token("t", "u", "n", NOW))
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert [p.name for p in tmp_path.iterdir()] == ["token.json"]
