# Homelab Assistant Agent

A specialized GitHub Copilot Agent for homelab infrastructure and operations. This agent provides expert guidance on Proxmox, Kubernetes (k8s/k3s), virtual machines, firewalls, Ubiquiti Unifi, and maintains documentation for homelab work.

## Overview

The Homelab Assistant Agent is designed to help you manage and optimize your homelab environment. It understands that homelab setups are different from production environments and provides appropriate recommendations while teaching best practices.

## Features

### Core Skills

- **Proxmox Virtual Environment**: VM/CT management, storage, clustering, backups
- **Kubernetes & K3s**: Cluster deployment, workload management, GitOps, storage
- **Virtual Machines**: Provisioning, templates, resource optimization
- **Firewall & Network Security**: pfSense, OPNsense, VLANs, VPN, security policies
- **Ubiquiti Unifi**: Controller setup, AP/switch configuration, network design
- **Note Taking & Documentation**: Recording changes, creating runbooks, knowledge base

### Key Capabilities

- **Homelab-Aware**: Provides practical solutions appropriate for non-production environments
- **Educational**: Explains best practices and why homelab trade-offs are acceptable
- **Security-Conscious**: Maintains security awareness even in learning contexts
- **Repository-Aware**: Uses `repolist.md` to track and manage multiple homelab repositories
- **Issue Tracking**: Logs significant work as GitHub issues in appropriate repositories

## Installation

### Prerequisites

- GitHub Copilot subscription (Individual, Business, or Enterprise)
- GitHub Copilot enabled in your development environment (VS Code, CLI, etc.)

### Setup

1. **Clone this repository** (if creating a new homelab agent):
   ```bash
   git clone https://github.com/wilsonwong1990/homelab-assistant-agent.git
   ```

2. **For existing projects**: Copy the agent configuration to your repository:
   ```bash
   mkdir -p .github/agents
   cp homelab-assistant-agent/.github/agents/homelab-assistant.agent.md .github/agents/
   ```

3. **Update `repolist.md`**: Add your homelab repositories to the list:
   ```bash
   # Edit repolist.md to include your repositories
   vim repolist.md
   ```

## Usage

### In VS Code

1. Open a project that includes the homelab agent configuration
2. Use the GitHub Copilot chat interface
3. Reference the agent with `@homelab-assistant` or let it auto-infer based on context
4. Ask questions or request help with homelab tasks

Example prompts:
```
@homelab-assistant How do I set up a k3s cluster on Proxmox VMs?
@homelab-assistant Help me configure VLANs on my Unifi switch
@homelab-assistant What's the best way to backup my Proxmox VMs?
```

### In GitHub Copilot CLI

```bash
# Use the agent for homelab questions
gh copilot suggest "set up k3s cluster"

# Get explanations for commands
gh copilot explain "kubectl get pods -A"
```

### In GitHub Copilot Workspace

The agent will automatically be available when working in Copilot Workspace on repositories that include this agent configuration.

## Repository Management

### Using repolist.md

The `repolist.md` file tracks all repositories in your homelab ecosystem. Update it when you:

- Create new repositories for homelab work
- Change repository purposes or structure
- Archive or deprecate repositories
- Need to cross-reference configurations

### Issue Tracking

The agent can log work as GitHub issues. For significant tasks:

1. The agent identifies the appropriate repository from `repolist.md`
2. Creates an issue documenting the work
3. Links related issues across repositories
4. Updates documentation as needed

## Configuration

### Customizing the Agent

Edit `.github/agents/homelab-assistant.agent.md` to:

- Add or remove skills
- Adjust the agent's tone or approach
- Include custom tools or integrations
- Add organization-specific guidelines

### Adding Skills

To extend the agent with new skills, update the metadata section:

```yaml
metadata:
  skills:
    - proxmox
    - kubernetes
    - your-new-skill
```

Then add a corresponding section in the agent prompt explaining the skill.

## Examples

### Example 1: K3s Cluster Setup

**You**: "I want to set up a k3s cluster with 3 nodes on Proxmox VMs"

**Agent**: Provides step-by-step guidance including:
- VM specifications for homelab use
- K3s installation commands
- Network configuration
- Storage setup options
- Explains how production would differ

### Example 2: Firewall Configuration

**You**: "How should I configure firewall rules for my homelab?"

**Agent**: Recommends:
- Basic network segmentation for homelab
- Essential security rules
- Common services to expose/protect
- VPN setup for remote access
- Notes production-level requirements

### Example 3: Documentation

**You**: "Document the changes I made to my Unifi controller"

**Agent**:
- Creates structured documentation
- Logs an issue in the appropriate repository
- Cross-references related configurations
- Updates the knowledge base

## Best Practices

### When to Use This Agent

✅ **Use for:**
- Homelab infrastructure questions
- Self-hosted service setup
- Network and security configuration
- VM and container management
- Documentation and note-taking
- Learning about production practices

❌ **Don't use for:**
- Production environment configurations (use production-focused agents)
- Enterprise-scale solutions
- Compliance-specific requirements
- Mission-critical system design

### Working with the Agent

1. **Be Specific**: Provide context about your homelab setup
2. **Reference Files**: Mention relevant configurations or repositories
3. **Ask for Explanations**: Request details on best practices vs homelab trade-offs
4. **Iterate**: The agent can help refine solutions based on feedback

## Contributing

To improve this agent:

1. Fork the repository
2. Create a feature branch
3. Update the agent configuration or documentation
4. Submit a pull request with your improvements

Areas for contribution:
- Additional skills or knowledge areas
- Improved prompts or examples
- Better documentation
- Integration with tools or services

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

### Learning Resources

- [Proxmox Documentation](https://pve.proxmox.com/wiki/Main_Page)
- [K3s Documentation](https://docs.k3s.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [pfSense Documentation](https://docs.netgate.com/pfsense/en/latest/)
- [Unifi Documentation](https://help.ui.com/)

### Related Projects

- [Awesome Homelab](https://github.com/awesome-selfhosted/awesome-selfhosted)
- [Homelab subreddit](https://reddit.com/r/homelab)
- [Self-Hosted Podcast](https://selfhosted.show/)

## Support

For issues or questions:
- Open an issue in this repository
- Check existing issues for similar questions
- Refer to the documentation and examples

## Acknowledgments

Built for the homelab community, by the homelab community. Special thanks to all contributors who help make homelab infrastructure more accessible and manageable.
