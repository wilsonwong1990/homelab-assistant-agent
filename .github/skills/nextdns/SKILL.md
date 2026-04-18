---
name: nextdns
description: NextDNS profile management for homelab DNS rewrites, blocklists, and split-horizon DNS. Manages A records, CNAMEs, and DNS-based service discovery for internal infrastructure.
---

# NextDNS Homelab Skill

## My Focus
I manage DNS rewrites and profile configuration via the NextDNS API for your homelab. When new infrastructure is provisioned (VMs, containers, services), I create the corresponding DNS records automatically.

## What I Manage

**DNS Rewrites (A Records / CNAMEs)**
Internal hostname → IP mappings for homelab services. These are split-horizon records that resolve internally but not on the public internet.

**Profile Configuration**
Blocklists, security settings, and parental controls via the NextDNS API.

**DNS Lifecycle**
Create records when infrastructure is provisioned, update when IPs change, and clean up when decommissioned.

## API Reference

**Base URL:** `https://api.nextdns.io`

**Authentication:** `X-Api-Key` header with API key stored in macOS Keychain.

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
  "content": "10.0.0.1"
}
```

## Credentials & Configuration

**All credentials and personal configuration are stored locally, never in this repo.**

**Credentials (macOS Keychain):**
- Profile ID: `security find-generic-password -a "nextdns" -s "nextdns-profile-id" -w`
- API Key: `security find-generic-password -a "nextdns" -s "nextdns-api" -w`

**Personal Configuration (private repo):**
- Location defined by `NEXTDNS_DNS_CONFIG` in `.env` (see `.env.example`)
- Default: `homelab-automation/nextdns/dns-config.md`
- Contains VLAN-to-subdomain mapping, domain structure, and environment-specific details
- This file lives in a private repo; the path is configured per-environment

**Existing Automation (in homelab-automation repo):**
- `nextdns/backup_rewrites.py` — Backs up rewrites to JSON on a schedule
- `nextdns/health_check.py` — Periodic API health monitoring
- `reports/nextdns_rewrites.json` — Latest backup of all rewrites

## Common Operations

### Create a DNS Rewrite
```bash
API_KEY=$(security find-generic-password -a "nextdns" -s "nextdns-api" -w)
PROFILE=$(security find-generic-password -a "nextdns" -s "nextdns-profile-id" -w)
curl -s -X POST "https://api.nextdns.io/profiles/${PROFILE}/rewrites" \
  -H "X-Api-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"name": "hostname.example.com", "content": "10.0.0.1"}'
```

### List All Rewrites
```bash
API_KEY=$(security find-generic-password -a "nextdns" -s "nextdns-api" -w)
PROFILE=$(security find-generic-password -a "nextdns" -s "nextdns-profile-id" -w)
curl -s "https://api.nextdns.io/profiles/${PROFILE}/rewrites" \
  -H "X-Api-Key: ${API_KEY}" | python3 -m json.tool
```

### Delete a Rewrite
```bash
API_KEY=$(security find-generic-password -a "nextdns" -s "nextdns-api" -w)
PROFILE=$(security find-generic-password -a "nextdns" -s "nextdns-profile-id" -w)
curl -s -X DELETE "https://api.nextdns.io/profiles/${PROFILE}/rewrites/REWRITE_ID" \
  -H "X-Api-Key: ${API_KEY}"
```

## Integration with Infrastructure Provisioning

When new infrastructure is created (VMs, containers, services), DNS rewrites should be created as part of the provisioning workflow:

1. **VM provisioned on Proxmox** → Create A record (hostname → static IP)
2. **Service deployed on Kubernetes** → Create A record or CNAME pointing to ingress
3. **Infrastructure decommissioned** → Delete corresponding DNS records
4. **IP address changes** → Delete old record, create new one (API has no PATCH for rewrites)

## VLAN-to-Subdomain Mapping

Refer to `config.private.md` for the user's specific VLAN-to-subdomain conventions. The general pattern is:

| VLAN | Subdomain Pattern | Purpose |
|------|-------------------|---------|
| Management | `*.mgmt.<domain>` | Infrastructure management |
| Server | `*.server.<domain>` | Server infrastructure |
| Container | `*.k8s.<domain>` | Kubernetes / container workloads |
| IoT | `*.iot.<domain>` | IoT devices |

## Subagent Mode

When dispatched as a subagent by the orchestrator:

**Identity**: You are the DNS management specialist. Focus exclusively on NextDNS rewrite operations.

**Credential Retrieval:**
Always retrieve credentials from macOS Keychain:
```bash
API_KEY=$(security find-generic-password -a "nextdns" -s "nextdns-api" -w)
PROFILE=$(security find-generic-password -a "nextdns" -s "nextdns-profile-id" -w)
```

**Context Loading:**
Read the DNS config file (path from `NEXTDNS_DNS_CONFIG` in `.env`, or find it at `homelab-automation/nextdns/dns-config.md`) for domain structure and VLAN mapping before creating records.

**Investigation Checklist:**
1. Retrieve credentials from Keychain
2. Read config.private.md for domain conventions
3. List current rewrites: `GET /profiles/${PROFILE}/rewrites`
4. Identify existing records for the target domain/hostnames
5. Create/update/delete records as requested
6. Verify changes by re-listing rewrites

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
- **Follow the subdomain convention** from the DNS config file (see `.env` for path)
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
