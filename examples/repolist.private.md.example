# Sample Homelab Repository Configuration

This example shows how to structure your `repolist.md` for a typical homelab setup.

## My Homelab Infrastructure

### homelab-k3s-gitops
- **URL**: `https://github.com/myusername/homelab-k3s-gitops`
- **Purpose**: GitOps repository for K3s cluster applications and configurations
- **Primary Technologies**: K3s, ArgoCD, Helm, Kustomize
- **Issue Tracking**: Yes - for application deployments and cluster changes
- **Dependencies**: homelab-terraform (provisions the VMs)
- **Notes**: Main GitOps repo, all apps deployed through ArgoCD

### homelab-terraform
- **URL**: `https://github.com/myusername/homelab-terraform`
- **Purpose**: Infrastructure as Code for Proxmox VM provisioning
- **Primary Technologies**: Terraform, Proxmox, Cloud-init
- **Issue Tracking**: Yes - for infrastructure changes
- **Dependencies**: None
- **Notes**: Provisions VMs for k3s cluster nodes

### homelab-ansible
- **URL**: `https://github.com/myusername/homelab-ansible`
- **Purpose**: Configuration management and automation
- **Primary Technologies**: Ansible, Python
- **Issue Tracking**: Yes - for automation improvements
- **Dependencies**: homelab-terraform (configures provisioned VMs)
- **Notes**: Handles OS configuration, package installation, user setup

### network-configs
- **URL**: `https://github.com/myusername/network-configs`
- **Purpose**: Network configuration backups and documentation
- **Primary Technologies**: pfSense, Unifi, VLANs
- **Issue Tracking**: Yes - for network changes
- **Dependencies**: None
- **Notes**: Contains firewall rules, VLAN configs, backup scripts

### homelab-docs
- **URL**: `https://github.com/myusername/homelab-docs`
- **Purpose**: Central documentation hub
- **Primary Technologies**: Markdown, MkDocs
- **Issue Tracking**: Yes - for documentation tasks
- **Dependencies**: All repositories
- **Notes**: Architecture diagrams, runbooks, troubleshooting guides

### monitoring-stack
- **URL**: `https://github.com/myusername/monitoring-stack`
- **Purpose**: Prometheus, Grafana, Loki stack configurations
- **Primary Technologies**: Prometheus, Grafana, Loki, AlertManager
- **Issue Tracking**: Yes - for monitoring improvements
- **Dependencies**: homelab-k3s-gitops (deployed via ArgoCD)
- **Notes**: Monitoring dashboards and alert rules

## How This Setup Works Together

1. **homelab-terraform** creates VMs on Proxmox
2. **homelab-ansible** configures those VMs
3. **homelab-k3s-gitops** manages applications via ArgoCD
4. **network-configs** maintains network infrastructure
5. **homelab-docs** documents everything
6. **monitoring-stack** keeps track of it all

## Agent Usage

When working with this setup, the homelab assistant agent will:
- Reference the appropriate repository for each type of work
- Create issues in the relevant repo
- Cross-link related changes
- Maintain documentation across repositories
