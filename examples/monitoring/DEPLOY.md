# Deploying the monitoring companion

This runbook turns a spare PC (here: Ryzen 7, 16 GB RAM, RX 480) into an
always-on monitor. You can still use it as a desktop. It complements the
[operator guide](README.md), which explains the design, permissions and approval
model. Nothing here enables remediation: execution stays disabled until you
approve a runbook through GitHub.

## Choose the OS

| Use | Recommendation |
|---|---|
| **Monitor + occasional desktop PC** | **Ubuntu Desktop 24.04 LTS, minimal install** |
| Headless monitor only | Ubuntu Server 24.04 LTS (or Debian 13) |
| Lighter desktop | Xubuntu/Kubuntu 24.04, Debian 13 with Xfce/KDE (manual install path) |

Why Ubuntu 24.04 LTS:

- It has support until 2029, and Ollama's Linux installer targets it directly.
- The RX 480 runs well on the in-kernel `amdgpu` driver and Mesa with no
  proprietary driver. Mesa's Vulkan driver is also what Ollama's experimental
  Vulkan backend would use. ROCm does not support the RX 480, so CPU inference
  is the baseline.
- Its Python (3.12) is covered by this project's CI.
- Ubuntu 26.04 LTS is accepted by these scripts but untested; consider it
  after its first point release if you want a newer kernel and Mesa for Vulkan
  experiments. CI covers Python 3.9 and 3.12 and installs on Ubuntu 24.04.
- Avoid rolling-release distros here. An always-on monitor benefits from boring
  updates.

Placement matters more than distro: run the monitor **outside** the Proxmox
cluster it watches. A monitor running on that cluster goes down with it and
can't send the alert.

### Desktop considerations

- The services are systemd *system* units, so they run without anyone logged in.
  Logging out or switching users doesn't stop monitoring.
- The GNOME session uses about 1.5-3 GB of RAM. With the 4-8 GB the model needs,
  16 GB still fits, but avoid also running heavy apps or games while a diagnosis
  runs.
- `install.sh --install-ollama` gives Ollama a lower CPU priority and loads one
  model at a time. It also unloads the model after 5 idle minutes, which frees
  RAM for desktop use.
- **Suspend stops monitoring.** `--no-sleep` (applied automatically by the
  image) masks suspend/hibernate. Screen blanking and locking still work.
