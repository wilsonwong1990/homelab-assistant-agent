# Homelab Assistant Agent

A specialized GitHub Copilot Agent for homelab infrastructure and operations. This agent uses a **modular skills architecture** to provide expert guidance on Proxmox, Kubernetes (k8s/k3s), virtual machines, firewalls, Ubiquiti Unifi, Elastic (ELK) observability, and documentation management.

## Overview

The Homelab Assistant Agent is designed to help you manage and optimize your homelab environment. It understands that homelab setups are different from production environments and provides appropriate recommendations while teaching best practices.

### Modular Architecture

This agent uses a **hybrid architecture** combining GitHub Copilot Agent Skills with a subagent dispatch pattern:

```
.github/
├── agents/
│   └── homelab-assistant.agent.md    # Orchestrating agent
└── skills/
    ├── proxmox/SKILL.md               # Proxmox expertise      ← subagent-capable
    ├── kubernetes/SKILL.md            # Upstream Kubernetes expertise
    ├── k3s/SKILL.md                   # Lightweight K3s expertise ← subagent-capable
    ├── virtual-machines/SKILL.md      # VM management
    ├── firewall/SKILL.md              # Network security        ← subagent-capable
    ├── unifi/SKILL.md                 # UniFi equipment         ← subagent-capable
    ├── documentation/SKILL.md         # Documentation practices
    ├── ELK/SKILL.md                   # Elastic Stack observability
    └── qa/SKILL.md                    # Quality gate validation  ← subagent-capable
```

**Two modes of operation:**
- **Skills as context**: For single-domain questions, skill knowledge loads into the agent's context (fast, simple)
- **Subagent dispatch**: For multi-domain projects, the orchestrator dispatches focused subagents that investigate and plan in parallel, then integrates their results

**Benefits:**
- **Parallel execution**: Query Proxmox and UniFi infrastructure simultaneously
- **Focused context**: Each subagent reasons deeply in its domain without context crowding
- **Cross-domain integration**: Orchestrator catches dependencies other agents can't see
- **Graceful degradation**: Falls back to sequential skill-as-context when dispatch isn't available

## Features

### Modular Skills

Each skill provides specialized knowledge:

- **proxmox** (`.github/skills/proxmox/`): Hypervisor operations, VM/CT management, storage strategies, backup workflows
- **kubernetes** (`.github/skills/kubernetes/`): Upstream Kubernetes cluster deployment, workload management, GitOps, storage integration
- **k3s** (`.github/skills/k3s/`): Lightweight K3s installs, HA topologies, networking, storage, and day-2 ops for homelab
- **virtual-machines** (`.github/skills/virtual-machines/`): VM provisioning, templates, resource optimization, cloud-init automation
- **firewall** (`.github/skills/firewall/`): Network security, rule management, VPN setup, VLAN segmentation
- **unifi** (`.github/skills/unifi/`): UniFi controller, access points, switches, network optimization
- **documentation** (`.github/skills/documentation/`): Note-taking, runbooks, knowledge management, issue tracking
- **ELK** (`.github/skills/ELK/`): Elastic Stack logging, metrics, tracing, dashboards, alerting for homelab observability
- **QA** (`.github/skills/qa/`): Quality gate that validates integrated plans for cross-domain consistency, safety, and completeness before execution

### Orchestrating Agent

The main agent (`.github/agents/homelab-assistant.agent.md`) coordinates these skills using a **phased execution model**:

**For single-domain questions** (e.g., "How do I passthrough a GPU?"):
- Loads the relevant skill as context and answers directly

**For multi-domain projects** (e.g., "Build a Proxmox cluster for k3s + Longhorn"):

```
         ┌──────────────────────┐
         │    Orchestrator      │
         │  Classify → Dispatch │
         │  → Plan/Integrate/QA │
         └──────┬───────────────┘
                │
    Phase 1: Discovery (parallel)
    ┌───────────┼───────────────┐
    │           │               │
    ▼           ▼               │
┌────────┐ ┌────────┐          │
│Proxmox │ │ UniFi  │          │
│  MCP   │ │  MCP   │          │
│ query  │ │ query  │          │
└───┬────┘ └───┬────┘          │
    │          │               │
    Phase 2: Planning (parallel, with Phase 1 results)
    ┌──────────┼───────────────┐
    │          │               │
    ▼          ▼               ▼
┌────────┐ ┌────────┐  ┌──────────┐
│  K3s   │ │Firewall│  │ Context: │
│cluster │ │  VLAN  │  │ VMs, k8s │
│  plan  │ │  plan  │  │ docs,ELK │
└───┬────┘ └───┬────┘  └────┬─────┘
    │          │             │
    Phase 3: Integration (orchestrator)
    └──────────┴─────────────┘
              │
    ┌─────────▼──────────┐
    │ Integrated Plan    │
    └─────────┬──────────┘
              │
    Phase 4: Quality Gate
    ┌─────────▼──────────┐
    │   QA subagent      │
    │ validates plan for │
    │ consistency,safety │
    └─────────┬──────────┘
              │
    ┌─────────▼──────────┐
    │  Final Plan with   │
    │  QA-verified steps │
    └────────────────────┘
```

