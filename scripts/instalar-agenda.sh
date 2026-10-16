#!/usr/bin/env bash
# Installs the weekly run: a systemd user timer that runs /linkedin-rascunhos headless.
#   scripts/instalar-agenda.sh            install and enable (Mondays 08:30)
#   scripts/instalar-agenda.sh --remover  disable and remove
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNITS="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME="linkedin-rascunhos"

if [[ "${1:-}" == "--remover" ]]; then
  systemctl --user disable --now "$NAME.timer" 2>/dev/null || true
  rm -f "$UNITS/$NAME.service" "$UNITS/$NAME.timer"
  systemctl --user daemon-reload
  echo "removido"
  exit 0
fi

CLAUDE="$(command -v claude)" || { echo "claude não está no PATH" >&2; exit 1; }
UV="$(command -v uv)" || { echo "uv não está no PATH" >&2; exit 1; }
read -r SECOND_BRAIN DRAFTS < <(cd "$REPO" && "$UV" run --quiet python -c \
  'from linkedin_ia import config; c = config.load(); print(c.second_brain, c.drafts_dir)')

for path in "$REPO" "$SECOND_BRAIN" "$DRAFTS" "$CLAUDE" "$UV"; do
  if [[ "$path" =~ [[:space:]%\$\"\\] ]]; then
    echo "caminho com espaço ou caractere especial não suportado: $path" >&2
    exit 1
  fi
done

# The headless agent reads untrusted text (the digest), so it gets only what the job needs:
# read the repo's skills and digests, the second brain and READMEs; write drafts and
# TAREFAS.md; run three CLI commands. dontAsk denies everything else, and the repo itself
# (the code `uv run linkedin` executes) is never writable.
ALLOWED=(
  "Bash(uv run linkedin coletar)"
  "Bash(uv run linkedin fila)"
  "Bash(uv run linkedin checar:*)"
  "Read(/$REPO/.claude/skills/**)"
  "Read(/$REPO/dossies/**)"
  "Read(/$SECOND_BRAIN/**)"
  "Read(~/dev/*/README*)"
  "Edit(/$DRAFTS/**)"
  "Edit(/$SECOND_BRAIN/TAREFAS.md)"
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
ExecStartPost=-/usr/bin/notify-send "LinkedIn" "Rascunhos da semana prontos no second brain"
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

systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer"
systemctl --user list-timers "$NAME.timer" --no-pager
echo "rodar agora: systemctl --user start $NAME.service · logs: journalctl --user -u $NAME"
