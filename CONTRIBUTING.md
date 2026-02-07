# Contributing to Homelab Assistant Agent

Thank you for your interest in improving the Homelab Assistant Agent! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

If you encounter problems or have suggestions:

1. Check existing issues to avoid duplicates
2. Open a new issue with a clear description
3. Include relevant details:
   - What you were trying to do
   - What the agent did or suggested
   - What you expected instead
   - Any error messages or logs

### Improving the Agent

The agent can be improved in several ways:

#### 1. Enhancing Knowledge Areas

Add or improve expertise in specific domains:

- Update `.github/agents/homelab-assistant.agent.md`
- Add new skill sections with practical guidance
- Include examples and common scenarios
- Explain best practices vs. homelab trade-offs

#### 2. Improving Documentation

- Enhance README.md with better examples
- Add troubleshooting guides
- Create tutorials for common tasks
- Improve repolist.md template

#### 3. Adding Examples

- Document real-world usage scenarios
- Share successful configurations
- Contribute homelab setup guides
- Add command references and cheat sheets

## Development Process

### Making Changes

1. **Fork the repository**
   ```bash
   gh repo fork wilsonwong1990/homelab-assistant-agent
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-improvement
   ```

3. **Make your changes**
   - Edit relevant files
   - Test the agent behavior
   - Update documentation

4. **Commit with clear messages**
   ```bash
   git commit -m "Add guidance for Docker container management"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-improvement
   gh pr create
   ```

### Testing Changes

When modifying the agent:

1. Test with actual homelab scenarios
2. Verify the agent provides helpful, accurate guidance
3. Check that examples work as described
4. Ensure documentation matches behavior

### Code Review

Pull requests will be reviewed for:

- Accuracy of technical information
- Appropriateness for homelab context
- Clarity of documentation
- Consistency with existing style

## Contribution Guidelines

### Agent Prompt Guidelines

When editing the agent prompt:

- **Be Practical**: Focus on solutions that work in homelab environments
- **Be Educational**: Explain the "why" behind recommendations
- **Be Balanced**: Mention best practices while keeping homelab context
- **Be Specific**: Provide concrete examples and commands
- **Be Safe**: Always consider security implications

### Documentation Style

- Use clear, concise language
- Include code examples with syntax highlighting
- Provide context and explanations
- Link to official documentation where appropriate
- Keep a friendly, helpful tone

### Commit Messages

Follow conventional commit format:

- `feat:` New features or capabilities
- `fix:` Bug fixes or corrections
- `docs:` Documentation improvements
- `refactor:` Restructuring without behavior change
- `test:` Adding or updating tests

Examples:
```
feat: Add Ansible automation guidance
docs: Improve K3s setup examples
fix: Correct Proxmox storage configuration advice
```

## Areas for Contribution

### High Priority

- [ ] Additional skill modules (Docker, Ansible, etc.)
- [ ] More detailed examples for each skill area
- [ ] Troubleshooting guides for common issues
- [ ] Integration guides for popular homelab tools

### Medium Priority

- [ ] Video tutorials or walkthroughs
- [ ] Template configurations for common setups
- [ ] Best practices documentation
- [ ] Comparison guides (e.g., k3s vs k8s, pfSense vs OPNsense)

### Nice to Have

- [ ] Community showcase of homelab setups
- [ ] Integration with homelab monitoring tools
- [ ] Automated testing of agent responses
- [ ] Multi-language support

## Community

### Communication

- **Issues**: For bug reports and feature requests
- **Discussions**: For questions and community interaction
- **Pull Requests**: For contributing code and documentation

### Code of Conduct

- Be respectful and constructive
- Welcome newcomers and help them learn
- Focus on what's best for the homelab community
- Assume good intentions

## Recognition

Contributors will be recognized in:
- README.md acknowledgments section
- Release notes for significant contributions
- Project documentation

## Questions?

If you're unsure about anything:

1. Open an issue with your question
2. Check existing documentation
3. Look at previous pull requests for examples

Thank you for helping make homelab infrastructure more accessible!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