- Classifies the task scope (single vs multi-domain)
- Dispatches focused subagents for domain-specific investigation and planning
- Integrates results, catching cross-domain dependencies
- Dispatches QA subagent to validate the integrated plan before delivery
- Presents a coherent, sequenced, QA-validated implementation plan

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

### MCP Server Setup

This agent uses [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) servers to connect to your homelab infrastructure. The configuration lives in `.github/copilot/mcp.json`.

**The committed config uses placeholder paths.** To use the MCP servers, update the paths for your local environment:

1. **Proxmox MCP** ([wilsonwong1990/proxmox-mcp](https://github.com/wilsonwong1990/proxmox-mcp)):
   ```bash
   # Clone and build
   git clone https://github.com/wilsonwong1990/proxmox-mcp.git
   cd proxmox-mcp && npm install && npm run build

   # Add to ~/.zshrc (or ~/.bashrc)
   export PROXMOX_HOST="https://your-proxmox-host:8006"
   export PROXMOX_TOKEN_ID="user@pam!token-name"
   export PROXMOX_TOKEN_SECRET="your-token-secret"
   export PROXMOX_ALLOW_SELF_SIGNED="true"
   export PROXMOX_READ_ONLY="true"
   ```

2. **UniFi Network MCP** ([sirkirby/unifi-mcp](https://github.com/sirkirby/unifi-mcp)):
   ```bash
   # Install uv (Python package runner)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Add to ~/.zshrc (or ~/.bashrc)
   export UNIFI_HOST="your-unifi-controller-ip"
   export UNIFI_USERNAME="your-local-admin-username"
   export UNIFI_PASSWORD="your-admin-password"
   export UNIFI_VERIFY_SSL="false"
   ```

3. **Set up MCP config** from the example template:
   ```bash
   cp .github/copilot/mcp.json.example .github/copilot/mcp.json
   # Edit mcp.json with your local paths (this file is gitignored)
   ```

   > **Note:** Use absolute paths. Find `uvx` with `which uvx` after installing `uv`. Credentials are sourced from shell environment variables — never commit secrets to this file.

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

3. **Update `repolist.private.md`**: Add your homelab repositories to the list:
   ```bash
   # Edit repolist.private.md to include your repositories
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

### Why Hybrid Skills + Subagents?

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

**Now (Hybrid Subagent Architecture)**:
- Skills serve dual purpose: context modules AND dispatchable subagents
- Multi-domain tasks execute in parallel instead of serially
- Each subagent gets a clean, focused context window
- Orchestrator focuses on cross-domain integration — its unique value
- Falls back gracefully to context-only mode when dispatch isn't available

### Subagent-Capable Skills

| Skill | MCP Backend | Subagent Capability |
|-------|-------------|---------------------|
| **Proxmox** | proxmox-mcp (read-only) | Queries real node/storage/VM state |
| **UniFi** | unifi-network | Queries real switch/VLAN/device state |
| **K3s** | — | Deep cluster topology and sizing planning |
| **Firewall** | — | Independent VLAN/rules design with security matrix |
| **QA** | — | Validates integrated plans before execution |

### Context-Only Skills

| Skill | Purpose |
|-------|---------|
| **Kubernetes** | Upstream concepts (K3s handles specifics) |
| **Virtual Machines** | VM sizing and lifecycle knowledge |
| **Documentation** | Cross-cutting documentation practices |
| **ELK** | Observability layer (post-infrastructure) |

### Real-World Example

**Task**: "Set up k3s cluster on Proxmox with VLAN segmentation"

**Orchestrator classifies**: Multi-domain → phased execution

**Phase 1 — Discovery (parallel dispatch):**
- Proxmox subagent queries MCP → reports: 2 nodes, 32GB RAM each, local-lvm + NFS storage, 4 existing VMs
- UniFi subagent queries MCP → reports: USW-Pro-48, VLANs 1/10/20 in use, 30 ports available

**Phase 2 — Planning (parallel dispatch with Phase 1 results):**
- K3s subagent → recommends: 3 dual-role nodes, 4 vCPU / 8GB RAM each, Longhorn with dedicated 100GB disk, MetalLB range 10.0.20.100-150
- Firewall subagent → recommends: VLAN 30 for k3s inter-node, VLAN 40 for Longhorn replication, firewall rule matrix for all flows

**Phase 3 — Integration (orchestrator):**
- Maps K3s network requirements to specific VLAN IDs
- Distributes VMs across Proxmox nodes (2 on node1, 1 on node2)
- Designs Linux bridges on Proxmox nodes for new VLANs
- Configures UniFi switch trunk ports for Proxmox uplinks
- Sequences implementation: VLANs first → bridges → VMs → k3s install → Longhorn

**Skills Engaged**:
1. **proxmox** (subagent): Queried infrastructure, created VM plan
2. **virtual-machines** (context): Informed VM sizing decisions
3. **k3s** (subagent): Designed cluster topology and requirements
4. **firewall** (subagent): Designed network segmentation
5. **unifi** (subagent): Queried and planned switch configuration
6. **documentation** (context): Structured the output plan

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
- [Elastic Stack Documentation](https://www.elastic.co/guide/index.html)


## Support

For issues or questions:
- Open an issue in this repository
- Check existing issues for similar questions
- Refer to the documentation and examples
