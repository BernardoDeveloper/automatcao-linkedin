"""Loads config.toml, falling back to config.example.toml on a fresh clone."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_REVIEW = "02-Areas/Carreira/LinkedIn/Revisão de posts.md"
DEFAULT_IMAGES = "02-Areas/Carreira/LinkedIn/Posts/imagens"
DEFAULT_API_VERSION = "202610"
DEFAULT_TOKEN = "~/.config/linkedin-ia/token.json"


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
    review_file: Path
    images_dir: Path
    api_version: str
    token_file: Path
    root: Path = ROOT

    @property
    def digest_dir(self) -> Path:
        return self.root / "dossies"

    @property
    def state_file(self) -> Path:
        return self.root / ".estado" / "ultima-coleta"

    @property
    def publish_state_file(self) -> Path:
        return self.root / ".estado" / "publicacao.json"


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
    api = data.get("linkedin", {})
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
        review_file=second_brain / drafts.get("revisao", DEFAULT_REVIEW),
        images_dir=second_brain / drafts.get("imagens", DEFAULT_IMAGES),
        api_version=str(api.get("versao", DEFAULT_API_VERSION)),
        token_file=_path(api.get("token", DEFAULT_TOKEN)),
        root=root,
    )
