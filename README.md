# Homelab Tools Marketplace

A GitHub Copilot plugin marketplace for practical homelab infrastructure and operations. It currently offers one cohesive plugin: a homelab orchestrator with 11 focused skills.

The plugin is designed to be installed in multiple homelab repositories. It contains reusable guidance, not your inventory, network layout, credentials, or MCP configuration.

## Install

In GitHub Copilot CLI, add the marketplace and install the plugin:

```shell
copilot plugin marketplace add wilsonwong1990/homelab-assistant-agent
copilot plugin marketplace browse homelab-tools
copilot plugin install homelab-assistant@homelab-tools
```

For other Copilot clients, follow their plugin installation instructions; plugin component support varies by client. See [the plugin and marketplace reference](https://docs.github.com/en/copilot/reference/plugin-and-marketplace-reference) and [customizing GitHub Copilot](https://docs.github.com/en/copilot/concepts/customizations/plugins).

To try the package locally with Copilot CLI, run these commands from a checkout of this repository:

```shell
copilot plugin marketplace add .
copilot plugin marketplace browse homelab-tools
copilot plugin install homelab-assistant@homelab-tools
```

## What's included

`homelab-assistant` is one cross-domain custom agent supported by these skills:

| Skill | Focus |
| --- | --- |
| `proxmox` | Hypervisor, VMs, containers, and storage |
| `kubernetes` | Upstream Kubernetes and workload operations |
| `k3s` | Lightweight Kubernetes clusters |
| `virtual-machines` | VM provisioning and cloud-init |
| `firewall` | Network security, VPNs, and segmentation |
| `unifi` | UniFi networking equipment |
| `nextdns` | DNS rewrites and profile configuration |
| `documentation` | Runbooks and homelab knowledge management |
| `code-review` | Code quality and security review |
| `qa` | Cross-domain plan validation |
| `elk` | Elastic Stack observability |

The orchestrator uses relevant skills for a single-domain question and coordinates domain planning for larger projects. It can provide useful guidance without MCP integrations; integrations are optional and must be configured separately by each user or project.

## Safety and personal configuration

- The plugin does not include credentials, live infrastructure configuration, or repository inventories.
- Keep environment-specific details in a private, user-managed location and provide only the context needed for a task.
- Infrastructure and GitHub writes are not automatic. The agent acts only on an explicit user request.
- MCP server configuration is not installed with this plugin. Configure integrations separately, with the permissions and credential handling appropriate to your environment.

## Contributing

The marketplace catalog is `.github/plugin/marketplace.json`. The plugin is self-contained under `plugins/homelab-assistant/`:

```text
plugins/homelab-assistant/
├── plugin.json
├── com.github.copilot/agents/
│   └── homelab-assistant.agent.md
└── skills/
    ├── code-review/SKILL.md
    ├── documentation/SKILL.md
    ├── elk/SKILL.md
    ├── firewall/SKILL.md
    ├── k3s/SKILL.md
    ├── kubernetes/SKILL.md
    ├── nextdns/SKILL.md
    ├── proxmox/SKILL.md
    ├── qa/SKILL.md
    ├── unifi/SKILL.md
    └── virtual-machines/SKILL.md
```

Keep the plugin self-contained, preserve the skill frontmatter, and do not add personal infrastructure details or credentials. Validate JSON files with `python3 -m json.tool <file>` and check that every marketplace source and skill path exists before submitting a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
