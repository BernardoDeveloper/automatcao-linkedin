from pathlib import Path

import pytest

from linkedin_ia import config

TEMPLATE = """
[fontes]
second_brain = "{base}/sb"
ai_memory = "{base}/aim"
claude_sessoes = "{base}/claude"
repositorios = ["{base}/dev"]
email_autor = "eu@exemplo.com"

[coleta]
dias_padrao = 14
max_itens = {max_items}
tamanho_trecho = 80
min_mencoes = 2
palavras_chave = ["ia", "claude", "inteligência artificial", "rag"]

[rascunhos]
pasta = "LinkedIn/Posts"

[confidencialidade]
dominios_internos = ["intranet.empresa.com"]
termos_proibidos = ["Cliente Acme", "Sistema Interno"]
permitidos = ["GPT-5"]
"""


@pytest.fixture
def make_config(tmp_path: Path):
    def make(max_items: int = 30) -> config.Config:
        path = tmp_path / "config.toml"
        path.write_text(TEMPLATE.format(base=tmp_path, max_items=max_items), encoding="utf-8")
        return config.load(root=tmp_path)

    return make
