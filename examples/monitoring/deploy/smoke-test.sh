#!/usr/bin/env bash
# Post-install verification for the homelab monitoring companion. Read-only,
# except --discord-test, which posts one message to the configured webhook.
set -euo pipefail

PREFIX=/opt/homelab-monitor
ETC=/etc/homelab-monitor
STATE=/var/lib/homelab-monitor
DB="$STATE/monitor.db"
OLLAMA=http://127.0.0.1:11434
CORE_UNITS=(homelab-monitor@monitor.service homelab-monitor@notify.service homelab-monitor@worker.service)

PRE_ENABLE=0
BENCHMARK=0
DISCORD_TEST=0
MAX_AGE=180

usage() {
  cat <<'EOF'
Usage: sudo ./smoke-test.sh [options]

  --pre-enable     Treat stopped core services/absent heartbeat as expected
  --benchmark      Time one short local-model generation (loads the model)
  --discord-test   Post one test message to DISCORD_WEBHOOK_URL from notify.env
  --max-age SEC    Heartbeat freshness limit (default: 180)
  -h, --help       Show this help
Exit status is non-zero if any check FAILs.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pre-enable) PRE_ENABLE=1; shift ;;
    --benchmark) BENCHMARK=1; shift ;;
    --discord-test) DISCORD_TEST=1; shift ;;
    --max-age) MAX_AGE="${2:?--max-age needs a value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ $EUID -eq 0 ]] || { echo "run as root (sudo)" >&2; exit 2; }
[[ "$MAX_AGE" =~ ^[0-9]+$ ]] || { echo "--max-age must be an integer" >&2; exit 2; }

PASS=0 WARNS=0 FAILS=0
pass() { PASS=$((PASS + 1)); printf 'PASS  %s\n' "$*"; }
warn() { WARNS=$((WARNS + 1)); printf 'WARN  %s\n' "$*"; }
fail() { FAILS=$((FAILS + 1)); printf 'FAIL  %s\n' "$*"; }
# Stopped/absent is expected before the operator enables services.
soft_fail() { if [[ $PRE_ENABLE -eq 1 ]]; then warn "$*"; else fail "$*"; fi; }

PY="$PREFIX/.venv/bin/python"
as_monitor() { (cd / && runuser -u homelab-monitor -- "$PY" -m homelab_monitor "$@"); }
mode_of() { stat -c '%U:%G %a' "$1"; }
env_value() { sed -n "s/^$2=//p" "$1" | tail -n 1; }

echo "== Installation"
if [[ -L "$PREFIX" && -f "$PREFIX/.install-complete" ]]; then
  pass "release $(basename "$(readlink -f "$PREFIX")") installed at $PREFIX"
else
  fail "$PREFIX is not a completed release symlink; run deploy/install.sh"
  echo; echo "Summary: $PASS passed, $WARNS warnings, $FAILS failed"; exit 1
fi
if writable="$(find "$(readlink -f "$PREFIX")" ! -type l \( ! -user root -o -perm /022 \) -print -quit)" && [[ -n "$writable" ]]; then
  fail "release contains files not root-owned or group/other-writable (e.g. $writable)"
else
  pass "release code is root-owned and read-only to service users"
fi
for id in homelab-monitor homelab-discord homelab-executor; do
  if id -u "$id" >/dev/null 2>&1; then pass "user $id exists"; else fail "user $id missing"; fi
done
if id -nG homelab-monitor | tr ' ' '\n' | grep -qx homelab-approve; then
  fail "homelab-monitor is in homelab-approve (must not reach the executor socket)"
fi

echo "== Configuration"
if out="$(as_monitor --config "$ETC/monitoring.json" validate 2>&1)"; then pass "$out"; else fail "validate: $out"; fi
for file in monitoring.json execution-policy.json discord-identity.json; do
  [[ -f "$ETC/$file" ]] || { fail "$ETC/$file missing"; continue; }
  perms="$(mode_of "$ETC/$file")"
  if [[ "$perms" == root:*" 640" ]]; then pass "$file is $perms"; else fail "$file is $perms (expected root:<group> 640)"; fi
done
for file in monitor.env notify.env worker.env discord.env executor.env; do
  [[ -f "$ETC/$file" ]] || { warn "$ETC/$file missing"; continue; }
  perms="$(mode_of "$ETC/$file")"
  if [[ "$perms" == "root:root 600" ]]; then pass "$file is root:root 600"; else fail "$file is $perms (expected root:root 600)"; fi
done
if placeholders="$(grep -lE 'REPLACE_|example\.internal|replace-with-' "$ETC/monitoring.json" "$ETC/monitor.env" "$ETC/notify.env" 2>/dev/null)"; then
  soft_fail "placeholders remain in: $(echo "$placeholders" | tr '\n' ' ')"
else
  pass "no placeholders in monitoring config or monitor/notify secrets"
fi
policy="$("$PY" -c 'import json,sys; p=json.load(open(sys.argv[1])); print(p.get("enabled", False), len(p.get("runbooks", {})))' "$ETC/execution-policy.json")"
if [[ "$policy" == "False 0" ]]; then
  pass "execution disabled with an empty runbook allowlist"
else
  warn "execution policy is '$policy' (enabled runbooks); confirm GitHub review, sudoers scope and $ETC/STOP procedure"
fi
perms="$(mode_of "$STATE")"
if [[ "$perms" == "homelab-monitor:homelab-observe 2750" ]]; then pass "state dir is $perms"; else fail "state dir is $perms (expected homelab-monitor:homelab-observe 2750)"; fi

