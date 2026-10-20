#!/usr/bin/env bash
# Installs two systemd user timers:
#   linkedin-rascunhos  Mondays 08:30, runs /linkedin-rascunhos headless, then the publisher
#   linkedin-publicar   hourly 09:00-18:00, runs `linkedin publicar` (review file, posting)
#   scripts/instalar-agenda.sh            install and enable
#   scripts/instalar-agenda.sh --remover  disable and remove
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNITS="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME="linkedin-rascunhos"
PUBLISH="linkedin-publicar"

if [[ "${1:-}" == "--remover" ]]; then
  for unit in "$NAME" "$PUBLISH"; do
    systemctl --user disable --now "$unit.timer" 2>/dev/null || true
    rm -f "$UNITS/$unit.service" "$UNITS/$unit.timer"
  done
  systemctl --user daemon-reload
  echo "removido"
  exit 0
fi

CLAUDE="$(command -v claude)" || { echo "claude não está no PATH" >&2; exit 1; }
UV="$(command -v uv)" || { echo "uv não está no PATH" >&2; exit 1; }
read -r SECOND_BRAIN DRAFTS < <(cd "$REPO" && "$UV" run --quiet python -c \
  'from linkedin_ia import config; c = config.load(); print(c.second_brain, c.drafts_dir)')

# The drafts agent may edit the drafts folder, so the review file and the images must live
# outside it: otherwise it could tick its own drafts or swap an approved image.
(cd "$REPO" && "$UV" run --quiet python -c '
from linkedin_ia import config
c = config.load()
drafts = c.drafts_dir.resolve()
inside = [str(p) for p in (c.review_file, c.images_dir) if p.resolve().is_relative_to(drafts)]
raise SystemExit(f"dentro da pasta de rascunhos: {inside}" if inside else 0)
')

for path in "$REPO" "$SECOND_BRAIN" "$DRAFTS" "$CLAUDE" "$UV"; do
  if [[ "$path" =~ [[:space:]%\$\"\\] ]]; then
    echo "caminho com espaço ou caractere especial não suportado: $path" >&2
    exit 1
  fi
done

# The headless agent reads untrusted text (the digest), so it gets only what the job needs:
# read the repo's skills and digests, the second brain and READMEs; write drafts; run three
# CLI commands. dontAsk denies everything else: the repo itself (the code `uv run linkedin`
# executes), the review file and .estado/ (where approvals live), `linkedin publicar` and
# `linkedin login`.
ALLOWED=(
  "Bash(uv run linkedin coletar)"
  "Bash(uv run linkedin fila)"
  "Bash(uv run linkedin checar:*)"
  "Read(/$REPO/.claude/skills/**)"
  "Read(/$REPO/dossies/**)"
  "Read(/$SECOND_BRAIN/**)"
  "Read(~/dev/*/README*)"
  "Edit(/$DRAFTS/**)"
)
DENIED=(
  "Edit(/$REPO/**)"
  "Edit(/$SECOND_BRAIN/.obsidian/**)"
  "Read(/$SECOND_BRAIN/.obsidian/**)"
)
quote() { printf '"%s" ' "$@"; }

mkdir -p "$UNITS"
cat > "$UNITS/$NAME.service" <<UNIT
[Unit]
Description=Rascunhos semanais do LinkedIn (claude -p /linkedin-rascunhos)

[Service]
Type=oneshot
TimeoutStartSec=30min
WorkingDirectory=$REPO
Environment="PATH=$(dirname "$UV"):$(dirname "$CLAUDE"):/usr/local/bin:/usr/bin:/bin"
ExecStart=$CLAUDE -p /linkedin-rascunhos --add-dir $SECOND_BRAIN --permission-mode dontAsk --allowedTools $(quote "${ALLOWED[@]}")--disallowedTools $(quote "${DENIED[@]}")
ExecStartPost=-$UV run --quiet linkedin publicar
UNIT

cat > "$UNITS/$NAME.timer" <<UNIT
[Unit]
Description=Rascunhos do LinkedIn toda segunda às 08:30

[Timer]
OnCalendar=Mon *-*-* 08:30:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT

cat > "$UNITS/$PUBLISH.service" <<UNIT
[Unit]
Description=Publica no LinkedIn os rascunhos aprovados (linkedin publicar)

[Service]
Type=oneshot
TimeoutStartSec=10min
WorkingDirectory=$REPO
Environment="PATH=$(dirname "$UV"):/usr/local/bin:/usr/bin:/bin"
ExecStart=$UV run --quiet linkedin publicar
UNIT

cat > "$UNITS/$PUBLISH.timer" <<UNIT
[Unit]
Description=Publicação do LinkedIn de hora em hora, das 9h às 18h

[Timer]
OnCalendar=*-*-* 09..18:00:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer" "$PUBLISH.timer"
systemctl --user list-timers "$NAME.timer" "$PUBLISH.timer" --no-pager
echo "rodar agora: systemctl --user start $NAME.service · $PUBLISH.service"
echo "logs: journalctl --user -u $NAME -u $PUBLISH"
