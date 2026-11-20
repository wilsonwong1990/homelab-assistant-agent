---
name: nextdns
description: NextDNS profile management for homelab DNS rewrites, blocklists, and split-horizon DNS. Manages A records, CNAMEs, and DNS-based service discovery for internal infrastructure.
---

# NextDNS Homelab Skill

## My Focus
I help plan and manage DNS rewrites and profile configuration via the NextDNS API for your homelab. Provisioning infrastructure does not authorize creating or changing DNS records.

## What I Manage

**DNS Rewrites (A Records / CNAMEs)**
Internal hostname → IP mappings for homelab services. These are split-horizon records that resolve internally but not on the public internet.

**Profile Configuration**
Blocklists, security settings, and parental controls via the NextDNS API.

**DNS Lifecycle**
Plan records for new infrastructure, IP changes, and decommissioning. Make each change only when the user explicitly requests it.

## API Reference

**Base URL:** `https://api.nextdns.io`

**Authentication:** `X-Api-Key` header. Use only a secure credential provider or private curl config file that the user identifies; never search for, retrieve, print, or commit secret values. Keep the config outside the repository and restrict access (for example, mode `0600` on POSIX systems). Do not put API keys in command-line arguments. Use the HTTPS API endpoint and keep TLS certificate verification enabled.

**Key Endpoints:**
- `GET /profiles/:id/rewrites` — List all DNS rewrites
- `POST /profiles/:id/rewrites` — Create a rewrite (`{"name": "host.domain", "content": "ip-or-cname"}`)
- `DELETE /profiles/:id/rewrites/:rewrite_id` — Delete a rewrite
- `GET /profiles/:id` — Full profile config
- `PATCH /profiles/:id` — Update profile settings

**Rewrite Object:**
```json
{
  "id": "abc123",
  "name": "host.subdomain.example.com",
  "type": "A",
  "content": "192.0.2.10"
}
```

## Credentials & Configuration

**All credentials and personal configuration are stored locally, never in this repo.**

Store credentials and any environment-specific DNS conventions outside this plugin. Use only a configuration file or credential provider that the user identifies; do not search for private configuration or assume a path.

For the curl examples below, the user can set `NEXTDNS_CURL_CONFIG` to the path of a private curl config file they manage. Its contents should include the authentication header:

```text
header = "X-Api-Key: <your-api-key>"
```

Set `NEXTDNS_PROFILE_ID` to the profile the user identifies. Do not ask the user to paste a key into chat or inspect their private config.
The identified curl config must not disable TLS verification. The examples start with `-q` so curl ignores any default config that could disable verification.

Mutating API calls (`POST`, `PATCH`, and `DELETE`) require an explicit user request for the specific change. Do not make DNS changes automatically as a side effect of provisioning, IP changes, or decommissioning. If the requested record or target profile is unclear, ask before writing.

## Common Operations

### Create a DNS Rewrite
```bash
curl -q -s --config "$NEXTDNS_CURL_CONFIG" -X POST "https://api.nextdns.io/profiles/${NEXTDNS_PROFILE_ID}/rewrites" \
  -H "Content-Type: application/json" \
  -d '{"name": "host.example.com", "content": "192.0.2.10"}'
```

### List All Rewrites
```bash
curl -q -s --config "$NEXTDNS_CURL_CONFIG" "https://api.nextdns.io/profiles/${NEXTDNS_PROFILE_ID}/rewrites" | python3 -m json.tool
```

### Delete a Rewrite
```bash
curl -q -s --config "$NEXTDNS_CURL_CONFIG" -X DELETE "https://api.nextdns.io/profiles/${NEXTDNS_PROFILE_ID}/rewrites/REWRITE_ID"
```

## Integration with Infrastructure Provisioning

When infrastructure is provisioned, changed, or decommissioned, identify whether DNS records may need attention. Propose the exact record changes; do not make them unless the user explicitly requests those changes.

- A provisioned VM may need a hostname-to-static-IP record.
- A deployed service may need an A record or CNAME pointing to its ingress.
- Decommissioned infrastructure may have records to remove.
- An IP change may require replacing an old record because the API has no PATCH for rewrites.

## VLAN-to-Subdomain Mapping

If the user provides VLAN-to-subdomain conventions, follow them. Otherwise, present a generic pattern and ask for the user's conventions before recommending specific records:

| VLAN | Subdomain Pattern | Purpose |
|------|-------------------|---------|
| Management | `*.mgmt.<domain>` | Infrastructure management |
| Server | `*.server.<domain>` | Server infrastructure |
| Container | `*.k8s.<domain>` | Kubernetes / container workloads |
| IoT | `*.iot.<domain>` | IoT devices |

## Subagent Mode

When dispatched as a subagent by the orchestrator:

**Identity**: You are the DNS management specialist. Focus exclusively on NextDNS rewrite operations.

**Context Loading:**
Read private DNS conventions only from a local path the user explicitly identifies.

**Investigation Checklist:**
1. Use only an explicitly configured credential provider or a private curl config the user identifies; never search for credentials
2. Read DNS conventions only from a local path the user explicitly identifies
3. List current rewrites when the user asks for an audit or change and read access is configured
4. Identify existing records for the requested hostnames
5. Make changes only when the user explicitly requests the specific change
6. Verify requested changes by re-listing rewrites

**Report Format:**
```
## DNS Changes Made

### Created
- hostname.subdomain.domain → 192.0.2.10 (ID: abc123)

### Deleted
- old-hostname.subdomain.domain (ID: xyz789)

### Existing (unchanged)
- other-host.subdomain.domain → 192.0.2.20
```

## Best Practices

- **Always use static IPs** for DNS rewrites (not DHCP addresses)
- **Follow user-provided subdomain conventions**; ask when they are needed but not supplied
- **Propose cleanup of related records** when the user asks to decommission infrastructure
- **Verify after changes** by listing rewrites to confirm
- **Don't duplicate records** — check for existing entries before creating
- **Never commit credentials or personal domain/IP info** to the public repo

## When to Use This Skill

Engage me when:
- Provisioning new VMs, containers, or services that need DNS names
- Changing IP addresses of existing infrastructure
- Decommissioning infrastructure (cleanup DNS)
- Auditing current DNS rewrites against actual infrastructure
- Debugging DNS resolution issues for internal services
