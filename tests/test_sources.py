import json
import os
import subprocess
from datetime import datetime, timedelta

from linkedin_ia import sources

NOW = datetime.now().astimezone()
SINCE = NOW - timedelta(days=7)


def write(path, text, days_ago=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    stamp = (NOW - timedelta(days=days_ago)).timestamp()
    os.utime(path, (stamp, stamp))
    return path


def origins(items):
    return sorted(i.origin for i in items)


def test_second_brain_keeps_recent_notes_that_mention_ai(make_config, tmp_path):
    cfg = make_config()
    sb = tmp_path / "sb"
    write(sb / "03-Recursos/RAG local.md", "---\ntipo: nota\n---\n# Testei RAG\nClaude ajudou\n")
    write(sb / "02-Areas/Saude/Saude.md", "# Consulta no dia 5 na Bahia\n")
    write(sb / "03-Recursos/Antiga.md", "# Claude antigo\n", days_ago=30)
    write(sb / "_templates/modelo.md", "# IA template\n")
    write(sb / ".obsidian/x.md", "# IA config\n")
    write(sb / "LinkedIn/Posts/2026-10-01 - Post.md", "# Post sobre IA\n")

    items = sources.second_brain(cfg, SINCE)

    assert origins(items) == ["03-Recursos/RAG local.md"]
    assert items[0].text.startswith("# Testei RAG")


def test_keywords_match_whole_words_ignoring_case(make_config, tmp_path):
    cfg = make_config()
    sb = tmp_path / "sb"
    write(sb / "a.md", "Usei ia no trabalho, IA de novo")
    write(sb / "b.md", "Hoje é dia de praia na Bahia, dia bom")
    write(sb / "c.md", "Curso de Inteligência Artificial com RAG")
    write(sb / "d.md", "Aprendi CLAUDE code e claude")

    assert origins(sources.second_brain(cfg, SINCE)) == ["a.md", "c.md", "d.md"]


def test_notes_need_the_minimum_mentions_outside_urls(make_config, tmp_path):
    cfg = make_config()
    sb = tmp_path / "sb"
    write(sb / "drone.md", "Pedir ao Claude um simulado")
    write(sb / "marca.md", "Design system: https://claude.ai/artifact/x e https://claude.ai/y")
    write(sb / "IA/estudo.md", "Anotei sobre Claude")

    assert origins(sources.second_brain(cfg, SINCE)) == ["IA/estudo.md"]


def test_ai_memory_skips_event_logs_and_manifests(make_config, tmp_path):
    cfg = make_config()
    aim = tmp_path / "aim"
    write(aim / "w/p/decisions/usar-rag.md", "# Decidimos usar RAG com Claude\n")
    write(aim / "w/p/log-2026-10.md", "## session-start | claude\n")
    write(aim / "w/_meta.md", "---\ntype: Scope Manifest\n---\nclaude")

    assert origins(sources.ai_memory(cfg, SINCE)) == ["w/p/decisions/usar-rag.md"]


def git_repo(path, *commits):
    path.mkdir(parents=True)
    run = lambda *a, **kw: subprocess.run(["git", "-C", str(path), *a], check=True, **kw)  # noqa: E731
    run("init", "-q")
    for email, subject in commits:
        env = {
            **os.environ,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_EMAIL": email,
            "GIT_AUTHOR_NAME": "x",
            "GIT_COMMITTER_NAME": "x",
        }
        run("commit", "-q", "--allow-empty", "-m", subject, env=env)


def test_git_collects_only_the_author_commits_per_repository(make_config, tmp_path):
    cfg = make_config()
    git_repo(
        tmp_path / "dev/agente",
        ("eu@exemplo.com", "feat: busca vetorial"),
        ("outro@exemplo.com", "fix: alheio"),
    )
    git_repo(tmp_path / "dev/site", ("eu@exemplo.com", "docs: readme"))
    (tmp_path / "dev/sem-git").mkdir()

    items = sources.git(cfg, SINCE)

    assert sorted((i.origin, i.text) for i in items) == [
        ("agente", "feat: busca vetorial"),
        ("site", "docs: readme"),
    ]


def session(path, *entries, days_ago=0):
    lines = [json.dumps(e) for e in entries]
    return write(path, "\n".join(lines) + "\nnot json\n", days_ago=days_ago)


def prompt(text, when=NOW, kind="user"):
    return {"type": kind, "timestamp": when.isoformat(), "message": {"content": text}}


def test_claude_sessions_keep_typed_prompts_about_ai(make_config, tmp_path):
    cfg = make_config()
    session(
        tmp_path / "claude/-home-eu-dev-agente/s1.jsonl",
        prompt("Monte um RAG com a documentação"),
        prompt("Abra https://claude.ai/x"),
        prompt("<command-name>/mcp</command-name> claude"),
        prompt("Instale o tema do Obsidian"),
        prompt("resposta do claude", kind="assistant"),
        prompt("Claude, antigo", when=NOW - timedelta(days=30)),
        {"type": "user", "timestamp": NOW.isoformat(), "message": {"content": [{"type": "x"}]}},
    )

    items = sources.claude_sessions(cfg, SINCE)

    assert [(i.origin, i.text) for i in items] == [("agente", "Monte um RAG com a documentação")]


def test_session_origin_is_the_project_folder(make_config, tmp_path):
    cfg = make_config()
    session(tmp_path / "claude/-home-eu/s.jsonl", prompt("Claude, ajuda"))
    session(tmp_path / "claude/-home-eu-Documents-second-brain/s.jsonl", prompt("IA aqui"))

    assert origins(sources.claude_sessions(cfg, SINCE)) == ["Documents-second-brain", "~"]
