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
Create records when infrastructure is provisioned, update when IPs change, and clean up when decommissioned.

## API Reference

**Base URL:** `https://api.nextdns.io`

**Authentication:** `X-Api-Key` header. Configure credentials through a secure, user-managed mechanism; never retrieve, print, or commit secret values.

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

Mutating API calls (`POST`, `PATCH`, and `DELETE`) require an explicit user request for the specific change. Do not make DNS changes automatically as a side effect of provisioning, IP changes, or decommissioning. If the requested record or target profile is unclear, ask before writing.

## Common Operations

### Create a DNS Rewrite
```bash
curl -s -X POST "https://api.nextdns.io/profiles/${NEXTDNS_PROFILE_ID}/rewrites" \
  -H "X-Api-Key: ${NEXTDNS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"name": "host.example.com", "content": "192.0.2.10"}'
```

### List All Rewrites
```bash
curl -s "https://api.nextdns.io/profiles/${NEXTDNS_PROFILE_ID}/rewrites" \
  -H "X-Api-Key: ${NEXTDNS_API_KEY}" | python3 -m json.tool
```

### Delete a Rewrite
```bash
curl -s -X DELETE "https://api.nextdns.io/profiles/${NEXTDNS_PROFILE_ID}/rewrites/REWRITE_ID" \
  -H "X-Api-Key: ${NEXTDNS_API_KEY}"
```

## Integration with Infrastructure Provisioning

When new infrastructure is created (VMs, containers, services), DNS rewrites may be needed. Propose the record and wait for an explicit request before changing NextDNS:

1. **VM provisioned on Proxmox** → Create A record (hostname → static IP)
2. **Service deployed on Kubernetes** → Create A record or CNAME pointing to ingress
3. **Infrastructure decommissioned** → Delete corresponding DNS records
4. **IP address changes** → Delete old record, create new one (API has no PATCH for rewrites)

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
1. Use only an explicitly configured credential provider; never search for credentials
2. Read DNS conventions only from a local path the user explicitly identifies
3. List current rewrites when the user asks for an audit or change and read access is configured
4. Identify existing records for the requested hostnames
5. Make changes only when the user explicitly requests the specific change
6. Verify requested changes by re-listing rewrites

**Report Format:**
```
## DNS Changes Made

### Created
- hostname.subdomain.domain → 10.0.0.1 (ID: abc123)

### Deleted
- old-hostname.subdomain.domain (ID: xyz789)

### Existing (unchanged)
- other-host.subdomain.domain → 10.0.0.2
```

## Best Practices

- **Always use static IPs** for DNS rewrites (not DHCP addresses)
- **Follow user-provided subdomain conventions**; ask when they are needed but not supplied
- **Clean up old records** when decommissioning infrastructure
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
