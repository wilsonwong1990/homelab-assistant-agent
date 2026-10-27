# Local-first monitoring companion

This is an executable pilot, not a deployed monitoring installation. It adds
deterministic detection, persistent incident delivery, local-model analysis,
and hybrid approval to the existing assistant. It neither provisions accounts
nor grants permissions. Execution ships **disabled with an empty allowlist**.

## Architecture

```text
monitor -> SQLite incidents -> notify -> Discord webhook
                         \-> worker -> loopback Ollama -> diagnosis -> notify

Hermes / another MCP client -> read-only incident MCP bridge
Discord bot -> reads / exact approval -> Unix socket -> restricted executor
GitHub issue approval -> trusted local runner -> socket -> executor
GitOps PR -> human-authorized merge -> existing infrastructure reconciler
```

Monitor, notifier, model worker, Discord bot, and executor are separate
processes. Notifications do not call Ollama or Hermes. The background worker is
deliberately a stateless Ollama call, not an unattended Hermes tool loop:
it reads bounded canonical skill context and collected evidence, has no tools,
and returns validated text fields, never executable actions. Hermes remains
the replaceable interactive assistant runtime using the same skills and state.
Generic Hermes tool approvals do not authorize infrastructure changes.

### Supported scope

| Integration | Current checks |
|---|---|
| Proxmox | Explicit expected-online nodes from `/api2/json/nodes` |
| UniFi | Explicit expected-online device UUIDs via Network Integration API; bounded pagination; legacy `mac`/`state=1` response shape also supported |
| Home Assistant | API health and selected entity availability or exact expected states |
| HTTP | Successful HTTP response, including non-JSON health endpoints |

This is not yet a metrics/log anomaly engine, VM inventory monitor, battery
threshold evaluator, or universal Home Assistant controller. It does not infer
that unchanged sensors are stale. More APIs require an explicit collector and
tests; extend the check-kind registry rather than letting an LLM invent checks.
Do not install ELK just for this lightweight pilot. If you already have
Prometheus, Uptime Kuma, or another monitor, prefer integrating its health
endpoints/alerts over duplicating collection.

## Host and model

Linux, an SSD, and 16 GB RAM are sufficient for an initial lightweight pilot.
Start with a quantized 3B-4B model, 4096-token context, 512-token output, and one
worker. The example uses `qwen3:4b` as a candidate, not a tested quality or speed
guarantee. Evaluate the installed model's JSON fidelity and performance before
relying on analysis. A 7B-8B Q4 model needs measurement of headroom and latency.
Allow roughly 4-8 GB for the initial model process, 2-4 GB for companion services,
OS headroom, and 20-40 GB free disk for artifacts/state.

The RX 480 is not on Ollama's documented ROCm support list. CPU is the baseline;
Vulkan is an optional driver/backend experiment, not a prerequisite. Do not
assume the model will be fast because the host is called a Ryzen 7.

Only a literal loopback Ollama origin is accepted by the background worker.
No cloud inference provider, auxiliary model, or fallback exists in that worker.
Before sending evidence, the worker checks `/api/show` for local model metadata
and rejects cloud tags and aliases with `remote_host`/`remote_model`.
HTTP redirects and environment proxies are disabled. Set **`OLLAMA_NO_CLOUD=1`
on the Ollama service itself**, restart it, and verify its cloud-disabled log;
setting it only on the worker does not configure the server. Keep Ollama private
and use only locally downloaded models; enforce inference egress restrictions at the OS
level if you need assurance about Ollama or Hermes themselves. Discord/GitHub
are external services and receive the selected notification/proposal content.

## Install and configure

