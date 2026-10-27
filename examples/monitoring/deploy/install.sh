#!/usr/bin/env bash
# Install or upgrade the homelab monitoring companion on Ubuntu 24.04+/Debian 13+
# (server or desktop). Idempotent. Never overwrites existing configuration or
# secrets, never enables execution, and never writes sudoers.
# See examples/monitoring/DEPLOY.md.
set -euo pipefail
umask 022

PREFIX=/opt/homelab-monitor
RELEASES=/opt/homelab-monitor-releases
ETC=/etc/homelab-monitor
STATE=/var/lib/homelab-monitor
ACTION_STATE=/var/lib/homelab-executor
BACKUPS=/var/backups/homelab-monitor
UNIT_DIR=/etc/systemd/system
CORE_UNITS=(homelab-monitor@monitor.service homelab-monitor@notify.service homelab-monitor@worker.service)
ALL_UNITS=("${CORE_UNITS[@]}" homelab-discord.service homelab-executor.service)
SLEEP_TARGETS=(sleep.target suspend.target hibernate.target hybrid-sleep.target)

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REF=HEAD
INSTALL_OLLAMA=0
MODEL=""
ENABLE=0
NO_SLEEP=0
KEEP=3
ALLOW_UNSUPPORTED=0

usage() {
  cat <<'EOF'
Usage: sudo ./install.sh [options]

  --source DIR          Git checkout to install from (default: this repository)
  --ref REF             Commit/tag/branch to install (default: HEAD)
  --install-ollama      Install Ollama, bind it to loopback, set OLLAMA_NO_CLOUD=1
  --model NAME          Pull this local model (default: model.name from config)
  --no-sleep            Mask suspend/hibernate so a desktop keeps monitoring
  --enable              Enable and start monitor/notify/worker (refused while
                        configuration still contains placeholders)
  --keep N              Older releases to retain besides current/previous (default: 3)
  --allow-unsupported   Proceed on an OS other than Ubuntu 24.04+/Debian 13+
  -h, --help            Show this help
EOF
}

log() { printf '==> %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*" >&2; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="${2:?--source needs a value}"; shift 2 ;;
    --ref) REF="${2:?--ref needs a value}"; shift 2 ;;
    --install-ollama) INSTALL_OLLAMA=1; shift ;;
    --model) MODEL="${2:?--model needs a value}"; shift 2 ;;
    --no-sleep) NO_SLEEP=1; shift ;;
    --enable) ENABLE=1; shift ;;
    --keep) KEEP="${2:?--keep needs a value}"; shift 2 ;;
    --allow-unsupported) ALLOW_UNSUPPORTED=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

[[ "$KEEP" =~ ^[0-9]+$ ]] || die "--keep must be a non-negative integer"
[[ $EUID -eq 0 ]] || die "run as root (sudo)"
command -v systemctl >/dev/null || die "systemd is required"

check_os() {
  [[ -r /etc/os-release ]] || die "cannot read /etc/os-release"
  # shellcheck disable=SC1091
  . /etc/os-release
  local major="${VERSION_ID:-0}" supported=0
  major="${major%%.*}"
  case "${ID:-}" in
    ubuntu) [[ "$major" =~ ^[0-9]+$ && "$major" -ge 24 ]] && supported=1 ;;
    debian) [[ "$major" =~ ^[0-9]+$ && "$major" -ge 13 ]] && supported=1 ;;
  esac
  if [[ $supported -eq 1 ]]; then
    log "OS: ${PRETTY_NAME:-$ID $VERSION_ID}"
  elif [[ $ALLOW_UNSUPPORTED -eq 1 ]]; then
    warn "untested OS ${PRETTY_NAME:-unknown}; continuing because --allow-unsupported was given"
  else
    die "untested OS ${PRETTY_NAME:-unknown}; use Ubuntu 24.04+/Debian 13+ or pass --allow-unsupported"
  fi
}

