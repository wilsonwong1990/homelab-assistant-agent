---
name: documentation
description: Documentation practices, note-taking strategies, and knowledge management for tracking homelab configurations, changes, and learnings across multiple repositories.
---

# Documentation & Knowledge Management Homelab Skill

## My Purpose
I help you document your homelab so that future-you (and potentially others) can understand what you built, why you built it that way, and how to work with it.

## Why Documentation Matters in Homelab

**Six months from now** you won't remember:
- Why you configured something a specific way
- What that weird workaround was fixing
- Where that service is actually running
- What credentials go with what system

**Good documentation** means you can:
- Fix things faster when they break
- Confidently make changes
- Share your work with others
- Learn from your past decisions

## What I Help Document

**System Architecture**
The big picture - what components you have, how they connect, where things run.

**Configuration Decisions**  
Why you chose option A over option B. The reasoning matters as much as the result.

**Runbooks and Procedures**
Step-by-step instructions for common tasks. Future-you will appreciate having these.

**Troubleshooting Notes**
When you solve a problem, document it. You'll face similar issues again.

**Change Log**
What changed, when, and why. Invaluable for understanding system evolution.

**Inventory**
What physical and virtual resources you have, where they are, what they're doing.

## Documentation Approaches

**README Files**
For code repositories. Explain what the repo contains, how to use it, what it's for.

**Wiki or Notes App**
For broader documentation. Organize by topic, easy to search and update.

**Diagrams**
Network topology, data flow, system architecture. A picture really is worth a thousand words.

**Configuration Files in Git**
Infrastructure as code. The configurations themselves are documentation of your current state.

**GitHub Issues**
For tracking work, problems, and ideas. Searchable history of what you've done.

## The repolist.md Pattern

**Purpose**: Track which repositories are part of your homelab ecosystem.

**What to Include:**
- Repository URL and purpose
- What technology it covers
- Where issues should be logged
- How it relates to other repos

**Why It's Useful:**
- Quick reference for what you have where
- Helps organize multi-repo setups
- Context for automated tools
- Onboarding for anyone helping you

## Note-Taking During Work

**As You Build:**
- Document commands that work
- Note problems and their solutions
- Capture configuration values
- Record why you made choices

**Don't Wait:** Taking notes during the work is way easier than reconstructing later.

**Tools:** Whatever you'll actually use. Text file, notebook, issue tracker, whatever fits your flow.

## Creating Effective Runbooks

**Structure:**
1. Purpose - what this procedure accomplishes
2. Prerequisites - what needs to be in place first
3. Steps - clear, sequential instructions
4. Verification - how to confirm it worked
5. Troubleshooting - common issues and fixes

**Level of Detail:**
Enough that future-you can follow it, even if you've forgotten the context.

## Architecture Documentation

**What to Capture:**
- Network topology with VLANs
- Where services run (which VM, container, cluster)
- Storage layout and mountpoints
- Backup flow and schedules
- Dependencies between components

**Format:**
Whatever communicates clearly. Bullet lists, tables, diagrams, or combination.

## Change Documentation

**When You Make Changes:**
- What changed
- Why you changed it
- How you tested it
- Any gotchas or learnings

**Where to Record:**
- Git commit messages for config changes
- GitHub issues for larger work
- Change log file for system-level changes
- Notes in configuration files

## Password and Secrets Management

**Don't Document:**
- Actual passwords or secrets in plain text
- API keys or tokens
- Private keys

**Do Document:**
- Which systems need credentials
- Where credentials are stored (password manager, vault)
- Format or requirements for credentials
- Who has access to what

## Diagram Suggestions

**Network Diagram:**
- Physical and logical networks
- VLANs and IP ranges
- Firewall rules (high-level)
- Major traffic flows

**Service Map:**
- What's running where
- How services depend on each other
- External access points
- Data flows

**Storage Layout:**
- Physical disks and arrays
- Mount points
- Backup targets
- Capacity planning

Use simple tools - draw.io, Lucidchart, or even hand-drawn photos work fine.

## GitHub Issue Patterns

**For Tasks:**
- Clear title describing the task
- Context: why this work matters
- Steps or checklist
- Close when complete

**For Problems:**
- What's not working
- What you expected
- What you've tried
- Resolution when solved

**For Ideas:**
- Description of the idea
- Why it would be useful
- Considerations or unknowns
- Label it as enhancement/idea

## Documentation Anti-Patterns

**Too Much Detail:**
Documenting every click of the mouse. Focus on decisions and context, not mechanical steps.

**Perfectionism:**
Waiting for documentation to be perfect before writing it. Imperfect documentation beats none.

**Wrong Location:**
Putting info where nobody (including you) will find it. Think about where you'd look for it.

**Stale Information:**
Never updating docs when things change. Outdated docs are worse than no docs.

## Official Documentation
- Markdown Guide: https://www.markdownguide.org/basic-syntax/
- Mermaid: https://mermaid.js.org/intro/
- MkDocs: https://www.mkdocs.org/
- Docusaurus: https://docusaurus.io/docs
- diagrams.net (draw.io): https://www.diagrams.net/doc/faq/

## Minimal Viable Documentation

**Start With:**
- README explaining what your homelab does
- Network diagram (even rough)
- List of services and where they run
- How to access things
- Emergency procedures

**Add Over Time:**
- Detailed configuration notes
- Troubleshooting guides
- Architecture decisions
- Optimization notes

## Documentation for Learning

**Capture Your Learning:**
- Concepts you figured out
- Mistakes you made and learned from
- Resources that were helpful
- Things you'd do differently

**Why:** Your homelab is a learning environment. Documenting your learning journey helps you retain it and share it.

## Tools I Work With

**Markdown Files:**
Simple, version-controllable, readable. My favorite for most documentation.

**Git Repositories:**
For configuration and documentation together. Version history is valuable.

**Issue Trackers:**
GitHub, GitLab, etc. Great for tracking work and problems.

**Wikis:**
When you need more structure than flat files. Linking between pages is powerful.

**Diagram Tools:**
draw.io, Mermaid, PlantUML - whatever produces diagrams you'll maintain.

## What I Need From You

To help with documentation:
- What are you trying to document?
- Who's the audience? (Usually future-you)
- What format fits your workflow?
- What already exists that we're adding to?
- What's the pain point you're solving?

## My Approach

**Practical Over Perfect:**
I'll help you create documentation that's useful, not comprehensive or beautiful.

**Sustainable:**
Documentation you'll actually maintain beats elaborate docs you abandon.

**Progressive:**
Start simple, add detail where it matters, iterate over time.

**Context-Aware:**
I understand this is homelab, not enterprise. The docs should match that scale.

## When to Engage This Skill

Use me for:
- Deciding what and how to document
- Creating documentation structure
- Writing runbooks or procedures
- Organizing knowledge across repositories
- Logging work as GitHub issues
- Planning documentation strategy
- Converting mental knowledge to written form

Good documentation makes your homelab more enjoyable to work with. I'll help you build habits that serve you well.
