# Homelab Assistant Agent

A specialized GitHub Copilot Agent for homelab infrastructure and operations. This agent uses a **modular skills architecture** to provide expert guidance on Proxmox, Kubernetes (k8s/k3s), virtual machines, firewalls, Ubiquiti Unifi, and documentation management.

## Overview

The Homelab Assistant Agent is designed to help you manage and optimize your homelab environment. It understands that homelab setups are different from production environments and provides appropriate recommendations while teaching best practices.

### Modular Architecture

This agent uses **GitHub Copilot Agent Skills** - a modular architecture where domain expertise is separated into focused, reusable skills. Each skill is loaded contextually based on your needs:

```
.github/
├── agents/
│   └── homelab-assistant.agent.md    # Orchestrating agent
└── skills/
    ├── proxmox/SKILL.md               # Proxmox expertise
    ├── kubernetes/SKILL.md            # K8s/K3s expertise
    ├── virtual-machines/SKILL.md      # VM management
    ├── firewall/SKILL.md              # Network security
    ├── unifi/SKILL.md                 # UniFi equipment
    └── documentation/SKILL.md         # Documentation practices
```

**Benefits:**
- **Context-aware**: Skills load only when relevant to your task
- **Maintainable**: Update individual skills independently
- **Extensible**: Add new skills without modifying the core agent
- **Focused**: Each skill provides deep expertise in its domain

## Features

### Modular Skills

Each skill provides specialized knowledge:

- **proxmox** (`.github/skills/proxmox/`): Hypervisor operations, VM/CT management, storage strategies, backup workflows
- **kubernetes** (`.github/skills/kubernetes/`): K3s/K8s cluster deployment, workload management, GitOps, storage integration
- **virtual-machines** (`.github/skills/virtual-machines/`): VM provisioning, templates, resource optimization, cloud-init automation
- **firewall** (`.github/skills/firewall/`): Network security, rule management, VPN setup, VLAN segmentation
- **unifi** (`.github/skills/unifi/`): UniFi controller, access points, switches, network optimization
- **documentation** (`.github/skills/documentation/`): Note-taking, runbooks, knowledge management, issue tracking

### Orchestrating Agent

The main agent (`.github/agents/homelab-assistant.agent.md`) coordinates these skills:
- Understands your overall goal
- Identifies which skills are relevant
- Coordinates multi-domain tasks
- Provides integrated, coherent guidance
- Maintains homelab context across domains

### Key Capabilities

- **Homelab-Aware**: Provides practical solutions appropriate for non-production environments
- **Educational**: Explains best practices and why homelab trade-offs are acceptable
- **Security-Conscious**: Maintains security awareness even in learning contexts
- **Repository-Aware**: Uses `repolist.md` to track and manage multiple homelab repositories
- **Cross-Domain**: Handles projects spanning multiple skill areas
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

2. **For existing projects**: Copy both the agent and skills to your repository:
   ```bash
   mkdir -p .github/agents .github/skills
   cp homelab-assistant-agent/.github/agents/homelab-assistant.agent.md .github/agents/
   cp -r homelab-assistant-agent/.github/skills/* .github/skills/
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
4. The agent will automatically load relevant skills based on your question

Example prompts:
```
@homelab-assistant How do I set up a k3s cluster on Proxmox VMs?
# This engages: proxmox, kubernetes, virtual-machines, and documentation skills

@homelab-assistant Help me configure VLANs on my Unifi switch
# This engages: unifi and firewall skills

@homelab-assistant What's the best way to backup my Proxmox VMs?
# This engages: proxmox and documentation skills
```

### How Skills Load

Skills are loaded **contextually** based on your needs:
- Ask about Kubernetes → kubernetes skill loads
- Ask about network security → firewall skill loads
- Multi-domain question → multiple skills coordinate

You don't need to manually specify which skill to use - the agent figures this out.

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

The `repolist.private.md` file tracks all repositories in your homelab ecosystem. Update it when you:

- Create new repositories for homelab work
- Change repository purposes or structure
- Archive or deprecate repositories
- Need to cross-reference configurations

### Issue Tracking

The agent can log work as GitHub issues. For significant tasks:

1. The agent identifies the appropriate repository from `repolist.private.md`
2. Creates an issue documenting the work
3. Links related issues across repositories
4. Updates documentation as needed

## Extending the Agent

### Adding New Skills

To create a new skill:

1. **Create skill directory**:
   ```bash
   mkdir -p .github/skills/your-skill-name
   ```

2. **Create SKILL.md file** with frontmatter:
   ```markdown
   ---
   name: your-skill-name
   description: Brief description of what this skill provides
   ---
   
   # Your Skill Name
   
   [Detailed skill instructions and expertise...]
   ```

3. **Update agent metadata** in `.github/agents/homelab-assistant.agent.md`:
   ```yaml
   metadata:
     skills:
       - proxmox
       - kubernetes
       - your-skill-name  # Add your new skill
   ```

4. **Test your skill**: Use the agent with questions related to your new skill domain

**Skill Writing Tips:**
- Be specific about when the skill should activate
- Provide practical guidance for homelab scale
- Include both how-to and why explanations
- Note production differences where relevant

### Customizing Existing Skills

Edit any skill file in `.github/skills/[skill-name]/SKILL.md` to:
- Add more detailed guidance
- Include your specific environment details
- Document your standards and preferences
- Add troubleshooting for issues you've encountered

## Architecture Benefits

### Why Modular Skills?

**Before (Monolithic)**:
- Single large agent file with all knowledge
- All expertise loaded for every question
- Harder to maintain and extend
- Mixed concerns in one place

**After (Modular Skills)**:
- Focused, maintainable skill files
- Context-aware loading (only what's needed)
- Easy to extend with new domains
- Clear separation of concerns
- Better organization and discoverability

### Real-World Example

**Task**: "Set up k3s cluster on Proxmox with VLAN segmentation"

**Skills Engaged**:
1. **proxmox**: Creating VMs for cluster nodes
2. **virtual-machines**: Template and sizing guidance
3. **kubernetes**: K3s installation and configuration
4. **firewall**: VLAN design and rules
5. **documentation**: Recording the setup

**Orchestration**: The main agent coordinates these skills to provide integrated guidance that works across all domains.

## Examples

### Example 1: Single-Skill Question

**You**: "How do I pass through a GPU to a Proxmox VM?"

**Agent Behavior**:
- Loads **proxmox** skill
- Provides PCI passthrough guidance
- Explains IOMMU requirements
- Notes homelab vs production considerations

### Example 2: Multi-Skill Project

**You**: "I want to set up a k3s cluster with 3 nodes on Proxmox VMs"

**Agent Behavior**:
- Loads **proxmox**, **kubernetes**, **virtual-machines**, **documentation** skills
- Coordinates VM creation with cluster requirements
- Provides integrated step-by-step guidance
- Suggests documentation approach

### Example 3: Network Security

**You**: "Help me segment my IoT devices from my main network"

**Agent Behavior**:
- Loads **firewall** and **unifi** skills (if you have UniFi equipment)
- Designs VLAN strategy
- Configures switch and firewall rules
- Explains security reasoning

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
