# Homelab Repository List

This file tracks repositories that the homelab assistant agent should be aware of for context and issue tracking. Each repository should document its purpose and how it fits into the overall homelab infrastructure.

## Repository Format

For each repository, include:
- **Repository URL/Path**: Full GitHub URL or relative path
- **Purpose**: What this repository contains/manages
- **Primary Technologies**: Key tech stack (k8s, Proxmox, etc.)
- **Issue Tracking**: Whether issues should be logged here
- **Dependencies**: Other repos this depends on or relates to

---

## Core Infrastructure Repositories

### homelab-assistant-agent
- **URL**: `https://github.com/wilsonwong1990/homelab-assistant-agent`
- **Purpose**: GitHub Copilot Agent configuration for homelab assistance
- **Primary Technologies**: GitHub Copilot, Agent configuration
- **Issue Tracking**: Yes - for agent improvements and feature requests
- **Dependencies**: None
- **Notes**: This is the agent definition repository

---

## Example Repository Entries

Below are example templates for common homelab repository types. Replace these with your actual repositories as you add them.

### Kubernetes/K3s Configuration
- **URL**: `https://github.com/YOUR_USERNAME/k3s-homelab` (example)
- **Purpose**: K3s cluster configuration and manifests
- **Primary Technologies**: K3s, Kubernetes, Helm, ArgoCD
- **Issue Tracking**: Yes - for cluster issues and enhancements
- **Dependencies**: None
- **Notes**: GitOps repository for cluster management

### Proxmox Automation
- **URL**: `https://github.com/YOUR_USERNAME/proxmox-automation` (example)
- **Purpose**: Proxmox VM/CT templates and automation scripts
- **Primary Technologies**: Proxmox, Terraform, Ansible
- **Issue Tracking**: Yes - for automation improvements
- **Dependencies**: None
- **Notes**: Infrastructure as Code for VM provisioning

### Network Configuration
- **URL**: `https://github.com/YOUR_USERNAME/network-config` (example)
- **Purpose**: Firewall rules, Unifi configuration, VLANs
- **Primary Technologies**: pfSense/OPNsense, Unifi, VLANs
- **Issue Tracking**: Yes - for network changes
- **Dependencies**: None
- **Notes**: Network documentation and configuration backups

### Homelab Documentation
- **URL**: `https://github.com/YOUR_USERNAME/homelab-docs` (example)
- **Purpose**: General homelab documentation and runbooks
- **Primary Technologies**: Markdown, Documentation
- **Issue Tracking**: Yes - for documentation tasks
- **Dependencies**: All other repositories
- **Notes**: Central documentation hub

---

## How to Use This File

### For the Agent
The homelab assistant agent reads this file to:
1. Understand which repositories are part of your homelab ecosystem
2. Determine where to log issues for specific work
3. Cross-reference configurations and dependencies
4. Maintain context across multiple repositories

### For You
Update this file when you:
1. Create a new repository for homelab work
2. Restructure your repository organization
3. Deprecate or archive old repositories
4. Change the purpose or scope of existing repositories

### Recording Work
When the agent completes significant work, it should:
1. Identify the appropriate repository from this list
2. Create a GitHub issue documenting the work
3. Link related issues across repositories when applicable
4. Update documentation in the relevant repository

---

## Adding New Repositories

To add a new repository to this list:

1. Add an entry following the format above
2. Commit and push the change to this repository
3. The agent will be aware of the new repository on next interaction

Example:
```markdown
### My New Homelab Project
- **URL**: `https://github.com/YOUR_USERNAME/project-name`
- **Purpose**: Brief description of what this manages
- **Primary Technologies**: List key technologies
- **Issue Tracking**: Yes/No
- **Dependencies**: List related repositories
- **Notes**: Any special considerations
```

---

## Notes

- Keep this file up to date as your homelab evolves
- Remove archived or deprecated repositories
- The agent uses this for context, so accuracy is important
- Consider adding private repositories if the agent needs awareness of them
