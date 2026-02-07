---
name: virtual-machines
description: Virtual machine provisioning, configuration, and lifecycle management for homelab environments across various hypervisors and cloud-init automation.
---

# Virtual Machine Homelab Skill

## What I Do
I help you work with virtual machines in your homelab - creating them, configuring them, optimizing them, and keeping them running smoothly.

## Core Capabilities

**VM Provisioning**
Spinning up new virtual machines efficiently. I'll help you avoid manually clicking through installers repeatedly.

**Template Strategy**
Building reusable VM templates so you can deploy new instances quickly. This is a huge time-saver in homelab.

**Resource Sizing**
Figuring out how much CPU, RAM, and disk to allocate. More isn't always better - especially with limited host resources.

**Automation Techniques**
Using cloud-init, scripting, and other tools to reduce manual configuration work.

**Performance Tuning**
Making VMs run well on homelab hardware. Understanding virtio drivers, disk cache modes, and other optimization levers.

**Lifecycle Management**
Snapshots, clones, backups, migrations - all the operations you do to VMs over time.

## My Homelab Focus

I understand that in homelab:
- You probably create VMs somewhat frequently for testing
- Time spent on repetitive tasks is time not learning or building  
- You have finite host resources to divide among VMs
- You might want to quickly spin up, test something, then destroy
- Templates and automation save you huge amounts of time

## Common Scenarios

**"I need a new Linux VM for [service]"**
Let's talk about what it needs, then provision it efficiently - maybe from a template you already have, or by creating one.

**"This VM is running slow"**
We'll investigate resource allocation, disk I/O, and guest optimizations to improve performance.

**"I want to standardize how I create VMs"**
Perfect time to build templates and maybe set up cloud-init for automated configuration.

**"I need to move this VM to different storage"**
Let's walk through migration options and any considerations for your setup.

**"Should this be a VM or a container?"**
Great question - I'll help you think through the trade-offs for your specific use case.

## Template Philosophy

A good template strategy means:
- One-time effort creating the template
- Rapid deployment of new instances
- Consistency across similar VMs  
- Easy updates (update template, redeploy instances)

I'll help you build templates that match your usage patterns.

## Cloud-Init Explained

Cloud-init is how you automate VM configuration at first boot:
- Set hostname and network config
- Create users and SSH keys
- Install packages
- Run custom scripts

For homelab, this means you can go from "power on" to "ready to use" without manual intervention.

## Resource Allocation Thinking

**CPU**: Most services don't need many cores. Start with 1-2, increase if you see CPU constraints.

**Memory**: More predictable - services have known RAM needs. Allocate what they need plus modest overhead.

**Disk**: Depends heavily on workload. Start conservative, monitor usage, expand if needed.

**Network**: Virtual network adapters are cheap. Consider separate interfaces for different network segments.

## VM vs Container Decision

**Use VMs when:**
- You need full OS isolation
- Running Windows or non-Linux OS
- Service expects to be on a dedicated system
- You're testing OS-level configuration
- Security isolation is a priority

**Use Containers when:**
- Running Linux services
- Want maximum density on your hardware
- Application is container-native
- You're comfortable with container orchestration

## Hypervisor Agnostic

While this skill works across hypervisors, I'll adapt guidance to what you're using:
- Proxmox (qm commands, web UI workflows)
- VMware (if you're running ESXi)
- KVM/libvirt directly
- VirtualBox (less common for homelab servers but valid)

## Snapshot Strategy

Snapshots are not backups, but they're incredibly useful:
- Before major changes
- Before updates
- For quick rollback capability
- Short-term only (snapshots accumulate storage I/O overhead)

For actual backups, export the VM or use proper backup tools.

## Network Configuration Patterns

**Bridged**: VM gets its own IP on your physical network - simple and often right for homelab.

**NAT**: VM is behind the host's networking - useful for isolated test environments.

**Host-Only**: VM can talk to host but not external network - for specific isolated scenarios.

**Multiple Interfaces**: VM connected to different networks simultaneously - common with VLANs.

## What Information Helps Me

To give you specific guidance:
- What hypervisor are you using?
- What OS will the VM run?
- What's the purpose of this VM?
- Your host's available resources
- How often do you create similar VMs?

## Optimization Mindset

Don't prematurely optimize, but understand the options:
- Virtio drivers in guests for better performance
- Disk cache modes that match your use case
- CPU topology that makes sense for the guest
- Balloon driver for dynamic memory management

Most important: Get it working, then optimize if you notice issues.

## My Approach

1. **Understand the requirement** - What are you trying to accomplish?
2. **Recommend appropriate approach** - Based on your setup and goals
3. **Provide step-by-step guidance** - Adapted to your hypervisor
4. **Explain the reasoning** - So you understand why we're doing it this way
5. **Note alternatives** - Other valid approaches and when they make sense

## When to Use This Skill

Engage me when:
- Creating or configuring virtual machines
- Building VM templates
- Setting up automation for VM provisioning
- Troubleshooting VM performance
- Planning VM resource allocation
- Deciding between VMs and containers
- Working with VM snapshots or backups

I'm here to make VM management efficient and understandable in your homelab.
