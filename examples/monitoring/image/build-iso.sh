#!/usr/bin/env bash
# Build a homelab monitoring PC installer from a stock Ubuntu 24.04 Desktop ISO.
# Adds autoinstall.yaml and a pinned git bundle of this repository; the boot
# records are replayed unchanged. Runs on Linux or macOS with xorriso and git.
set -euo pipefail

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REF=HEAD
ISO=""
OUT=""

usage() {
  cat <<'EOF'
Usage: ./build-iso.sh --iso ubuntu-24.04.x-desktop-amd64.iso [options]

  --iso FILE      Stock Ubuntu Desktop 24.04 LTS ISO (required)
  --ref REF       Commit/tag/branch to embed (default: HEAD; must be committed)
  --source DIR    Repository checkout (default: this repository)
  --out FILE      Output ISO (default: homelab-monitor-<commit>.iso)
  -h, --help      Show this help

If SHA256SUMS from releases.ubuntu.com sits next to the ISO, it is verified.
Install xorriso with: apt install xorriso  |  brew install xorriso
EOF
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --iso) ISO="${2:?--iso needs a value}"; shift 2 ;;
    --ref) REF="${2:?--ref needs a value}"; shift 2 ;;
    --source) SOURCE="${2:?--source needs a value}"; shift 2 ;;
    --out) OUT="${2:?--out needs a value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

[[ -n "$ISO" ]] || { usage >&2; die "--iso is required"; }
[[ -f "$ISO" ]] || die "$ISO not found"
command -v xorriso >/dev/null || die "xorriso is required"
command -v git >/dev/null || die "git is required"

sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }

sums="$(dirname "$ISO")/SHA256SUMS"
if [[ -f "$sums" ]]; then
  expected="$(awk -v f="$(basename "$ISO")" '{n=$2; sub(/^\*/, "", n)} n == f {print $1}' "$sums")"
  [[ -n "$expected" ]] || die "$(basename "$ISO") is not listed in $sums"
  [[ "$(sha256 "$ISO")" == "$expected" ]] || die "checksum mismatch for $ISO"
  echo "==> verified $(basename "$ISO") against SHA256SUMS"
else
  echo "WARN: no SHA256SUMS beside the ISO; verify it yourself before use" >&2
fi

COMMIT="$(git -C "$SOURCE" rev-parse "${REF}^{commit}")" || die "cannot resolve $REF"
SHORT="${COMMIT:0:12}"
OUT="${OUT:-homelab-monitor-$SHORT.iso}"
[[ -e "$OUT" ]] && die "$OUT already exists"
if [[ -n "$(git -C "$SOURCE" status --porcelain --untracked-files=no)" ]]; then
  echo "WARN: uncommitted changes are NOT included; embedding commit $SHORT" >&2
fi

WORK="$(mktemp -d)"
TMP_REF="refs/heads/homelab-image-$$"
cleanup() { git -C "$SOURCE" update-ref -d "$TMP_REF" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT

mkdir -p "$WORK/homelab"
git -C "$SOURCE" update-ref "$TMP_REF" "$COMMIT"
git -C "$SOURCE" bundle create --quiet "$WORK/homelab/homelab-assistant-agent.bundle" "$TMP_REF"
git -C "$SOURCE" bundle verify --quiet "$WORK/homelab/homelab-assistant-agent.bundle"
printf '%s\n' "$COMMIT" > "$WORK/homelab/ref"
# Use the autoinstall file from the embedded commit, not the working tree.
git -C "$SOURCE" show "$COMMIT:examples/monitoring/image/autoinstall.yaml" > "$WORK/autoinstall.yaml"

xorriso -indev "$ISO" -outdev "$OUT" \
  -map "$WORK/autoinstall.yaml" /autoinstall.yaml \
  -map "$WORK/homelab" /homelab \
  -boot_image any replay

echo "==> wrote $OUT (commit $SHORT, sha256 $(sha256 "$OUT"))"
echo "Write it to a USB stick (balenaEtcher, 'dd', or Rufus in DD mode) and boot the PC from it."