install_packages() {
  command -v apt-get >/dev/null || die "apt-get is required; install python3, python3-venv, git, curl, sqlite3 manually"
  local missing=() pkg
  for pkg in python3 python3-venv git ca-certificates curl sqlite3; do
    dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q 'install ok installed' || missing+=("$pkg")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    log "installing packages: ${missing[*]}"
    DEBIAN_FRONTEND=noninteractive apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${missing[@]}"
  fi
  python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' || die "Python 3.9+ is required"
}

ensure_group() { getent group "$1" >/dev/null || groupadd --system "$1"; }

ensure_user() {
  local user="$1" group="$2" extra="$3"
  if ! id -u "$user" >/dev/null 2>&1; then
    useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin \
      --gid "$group" ${extra:+--groups "$extra"} "$user"
  fi
  [[ "$(id -gn "$user")" == "$group" ]] || die "$user exists with unexpected primary group $(id -gn "$user")"
}

create_identities() {
  log "ensuring service identities"
  ensure_group homelab-observe
  ensure_group homelab-approve
  # Only monitor/notify/worker write monitoring state.
  ensure_user homelab-monitor homelab-observe ""
  # Discord transport: reads state and may reach the executor socket.
  ensure_user homelab-discord homelab-observe homelab-approve
  # Executor: private action state, reads monitoring state.
  ensure_user homelab-executor homelab-approve homelab-observe
  if id -nG homelab-monitor | tr ' ' '\n' | grep -qx homelab-approve; then
    die "homelab-monitor must not be in homelab-approve"
  fi
}

create_directories() {
  log "ensuring directories and permissions"
  install -d -o root -g root -m 0755 "$ETC" "$RELEASES"
  install -d -o root -g root -m 0700 "$BACKUPS"
  install -d -o homelab-monitor -g homelab-observe -m 2750 "$STATE"
  install -d -o homelab-executor -g homelab-approve -m 0700 "$ACTION_STATE"
}

git_src() { git -c safe.directory="$SOURCE" -C "$SOURCE" "$@"; }

resolve_release() {
  [[ -d "$SOURCE" ]] || die "source $SOURCE does not exist"
  # The checkout may belong to a non-root user; trust it only for these commands.
  RELEASE_ID="$(git_src rev-parse --short=12 "${REF}^{commit}")" || die "cannot resolve $REF in $SOURCE"
  RELEASE_DIR="$RELEASES/$RELEASE_ID"
  if [[ -n "$(git_src status --porcelain --untracked-files=no 2>/dev/null)" ]]; then
    warn "uncommitted changes in $SOURCE are NOT installed; only commit $RELEASE_ID is"
  fi
}

build_release() {
  if [[ -f "$RELEASE_DIR/.install-complete" ]]; then
    log "release $RELEASE_ID already built"
    return
  fi
  rm -rf "$RELEASE_DIR"
  log "building release $RELEASE_ID"
  install -d -o root -g root -m 0755 "$RELEASE_DIR"
  git_src archive --format=tar "$RELEASE_ID" | tar -x -C "$RELEASE_DIR"
  # Create the venv in place: its scripts and editable install embed this path.
  python3 -m venv "$RELEASE_DIR/.venv"
  "$RELEASE_DIR/.venv/bin/python" -m pip install --quiet --disable-pip-version-check --upgrade pip
  "$RELEASE_DIR/.venv/bin/python" -m pip install --quiet --disable-pip-version-check -e "${RELEASE_DIR}[discord]"
  chown -R root:root "$RELEASE_DIR"
  chmod -R u+rwX,go+rX,go-w "$RELEASE_DIR"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$RELEASE_DIR/.install-complete"
  chmod 0644 "$RELEASE_DIR/.install-complete"
}

install_if_absent() {
  local src="$1" dest="$2" group="$3" mode="$4"
  [[ -e "$dest" ]] && return
  install -o root -g "$group" -m "$mode" "$src" "$dest"
  log "created $dest from template; edit it before enabling"
}

