---
name: linkedin-apresentacao
description: Escreve um rascunho de post do LinkedIn sobre uma palestra ou treinamento de IA que o Bernardo deu no trabalho, a partir dos slides, do guia, de um link de artifact ou de anotações, e grava no second brain. Use quando ele disser que apresentou, deu um treinamento, fez uma palestra ou uma talk, ou pedir para "postar sobre a apresentação".
---

Você escreve um rascunho. Nunca publica nada (docs/adr/0001-drafts-only-no-linkedin-api.md).
Rode a partir da raiz deste repositório. Leia
`../linkedin-rascunhos/references/voz.md` e `../linkedin-rascunhos/references/modelo.md`.

## 1. Material

Aceite o que vier: caminho de PDF/Markdown, link `claude.ai/artifact/...` (leia com a
ferramenta Artifact, ação `read`), ou anotações coladas. Se não vier nada, procure no
second brain (`second_brain` em `config.toml`, por padrão `~/Documents/second-brain`) por notas com
`apresentação`, `treinamento` ou `slides` em `06-Documentos/Carreira/` e `02-Areas/Carreira/`.

Precisa saber, e pergunte numa mensagem só o que faltar:

- **data** da palestra;
- **público** (ex.: "time de desenvolvimento do jurídico, ~15 pessoas");
- **o que perguntaram ou acharam difícil** — é a parte mais valiosa do post. Se ele não
  souber, siga sem ela e deixe um `<!-- completar: perguntas do público -->` no `## Resumo`.

## 2. Escrever

Um rascunho, `pilar: apresentacao`, `status: rascunho`, `publicar_em` no próximo dia útil.
`fontes` aponta para a nota do material (`"[[Guia IA no dia a dia - AdvPL TLPP]]"`).

O `## Post` conta, nesta ordem: para quem foi, a ideia principal em uma frase, os 3 a 5
pontos que mais funcionaram, o que o público perguntou ou travou, e uma pergunta para quem
lê. Fale da técnica, nunca do caso interno: o modelo escolhido e o porquê pode; o nome do
fonte, a issue e o cliente do exemplo, não.

`## Resumo` → **Imagem sugerida:** foto da apresentação (sem tela com dado interno) ou um
slide genérico.

## 3. Checar e avisar

```bash
uv run linkedin checar "<rascunho>"
```

Reescreva até exit 0. Adicione em `TAREFAS.md` do second brain (seção `## 📆 Esta semana`):

```
- [ ] Revisar post da apresentação: [[AAAA-MM-DD - Título]] — [[LinkedIn]] 📅 <publicar_em>
```
