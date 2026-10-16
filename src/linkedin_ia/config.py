"""Loads config.toml, falling back to config.example.toml on a fresh clone."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    second_brain: Path
    ai_memory: Path
    claude_sessions: Path
    repo_roots: tuple[Path, ...]
    author_email: str
    default_days: int
    max_items: int
    excerpt_length: int
    min_mentions: int
    keywords: tuple[str, ...]
    drafts_dir: Path
    internal_domains: tuple[str, ...]
    forbidden_terms: tuple[str, ...]
    allowed_terms: tuple[str, ...]
    root: Path = ROOT

    @property
    def digest_dir(self) -> Path:
        return self.root / "dossies"

    @property
    def state_file(self) -> Path:
        return self.root / ".estado" / "ultima-coleta"


def _path(value: str) -> Path:
    return Path(value).expanduser()


def load(path: Path | None = None, root: Path = ROOT) -> Config:
    if path is None:
        path = root / "config.toml"
        if not path.exists():
            path = root / "config.example.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    sources, collect = data["fontes"], data["coleta"]
    drafts, secret = data["rascunhos"], data["confidencialidade"]
    second_brain = _path(sources["second_brain"])
    return Config(
        second_brain=second_brain,
        ai_memory=_path(sources["ai_memory"]),
        claude_sessions=_path(sources["claude_sessoes"]),
        repo_roots=tuple(_path(p) for p in sources["repositorios"]),
        author_email=sources["email_autor"],
        default_days=collect["dias_padrao"],
        max_items=collect["max_itens"],
        excerpt_length=collect["tamanho_trecho"],
        min_mentions=collect.get("min_mencoes", 1),
        keywords=tuple(collect["palavras_chave"]),
        drafts_dir=second_brain / drafts["pasta"],
        internal_domains=tuple(secret["dominios_internos"]),
        forbidden_terms=tuple(secret["termos_proibidos"]),
        allowed_terms=tuple(secret["permitidos"]),
        root=root,
    )
