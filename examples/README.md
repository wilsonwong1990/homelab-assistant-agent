# Homelab Assistant Agent - Usage Examples

This directory contains practical examples of how to interact with the Homelab Assistant Agent.

## Quick Start Examples

### Example 1: Setting Up K3s on Proxmox

**Prompt to Agent:**
```
I have 3 Proxmox VMs ready (2GB RAM each, 2 vCPUs). 
Help me install a K3s cluster with one control plane and two worker nodes.
```

**What the Agent Will Help With:**
- Installation commands for K3s on each node
- Network configuration between nodes
- Token generation and node joining
- Basic kubectl setup
- Storage class configuration
- Recommendations on resource allocation for homelab scale

---

### Example 2: Configuring Unifi VLANs

**Prompt to Agent:**
```
I want to segment my homelab network into 3 VLANs:
- VLAN 10: Management (Proxmox, switches, APs)
- VLAN 20: Services (k8s, containers, services)
- VLAN 30: IoT devices

How do I configure this in my Unifi controller?
```

**What the Agent Will Help With:**
- Creating VLANs in Unifi controller
- Port profile configuration
- Inter-VLAN routing rules
- Firewall rules for homelab security
- DHCP server setup per VLAN
- Testing connectivity between VLANs

---

### Example 3: Proxmox Backup Strategy

**Prompt to Agent:**
```
What's a good backup strategy for my Proxmox homelab with 
5 VMs and 3 LXC containers? I have a NAS with 4TB available.
```

**What the Agent Will Help With:**
- PBS (Proxmox Backup Server) vs vzdump comparison
- Backup scheduling recommendations
- Storage configuration for NFS/CIFS backup target
- Retention policies appropriate for homelab
- Testing restore procedures
- Backup verification steps

---

### Example 4: Documentation and Issue Tracking

**Prompt to Agent:**
```
I just finished setting up my k3s cluster. Document what I did 
and create an issue tracking this work.
```

**What the Agent Will Help With:**
- Creating structured documentation
- Checking repolist.md for appropriate repository
- Creating a GitHub issue with details
- Linking related configurations
- Adding to knowledge base

---

## Advanced Examples

### Example 5: GitOps with ArgoCD

**Prompt to Agent:**
```
Walk me through setting up ArgoCD on my k3s cluster for 
managing my homelab applications. I want to sync from a 
private GitHub repository.
```

---

### Example 6: Firewall Configuration

**Prompt to Agent:**
```
I'm running pfSense. Help me configure:
- Port forwarding for my web services
- WireGuard VPN for remote access
- Rules to block IoT devices from accessing my management VLAN
```

---

## Tips for Best Results

1. **Provide Context**: Tell the agent about your current setup
2. **Be Specific**: Mention hardware, software versions, and constraints
3. **Ask Follow-ups**: The agent can iterate and refine solutions
4. **Request Explanations**: Ask "why" to learn best practices
5. **Mention Trade-offs**: The agent will explain homelab vs production differences

## Example Conversation Flow

```
You: I want to deploy a media server on my k3s cluster

Agent: [Provides options like Plex, Jellyfin, recommendations for homelab]

You: Let's go with Jellyfin. I have NFS storage available.

Agent: [Provides Kubernetes manifests, PVC configuration, service setup]

You: Should I use an ingress or NodePort?

Agent: [Explains both options, recommends based on homelab context]
```

## Recording Your Work

The agent can help document changes by:
- Creating structured documentation files
- Logging issues in appropriate repositories (via repolist.md)
- Generating runbooks for future reference
- Linking related configurations

Simply ask: "Document this configuration" or "Create an issue for this work"