Use Python 3.9+ from this source checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[discord]'
cp examples/monitoring/monitoring.example.json monitoring.json
cp examples/monitoring/execution-policy.example.json execution-policy.json
cp examples/monitoring/discord-identity.example.json discord-identity.json
.venv/bin/python -m homelab_monitor --config monitoring.json validate
```

Replace placeholders before polling. Local configuration names and `state/`
are gitignored. The package is installed editable so `.github/skills/` remains
the source of truth. If deployed without this source layout, set `skill_root`
in `monitoring.json` to an absolute, read-only canonical `.github/skills` path.
Missing skills fail investigation explicitly; they do not stop alerts.

- Create source-enforced read-only accounts/tokens. A user named "observer" or
  an MCP `readOnlyHint` is not an access boundary.
- `headers_env` maps HTTP header names to environment variable names, not values.
  Supply complete header values through a secret store or systemd environment
  file. Do not place secrets in URLs, JSON config, commits, prompts, or logs.
- Use `PROXMOX_AUTHORIZATION=PVEAPIToken=USER@REALM!TOKEN=SECRET` with suitable
  Proxmox audit permissions. Explicitly exclude retired/intentionally offline
  nodes from `expected_online`.
- UniFi uses a read-only API key and a real site UUID. Integration device UUIDs
  are not MAC addresses. API/version permissions must be verified on your
  controller; merely having a working desktop MCP does not configure this host.
  The companion performs only GETs, does not log in with administrator passwords,
  and does not fall back to another authentication method.
- HA uses `HA_AUTHORIZATION=Bearer TOKEN`; select only needed entities. A
  long-lived token is not intrinsically read-only: enforce appropriate account
  permissions or put a constrained GET-only adapter in front of HA.
- Trust your private CA in the service OS. TLS verification is never disabled.
- `failures`/`recoveries` are consecutive samples (default 2). `depends_on`
  suppresses dependent incidents when a source fails. `maintenance_until` is a
  Unix timestamp. A suppressed check cannot authorize execution.
  A failing check is `pending` until its threshold, then `firing`; an untested
  maintenance/dependency-suppressed check is not reported healthy. Changes to a
  check's definition reset its incident sampling and invalidate old proposals.
- Configure Discord's incoming webhook as `DISCORD_WEBHOOK_URL` in the notifier
  environment only. The notifier disables mentions, retries failures with capped
  exponential backoff, and records successful delivery.

## Run and inspect

First populate state using only reads:

```bash
.venv/bin/python -m homelab_monitor --config monitoring.json poll
.venv/bin/python -m homelab_monitor status
.venv/bin/python -m homelab_monitor heartbeat --max-age 180
```

Run each long-lived component under a supervisor, in separate processes:

```bash
.venv/bin/python -m homelab_monitor monitor
.venv/bin/python -m homelab_monitor notify
.venv/bin/python -m homelab_monitor worker
```

`investigate` processes at most one queued incident; `request-read CHECK`
queues a manual read-only analysis, limited to 100 outstanding manual/firing
requests at admission and one manual request per check per minute. Do not run
multiple workers/notifiers: the supported deployment is one of each per state
database. The worker claims each incident once and records failures; a crash
leaves a `running` record for operator inspection, not an automatic replay.
The continuous worker drains the persisted firing-event backlog.

Notifier delivery is **at least once**, not exactly once: a crash/network loss
after Discord accepts a message but before SQLite records it can duplicate it.
Use incident IDs to identify duplicates. Resolved incidents generate recovery
messages with the same incident ID. Sent events/diagnoses expire after
`retention_days` (default 30); unsent alerts are retained rather than dropped.
Monitor disk usage if Discord remains unavailable. No claim is made that disk
usage stays bounded under an indefinite delivery outage.

The sample `homelab-monitor@.service` supports instances `monitor`, `notify`, and
`worker`. It assumes an approved deployment under `/opt/homelab-monitor`, a
`homelab-monitor` user, `homelab-observe` group, state directory
`/var/lib/homelab-monitor` owned by that user/group (mode 2750), and split
`/etc/homelab-monitor/{monitor,notify,worker}.env` files. Create these through
your reviewed infrastructure configuration, not by giving the agent root.
Worker environment files may be empty; install with restricted permissions.

SQLite DB/WAL/SHM must be group-readable for read-only consumers; existing files
from an older umask may need an operator permissions fix. Only monitor/notifier/
worker need write access to this directory. The Discord and Hermes users need
read access, not membership in the monitor's write identity.

Supervise each component and inspect its journal. The heartbeat command checks
the monitor's collection heartbeat only, not the gateway/notifier/model.
Use an observer on another host to check that heartbeat and delivery health.
The pilot does not provision this independent observer. A local host cannot
notify Discord during its own power or WAN outage without an independent path.

## Hermes and use from another system

`hermes-config.example.yaml` is a starting point for a **dedicated** local-only
profile, not an installer or a guarantee about every Hermes release. Verify
the provider keys, model routing (including auxiliary routes), tool selection,
fallbacks, hooks, optional external memory, and egress on the installed version.
Do not reuse an unrestricted personal profile for unattended monitoring.
Set all inference routes to your local endpoint or disable unused features.

Reference/link this checkout's canonical `.github/skills/` in the profile's
skills directory and apply `.github/skills/monitoring/SKILL.md` as the safety
policy alongside domain skills. Keep execution disabled in the Hermes identity:
no sudo, execution socket access, infrastructure write tokens, terminal-backed
remediation, or writable source MCPs. Permit only the read-only observer tools
for monitoring. The companion does not automatically copy Copilot's custom-agent
frontmatter, dispatch tools, or credentials into Hermes.

The bridge is standard newline-delimited stdio MCP:

```bash
.venv/bin/python -m homelab_monitor --db /var/lib/homelab-monitor/monitor.db mcp
```

It exposes only `homelab_status` and `homelab_incidents`, both against SQLite
opened with `mode=ro`. For a second workstation, either install this repository
with its own configuration/credentials or use a restricted SSH stdio command to
that bridge on the monitor host. Do not share the live SQLite WAL over NFS or
assume session memory is automatically shared. No public inbound endpoint is
required.

## Hybrid approval

| Lane | Allowed |
|---|---|
| Reads | No change approval; read-only source permissions still enforced |
| Discord | Exact low-risk runbooks/targets already approved in Git |
| GitHub | Configuration, deployments, permissions, policy/agent changes; separately authorized operational runbooks |
| Unknown | Deny; create/review a repository proposal before enabling anything |

Discord privacy reduces exposure but does not authenticate approval by itself.
Enable MFA on your account, protect the bot token, and minimize the permitted
blast radius. A compromised Discord owner account/bot could approve any action
in the Discord allowlist; it must not be able to change that allowlist.

### Enable only a deliberately selected runbook

The pilot implements one operation: **restart a fixed local systemd service**,
then verify `systemctl is-active`. It is not a remote SSH executor or a generic
Home Assistant write client. Network/firewall/host reboots, locks, doors, alarms,
and safety controls are not implemented. GitHub approval does not magically add
these operations. Reuse an existing GitOps reconciler for configuration rather
than granting this service the ability to apply arbitrary PR code.

Through a reviewed GitHub change, set `enabled: true` and add a runbook such as:

```json
{
  "restart-demo": {
    "operation": "restart_systemd",
    "lane": "discord",
    "low_risk": true,
    "unit": "noncritical-demo.service",
    "check": "demo-health",
    "version": "1",
    "impact": "Brief outage of this noncritical application only.",
    "recovery": "Inspect its journal; restore its reviewed configuration if needed."
  }
}
```

This object is the **contents of `runbooks`**, not a complete policy. Define the
corresponding HTTP check, ensure the service really is noncritical, review its
dependencies, and grant the executor's OS identity sudo rights for **only**
`/usr/bin/systemctl restart noncritical-demo.service`. Never grant a shell,
arbitrary `systemctl`, wildcard units, or policy/config write access. Keep the
checkout, installed Python environment, systemd unit definitions, policy, and
sudoers root/deployment-owned and read-only to all runtime identities.

Run `homelab-executor.service` as a separate user with its own private
`/var/lib/homelab-executor` directory (0700). Its Unix socket permits only the
trusted approval transports via `homelab-approve`; **do not** add monitor,
notifier, worker, Hermes, or arbitrary users to that group. Filesystem access
to this socket is a trust boundary: the executor trusts the Discord transport
to report authenticated Gateway actor IDs, not user-supplied JSON.
The executor uses narrowly scoped sudo, so its unit cannot use
`NoNewPrivileges=true`; the other services can and do.

Create `homelab-discord` as an independent user with read access to observer
state and socket access only. Supply `DISCORD_BOT_TOKEN` and enable the bot's
Message Content Intent. Use minimal guild/channel read/send permissions; no
Discord Administrator permission or member lookup is required. Configure
numeric IDs consistently in both identity and execution policy. The sample
`homelab-discord.service` is separate from the monitoring identity.

Commands in the configured private guild/channel (DMs are ignored):

```text
!status
!read demo-health
!propose restart-demo
!approve PROPOSAL_ID EXACT_SHA256
```

`!read` displays collected evidence and the most recent analysis, not a new
unbounded agent turn. `!propose` returns exact target, runbook version, incident,
impact/recovery, digest, and expiry. Proposals expire after five minutes. Only
the configured numeric user may approve in the configured guild/channel.
Generic "yes", reactions, webhooks, bot messages, and other channels do not count.
The executor rechecks identity, lane, current policy hash, incident identity,
check-definition hash, freshness (180 seconds), and current failing state before acting.

Each proposal is consumed durably before execution. Concurrent/replayed approval
cannot restart twice. Target cooldown is ten minutes from proposal creation.
`executing`/`unknown` outcomes block further actions on that unit until an
operator inspects actual state and reconciles the audit record. Never delete
audit history to blindly retry. Application recovery is confirmed by subsequent
monitoring, not solely by `systemctl` success.

Touch `/etc/homelab-monitor/STOP` through an authorized operator/deployment to
block new executions immediately. It cannot interrupt an already-started action.
Policy/audit/identity validation failures deny execution. A policy edit
invalidates outstanding approvals. Limit action audit/proposal storage through
an operator-managed archival procedure; execution history is not auto-deleted.

### GitHub IssueOps and GitOps

For a supported operational runbook that requires GitHub authorization, use
`lane: "github"` instead. Set the exact owning `owner/repo` and numeric human
GitHub IDs in the policy. Provide `GITHUB_READ_TOKEN` **only** to the executor,
with read permissions sufficient to retrieve issues/comments and verify current
repository collaborator permissions. It never needs merge or repository-write
rights. This pilot supports github.com, not GitHub Enterprise Server.

Create an issue in that repository, then use:

```text
!propose RUNBOOK ISSUE_NUMBER
```

Publish/review the full immutable proposal in the issue, then comment from your
authenticated account (GitHub Mobile is suitable):

```text
approve PROPOSAL_ID EXACT_SHA256
```

The trusted local relay invokes:

```bash
.venv/bin/python -m homelab_monitor approve-github PROPOSAL_ID EXACT_SHA256 COMMENT_ID
```

`issueops-workflow.example.yml` is an **inactive example**, to be installed via a
reviewed PR in the owning infrastructure repository. It requires a dedicated
LAN-connected `homelab-issueops` runner with socket access, not arbitrary job
execution access. Restrict its runner group/repository workflows; never run
untrusted PR jobs on that runner. It checks out no issue/PR-supplied code and
passes only parsed references to the installed client.

The executor independently fetches the comment through GitHub's API, verifies
the exact repository/issue, unedited comment, human numeric ID, current
write/admin permission, proposal hash, and current local state. A deleted/edited
comment, closed issue, unauthorized actor, or unavailable GitHub API denies the
action. Do not retry an uncertain execution by posting another approval.
The relay's result appears in Actions; the executor retains the durable audit.
The pilot does not post results back to GitHub automatically.

Declarative GitOps uses your existing protected PR/merge/reconciler workflow.
This project supplies the boundary and guidance, not a universal reconciler.
Choose protection rules supported by your repository/plan, account for a sole
owner's inability to approve their own PR, and never let the proposal identity
approve/merge or modify its own execution policy. Proposal publication is manual
in this pilot; autonomous issue/PR creation needs separately scoped authorization.
If GitHub is down, GitHub-required actions wait. Previously approved low-risk
runbooks can still use Discord with valid local policy/audit; no fallback expands
the Discord lane.

## Validation and operations

```bash
python3 -m unittest discover -s tests -v
python3 -m homelab_monitor --config examples/monitoring/monitoring.example.json validate
```

Tests use local HTTP fixtures and mocked external transports/side effects;
they never restart real services or contact Discord/GitHub. Before deployment,
verify actual API permissions/TLS, model memory/latency/quality on the Ryzen host,
Discord delivery and identity restrictions, service recovery, restart persistence,
GitHub Mobile approval/relay, kill switch, and an independent heartbeat observer.
Do not interpret fixture coverage as proof of hardware or live integration
compatibility.

Back up reviewed configuration separately from secrets and use SQLite's online
backup API (or stop all writers before copying DB/WAL). Inspect `checks`,
`events`, `investigations`, and executor `actions` for incident/action history.
Use bounded journald retention, source credential rotation, model service
supervision, and tested restoration. Adding a new integration or runbook requires
a reviewed configuration/code change and representative failure-path tests.