- Shutting the PC down also stops alerts. Configure an external heartbeat
  observer (see [README](README.md#run-and-inspect)) if that matters.
- The monitor itself has no GUI. Discord is the alert/approval UI, and
  `homelab_monitor status` or Hermes provide manual inspection.

## Option A: build an installer image (recommended for a fresh PC)

`image/build-iso.sh` repacks the **stock** Ubuntu Desktop 24.04 ISO with:

- `autoinstall.yaml`: minimal desktop, security updates, git/python/sqlite.
  Language, keyboard, network, **disk** and **user account** stay interactive.
  The image therefore contains no password and cannot erase a disk without
  your confirmation.
- A git bundle pinned to one commit of this repository. You install exactly
  the code you reviewed.
- A first-boot unit that runs `deploy/install.sh --install-ollama --no-sleep`
  once the network is up. It retries every 2 minutes until it succeeds.

No secrets or private infrastructure details are placed in the image.

```bash
# On any Linux/macOS machine with git and xorriso (apt/brew install xorriso)
curl -LO https://releases.ubuntu.com/24.04/ubuntu-24.04.3-desktop-amd64.iso   # use the current point release
curl -LO https://releases.ubuntu.com/24.04/SHA256SUMS
examples/monitoring/image/build-iso.sh --iso ubuntu-24.04.3-desktop-amd64.iso --ref main
```

Write the resulting `homelab-monitor-<commit>.iso` to a USB stick with
balenaEtcher, `dd`, or Rufus in DD mode. Boot the PC from it and answer the
interactive screens. If the installer asks you to confirm the automated
install, accept it. After reboot, log in and follow the first-boot progress:

```bash
journalctl -fu homelab-firstboot.service   # apt, PyPI, Ollama and the model download
```

Then continue at [Configure](#configure).

## Option B: install on an existing Ubuntu/Debian system

```bash
sudo apt install -y git
git clone https://github.com/wilsonwong1990/homelab-assistant-agent.git
cd homelab-assistant-agent
sudo examples/monitoring/deploy/install.sh --install-ollama --no-sleep   # omit --no-sleep on a server
```

`install.sh` is idempotent and safe to rerun. It:

1. Installs `python3`, `python3-venv`, `git`, `curl` and `sqlite3`.
2. Creates `homelab-monitor`, `homelab-discord` and `homelab-executor` system
   users and the `homelab-observe`/`homelab-approve` groups.
3. Builds `/opt/homelab-monitor-releases/<commit>` with its own virtualenv,
   root-owned and read-only to services. It then points `/opt/homelab-monitor`
   at that release.
4. Creates `/etc/homelab-monitor` configuration and split `*.env` secret files
   from templates, **only if absent** (root-only `0600` env files, which systemd
   reads as root).
5. Installs the systemd units without enabling them, validates the
   configuration, and backs up existing state databases before switching.
6. With `--install-ollama`: installs Ollama, binds it to `127.0.0.1`, sets
   `OLLAMA_NO_CLOUD=1`, and pulls the model named in `monitoring.json`.

It never writes sudoers, enables the executor or Discord approval bot, or
overwrites your configuration.

## Configure

```bash
sudoedit /etc/homelab-monitor/monitoring.json   # checks, expected nodes/devices, model
sudoedit /etc/homelab-monitor/monitor.env       # PROXMOX_AUTHORIZATION, UNIFI_READ_API_KEY, HA_AUTHORIZATION
sudoedit /etc/homelab-monitor/notify.env        # DISCORD_WEBHOOK_URL
```

Use read-only tokens as described in the [README](README.md#install-and-configure).
If your Proxmox/UniFi/HA certificates come from a private CA, add it to the OS
trust store: copy it to `/usr/local/share/ca-certificates/` and run
`update-ca-certificates`.

## Verify and enable

```bash
S=/opt/homelab-monitor/examples/monitoring/deploy
sudo $S/smoke-test.sh --pre-enable --discord-test   # config, permissions, Ollama, one Discord test post
sudo $S/install.sh --source /opt/homelab-monitor-src --enable   # Option B: --source <your clone>
sleep 180
sudo $S/smoke-test.sh --benchmark                   # services, heartbeat, firing checks, model speed
```

`--enable` refuses to start services while placeholders remain. `--benchmark`
prints load time, tokens/second and whether the output was valid JSON. If the
total exceeds about 60% of `model.timeout`, choose a smaller model or raise the
timeout (maximum 300 s).

### Optional: try Vulkan on the RX 480

Experimental. Measure with `--benchmark` before and after, and revert if output
quality or stability suffers.

```bash
sudo apt install -y mesa-vulkan-drivers vulkan-tools && vulkaninfo --summary
sudo systemctl edit ollama.service      # add: [Service]  Environment="OLLAMA_VULKAN=1"
sudo systemctl restart ollama && journalctl -u ollama -b | grep -i -E 'vulkan|gpu'
```

The RX 480's 4 or 8 GB of VRAM limits offload. With 4 GB, much of a 4B model
may still run on CPU.

## Upgrade

```bash
cd /opt/homelab-monitor-src   # or your clone
sudo git fetch origin && sudo git checkout --detach origin/main   # review the diff first
sudo /opt/homelab-monitor/examples/monitoring/deploy/install.sh --source "$PWD"
sudo /opt/homelab-monitor/examples/monitoring/deploy/smoke-test.sh
```

Each commit becomes a new release directory. The configuration is validated
with the new code *before* switching, and the state databases are backed up to
`/var/backups/homelab-monitor/`. Running services are restarted after the
switch. The current release, the previous one and three older ones are kept.

## Roll back

```bash
D=/opt/homelab-monitor/examples/monitoring/deploy
sudo $D/rollback.sh --list
sudo $D/rollback.sh              # previous release
sudo $D/rollback.sh 1a2b3c4d5e6f # a specific release
sudo $D/smoke-test.sh
```

Rollback switches code and unit files only; configuration and secrets are
unchanged. If a newer release migrated the database and the older one fails to
read it, restore the matching backup while services are stopped:

```bash
sudo systemctl stop 'homelab-monitor@*'
sudo install -o homelab-monitor -g homelab-observe -m 0640 \
  /var/backups/homelab-monitor/monitor-<stamp>-before-<release>.db /var/lib/homelab-monitor/monitor.db
sudo rm -f /var/lib/homelab-monitor/monitor.db-wal /var/lib/homelab-monitor/monitor.db-shm
sudo systemctl start homelab-monitor@monitor homelab-monitor@notify homelab-monitor@worker
```

Incidents recorded after that backup are lost.

## Later: approvals and Hermes

Keep these off until the core monitor has run cleanly for a while:

- **Discord approval bot / executor**: follow
  [Hybrid approval](README.md#hybrid-approval). It needs a reviewed policy
  change, an exact sudoers entry and `systemctl enable --now homelab-executor
  homelab-discord`.
- **Hermes**: follow [Hermes and use from another system](README.md#hermes-and-use-from-another-system).
  The desktop session is a convenient place to run it interactively.

## Uninstall

```bash
sudo systemctl disable --now 'homelab-monitor@*' homelab-discord homelab-executor homelab-firstboot 2>/dev/null
sudo rm -f /etc/systemd/system/homelab-{monitor@,discord,executor,firstboot}.service && sudo systemctl daemon-reload
sudo rm -rf /opt/homelab-monitor /opt/homelab-monitor-releases /opt/homelab-monitor-src
# Configuration, secrets, state and backups are kept until you delete them deliberately:
#   /etc/homelab-monitor /var/lib/homelab-monitor /var/lib/homelab-executor /var/backups/homelab-monitor
sudo systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target
```