echo "== Services"
for unit in "${CORE_UNITS[@]}"; do
  if systemctl is-active --quiet "$unit"; then pass "$unit active"; else soft_fail "$unit not active"; fi
done
for unit in homelab-discord.service homelab-executor.service; do
  if systemctl is-active --quiet "$unit"; then warn "$unit active; confirm it was deliberately enabled"; else pass "$unit inactive (default)"; fi
done
if [[ -f "$DB" ]]; then
  if out="$(as_monitor --db "$DB" heartbeat --max-age "$MAX_AGE" 2>&1)"; then pass "$out"; else soft_fail "heartbeat: $out"; fi
  if status="$(as_monitor --db "$DB" status 2>/dev/null)"; then
    firing="$(printf '%s' "$status" | "$PY" -c 'import json,sys
print(",".join(r["id"] for r in json.load(sys.stdin) if r.get("status") == "firing") or "0")' 2>/dev/null || echo "?")"
    if [[ "$firing" == "0" ]]; then pass "no firing checks"; else warn "firing checks: $firing (see: homelab_monitor status)"; fi
  fi
else
  soft_fail "no state database yet at $DB"
fi
if systemctl get-default | grep -q graphical; then
  if [[ "$(systemctl is-enabled suspend.target 2>/dev/null || true)" == "masked" ]]; then
    pass "desktop: suspend masked"
  else
    warn "desktop install can suspend when idle and stop monitoring; rerun install.sh with --no-sleep"
  fi
fi

echo "== Local model"
if curl -fsS --max-time 5 "$OLLAMA/api/version" >/dev/null 2>&1; then
  pass "Ollama answering on $OLLAMA"
  if systemctl show ollama.service -p Environment 2>/dev/null | grep -q 'OLLAMA_NO_CLOUD=1'; then
    pass "OLLAMA_NO_CLOUD=1 set on the Ollama service"
  else
    fail "OLLAMA_NO_CLOUD=1 not set on ollama.service (install.sh --install-ollama adds it)"
  fi
  if command -v ss >/dev/null; then
    if ss -Htln 'sport = :11434' | awk '{print $4}' | grep -vqE '^(127\.0\.0\.1|\[::1\]):11434$'; then
      fail "Ollama listens beyond loopback: $(ss -Htln 'sport = :11434' | awk '{print $4}' | tr '\n' ' ')"
    else
      pass "Ollama bound to loopback only"
    fi
  fi
  model="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("model", {}).get("name", ""))' "$ETC/monitoring.json")"
  if [[ -n "$model" ]]; then
    if curl -fsS --max-time 10 "$OLLAMA/api/tags" | "$PY" -c 'import json,sys; n=sys.argv[1]; m=[x["name"] for x in json.load(sys.stdin).get("models", [])]; sys.exit(0 if n in m or n + ":latest" in m else 1)' "$model"; then
      pass "model $model pulled"
    else
      fail "model $model not pulled (ollama pull $model)"
      BENCHMARK=0
    fi
  fi
  if [[ $BENCHMARK -eq 1 && -n "$model" ]]; then
    echo "   benchmarking $model (first run includes load time)..."
    body="$("$PY" -c 'import json,sys; print(json.dumps({"model": sys.argv[1], "stream": False, "format": "json",
      "options": {"num_ctx": 4096, "num_predict": 128, "temperature": 0},
      "prompt": "Return JSON with keys summary and next_read describing: node pve2 stopped answering API checks."}))' "$model")"
    if result="$(curl -fsS --max-time 300 "$OLLAMA/api/generate" -H 'Content-Type: application/json' -d "$body")"; then
      printf '%s' "$result" | "$PY" -c 'import json,sys
r=json.load(sys.stdin); ns=1e9
ev=r.get("eval_count",0); ed=r.get("eval_duration",0) or 1
print("   load %.1fs, prompt %.1fs, generate %d tokens in %.1fs (%.1f tok/s), total %.1fs" % (
  r.get("load_duration",0)/ns, r.get("prompt_eval_duration",0)/ns, ev, ed/ns, ev/(ed/ns), r.get("total_duration",0)/ns))
try: json.loads(r.get("response","")); print("   output was valid JSON")
except ValueError: print("   output was NOT valid JSON")'
      pass "benchmark completed; compare against the worker timeout in monitoring.json"
    else
      fail "benchmark request failed or exceeded 300s"
    fi
  fi
else
  warn "Ollama not reachable on $OLLAMA; alerts still work, diagnosis will not"
fi

if [[ $DISCORD_TEST -eq 1 ]]; then
  echo "== Discord"
  hook="$(env_value "$ETC/notify.env" DISCORD_WEBHOOK_URL)"
  if [[ -z "$hook" || "$hook" == *REPLACE_* ]]; then
    fail "DISCORD_WEBHOOK_URL not configured in notify.env"
  else
    payload="$("$PY" -c 'import json,socket; print(json.dumps({"content": "homelab-monitor smoke test from %s" % socket.gethostname(), "allowed_mentions": {"parse": []}}))')"
    # Keep the secret webhook URL off the process list by passing it via stdin config.
    if printf 'url = "%s"\n' "$hook" | curl -fsS --max-time 15 -o /dev/null -K - -H 'Content-Type: application/json' -d "$payload"; then
      pass "test message posted to Discord"
    else
      fail "Discord webhook post failed"
    fi
  fi
fi

echo
echo "Summary: $PASS passed, $WARNS warnings, $FAILS failed"
[[ $FAILS -eq 0 ]]