write_env_if_absent() {
  local dest="$1"; shift
  [[ -e "$dest" ]] && return
  local tmp
  tmp="$(mktemp)"
  printf '%s\n' "# Read by systemd as root; keep root:root 0600. Not shell code." "$@" > "$tmp"
  install -o root -g root -m 0600 "$tmp" "$dest"
  rm -f "$tmp"
  log "created $dest; replace placeholders"
}

install_configuration() {
  local ex="$RELEASE_DIR/examples/monitoring"
  install_if_absent "$ex/monitoring.example.json" "$ETC/monitoring.json" homelab-observe 0640
  install_if_absent "$ex/execution-policy.example.json" "$ETC/execution-policy.json" homelab-approve 0640
  install_if_absent "$ex/discord-identity.example.json" "$ETC/discord-identity.json" homelab-observe 0640
  write_env_if_absent "$ETC/monitor.env" \
    "PROXMOX_AUTHORIZATION=PVEAPIToken=observer@pve!monitor=REPLACE_SECRET" \
    "UNIFI_READ_API_KEY=REPLACE_SECRET" \
    "HA_AUTHORIZATION=Bearer REPLACE_SECRET"
  write_env_if_absent "$ETC/notify.env" \
    "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/REPLACE_ID/REPLACE_SECRET"
  write_env_if_absent "$ETC/worker.env" "# No credentials required."
  write_env_if_absent "$ETC/discord.env" "DISCORD_BOT_TOKEN=REPLACE_SECRET"
  write_env_if_absent "$ETC/executor.env" \
    "# Only if GitHub IssueOps is enabled; read-only token. Never give it to Hermes." \
    "#GITHUB_READ_TOKEN=REPLACE_READ_ONLY_REPO_TOKEN"
  local enabled
  enabled="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("enabled", False))' "$ETC/execution-policy.json")"
  [[ "$enabled" == "False" ]] || warn "execution policy is enabled; confirm it was approved through GitHub"
}

install_units() {
  log "installing systemd units (customize with 'systemctl edit UNIT', not by editing these files)"
  local unit
  for unit in homelab-monitor@.service homelab-discord.service homelab-executor.service; do
    install -o root -g root -m 0644 "$RELEASE_DIR/examples/monitoring/$unit" "$UNIT_DIR/$unit"
  done
  systemctl daemon-reload
}

validate_release() {
  log "validating configuration with release $RELEASE_ID as homelab-monitor"
  (cd / && runuser -u homelab-monitor -- "$RELEASE_DIR/.venv/bin/python" -m homelab_monitor \
    --config "$ETC/monitoring.json" validate) || die "configuration validation failed; current release left unchanged"
}

backup_state() {
  local stamp db out
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  for db in "$STATE/monitor.db" "$ACTION_STATE/actions.db"; do
    [[ -f "$db" ]] || continue
    out="$BACKUPS/$(basename "$db" .db)-$stamp-before-$RELEASE_ID.db"
    sqlite3 "$db" ".backup '$out'"
    chmod 0600 "$out"
    log "backed up $db to $out"
  done
}

switch_release() {
  if [[ -e "$PREFIX" && ! -L "$PREFIX" ]]; then
    die "$PREFIX exists and is not a symlink; move the manual install aside first"
  fi
  local current=""
  [[ -L "$PREFIX" ]] && current="$(readlink -f "$PREFIX")"
  if [[ "$current" == "$RELEASE_DIR" ]]; then
    log "release $RELEASE_ID already current"
    return
  fi
  [[ -n "$current" ]] && printf '%s\n' "$current" > "$RELEASES/.previous"
  ln -sfn "$RELEASE_DIR" "$PREFIX.new"
  mv -T "$PREFIX.new" "$PREFIX"
  log "switched $PREFIX -> $RELEASE_DIR"
  local unit
  for unit in "${ALL_UNITS[@]}"; do
    systemctl try-restart "$unit" || warn "restart of $unit failed; inspect journalctl -u $unit"
  done
}

