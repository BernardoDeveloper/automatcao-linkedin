---
name: linkedin-rascunhos
description: Escreve de 1 a 3 rascunhos de post do LinkedIn sobre IA a partir do dossiê da semana (second brain, ai-memory, commits, sessões do Claude Code) e os grava no second brain para o Bernardo revisar. Use na execução semanal, quando ele pedir "rascunhos do LinkedIn", "posts da semana", ou quando quiser transformar o que andou fazendo com IA em post.
---

Você escreve rascunhos. Nunca publica nada (docs/adr/0001-drafts-only-no-linkedin-api.md).
Rode tudo a partir da raiz deste repositório.

## 1. Coletar

```bash
uv run linkedin coletar        # imprime o caminho do dossiê
uv run linkedin fila           # imprime "pasta: <pasta dos rascunhos>" e o que já existe
```

Leia o dossiê inteiro. Leia `references/voz.md` e `references/modelo.md`. Para cada rascunho
existente na fila, leia só o título e o `## Resumo` — é o que diz quais temas já foram usados.

Se um item do dossiê parecer promissor mas o trecho for curto, abra a nota de origem
(o caminho é relativo ao second brain: `second_brain` em `config.toml`, por padrão
`~/Documents/second-brain`) ou o README do repositório em `~/dev/<repo>`.

## 2. Escolher os temas

- De 1 a 3 temas. Menos é melhor que fraco. Prefira o que tem resultado concreto.
- Pule tema que um rascunho existente já cobre, em qualquer status.
- Varie o pilar (`aprendizado`, `bastidor`, `apresentacao`, `opiniao`).
- Ignore o que não é IA ou desenvolvimento: finanças, família, saúde, viagens, drones/FPV
  (FPV é a marca do Instagram, outra área). Uma sessão pessoal que usou o Claude não é tema;
  o *jeito* de usar pode ser.
- Se houver material de palestra no trabalho, prefira a skill `linkedin-apresentacao`.

Se nada no dossiê render post, não escreva nenhum rascunho: diga em uma linha por quê e pare.

## 3. Escrever

Para cada tema, crie `<pasta>/AAAA-MM-DD - <Título>.md` (data de hoje) a partir de
`references/modelo.md`:

- `status: rascunho`, `criado` hoje, `publicar_em` nos próximos dias úteis — terça e quinta,
  um post por dia, sem colidir com o `publicar_em` de rascunhos já na fila.
- `fontes`: os itens do dossiê usados — `"[[Nome da nota]]"` para nota do second brain,
  `"git: <repo>"`, `"claude: <projeto>"`, `"ai-memory: <página>"`.
- `## Post` segue o guia de voz. Escreva em português do Brasil.

## 4. Checar

```bash
uv run linkedin checar "<rascunho>"
```

Exit 2 é um achado: reescreva o trecho do `## Post` sem a informação (troque o caso pela
técnica) e rode de novo, até exit 0. Nunca contorne um achado trocando o formato do texto
(ex.: "DJURPFS – 1234").

## 5. Avisar

Em `TAREFAS.md` do second brain, na seção `## 📆 Esta semana` (ou a mais próxima que
existir), adicione uma linha só:

```
- [ ] Revisar rascunhos do LinkedIn: [[AAAA-MM-DD - Título 1]], [[AAAA-MM-DD - Título 2]] — [[LinkedIn]] 📅 <publicar_em do primeiro>
```

Termine com uma linha por rascunho: título, pilar, `publicar_em`.
