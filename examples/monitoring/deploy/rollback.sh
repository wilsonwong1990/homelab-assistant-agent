#!/usr/bin/env bash
# Switch /opt/homelab-monitor back to the previous (or a named) release and
# restart running components. Configuration and secrets are not touched.
set -euo pipefail

PREFIX=/opt/homelab-monitor
RELEASES=/opt/homelab-monitor-releases
ETC=/etc/homelab-monitor
UNITS=(homelab-monitor@monitor.service homelab-monitor@notify.service homelab-monitor@worker.service
       homelab-discord.service homelab-executor.service)

usage() {
  cat <<'EOF'
Usage: sudo ./rollback.sh [RELEASE_ID]
       sudo ./rollback.sh --list

Without RELEASE_ID, returns to the release recorded before the last switch.
Database backups taken before each upgrade are in /var/backups/homelab-monitor;
restore one only if the newer release changed the schema (see DEPLOY.md).
EOF
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "run as root (sudo)"
current="$(readlink -f "$PREFIX" 2>/dev/null || true)"

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
  --list)
    for dir in "$RELEASES"/*/; do
      dir="${dir%/}"
      [[ -f "$dir/.install-complete" ]] || continue
      marker=" "; [[ "$dir" == "$current" ]] && marker="*"
      printf '%s %s  built %s\n' "$marker" "$(basename "$dir")" "$(cat "$dir/.install-complete")"
    done
    exit 0 ;;
  "") [[ -f "$RELEASES/.previous" ]] || die "no previous release recorded; pass a RELEASE_ID (see --list)"
      target="$(cat "$RELEASES/.previous")" ;;
  *) [[ "$1" =~ ^[0-9a-f]{7,40}$ ]] || die "invalid release id: $1"
     target="$RELEASES/$1" ;;
esac

[[ -f "$target/.install-complete" ]] || die "$target is not a completed release"
[[ "$target" != "$current" ]] || die "$(basename "$target") is already current"

(cd / && runuser -u homelab-monitor -- "$target/.venv/bin/python" -m homelab_monitor \
  --config "$ETC/monitoring.json" validate) || die "current configuration does not validate with $(basename "$target")"

ln -sfn "$target" "$PREFIX.new"
mv -T "$PREFIX.new" "$PREFIX"
[[ -n "$current" ]] && printf '%s\n' "$current" > "$RELEASES/.previous"
# Unit files are shared across releases; reinstall the target's copies.
for unit in homelab-monitor@.service homelab-discord.service homelab-executor.service; do
  install -o root -g root -m 0644 "$target/examples/monitoring/$unit" "/etc/systemd/system/$unit"
done
systemctl daemon-reload
for unit in "${UNITS[@]}"; do
  systemctl try-restart "$unit" || echo "WARN: restart of $unit failed; inspect journalctl -u $unit" >&2
done
echo "rolled back to $(basename "$target"); run deploy/smoke-test.sh"