prune_releases() {
  local current previous="" dir kept=0
  current="$(readlink -f "$PREFIX")"
  [[ -f "$RELEASES/.previous" ]] && previous="$(cat "$RELEASES/.previous")"
  while IFS= read -r dir; do
    [[ "$dir" == "$current" || "$dir" == "$previous" ]] && continue
    if [[ $kept -lt $KEEP ]]; then
      kept=$((kept + 1))
      continue
    fi
    log "pruning old release $dir"
    rm -rf "$dir"
  done < <(find "$RELEASES" -mindepth 1 -maxdepth 1 -type d ! -name '.*' -printf '%T@ %p\n' | sort -rn | cut -d' ' -f2-)
}

setup_ollama() {
  if ! command -v ollama >/dev/null; then
    log "installing Ollama with its official script (review: https://ollama.com/install.sh)"
    local script
    script="$(mktemp)"
    curl -fsSL --proto '=https' --tlsv1.2 https://ollama.com/install.sh -o "$script"
    sh "$script"
    rm -f "$script"
  fi
  install -d -o root -g root -m 0755 /etc/systemd/system/ollama.service.d
  cat > /etc/systemd/system/ollama.service.d/homelab.conf <<'EOF'
[Service]
# Loopback only, no cloud models; the worker independently verifies both.
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_NO_CLOUD=1"
# Bound memory and keep a shared desktop responsive during inference.
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_KEEP_ALIVE=5m"
CPUWeight=50
Nice=5
EOF
  chmod 0644 /etc/systemd/system/ollama.service.d/homelab.conf
  systemctl daemon-reload
  systemctl enable ollama.service
  systemctl restart ollama.service
  local i
  for i in $(seq 1 30); do
    curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1 && break
    [[ $i -eq 30 ]] && die "Ollama did not become ready on 127.0.0.1:11434"
    sleep 1
  done
  if [[ -z "$MODEL" ]]; then
    MODEL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("model", {}).get("name", ""))' "$ETC/monitoring.json")"
  fi
  if [[ -n "$MODEL" ]]; then
    log "pulling local model $MODEL"
    OLLAMA_HOST=127.0.0.1:11434 ollama pull "$MODEL"
  else
    warn "no model configured; pull one with: ollama pull MODEL"
  fi
}

disable_sleep() {
  log "masking ${SLEEP_TARGETS[*]} so the PC keeps monitoring while idle"
  systemctl mask "${SLEEP_TARGETS[@]}"
}

placeholder_files() {
  grep -lE 'REPLACE_|example\.internal|replace-with-' "$ETC/monitoring.json" "$ETC/monitor.env" "$ETC/notify.env" 2>/dev/null
}

enable_core() {
  local files
  if files="$(placeholder_files)"; then
    warn "not enabling; placeholders remain in: $(echo "$files" | tr '\n' ' ')"
    return 1
  fi
  log "enabling ${CORE_UNITS[*]}"
  systemctl enable --now "${CORE_UNITS[@]}"
}

check_os
install_packages
create_identities
create_directories
resolve_release
build_release
install_configuration
install_units
validate_release
backup_state
switch_release
prune_releases
if [[ $INSTALL_OLLAMA -eq 1 ]]; then setup_ollama; fi
if [[ $NO_SLEEP -eq 1 ]]; then disable_sleep; fi
status=0
if [[ $ENABLE -eq 1 ]]; then enable_core || status=1; fi

cat <<EOF

Installed release $RELEASE_ID at $PREFIX.
Next:
  1. Edit $ETC/monitoring.json and $ETC/{monitor,notify}.env (replace every placeholder).
  2. sudo $PREFIX/examples/monitoring/deploy/smoke-test.sh --pre-enable
  3. sudo $PREFIX/examples/monitoring/deploy/install.sh --source $SOURCE --ref $RELEASE_ID --enable
  4. sudo $PREFIX/examples/monitoring/deploy/smoke-test.sh --benchmark
The Discord approval bot and executor stay disabled; see examples/monitoring/DEPLOY.md.
EOF
exit "$status"
