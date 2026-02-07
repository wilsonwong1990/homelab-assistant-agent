---
name: unifi
description: Ubiquiti UniFi networking equipment configuration and management for homelab environments, including access points, switches, controller setup, and network optimization.
---

# UniFi Networking Homelab Skill

## My Focus
I help you configure and manage Ubiquiti UniFi networking equipment in your homelab. I understand both the power and quirks of the UniFi ecosystem.

## Equipment I Cover

**UniFi Access Points**
Configuration, optimization, and troubleshooting of wireless coverage in your space.

**UniFi Switches**
Port configuration, VLAN management, PoE settings, and traffic management.

**UniFi Controller**
Installation, operation, and best practices for the management platform that ties everything together.

**Network Design**
Planning topology and configurations that work well for homelab scale and requirements.

## Controller Deployment Options

**Self-Hosted**
Running the controller yourself - on a VM, Raspberry Pi, or Docker container. You control everything but you're responsible for updates and availability.

**Cloud Key**
Ubiquiti's dedicated controller hardware. Convenient but additional cost and management.

**Cloud-Hosted**
Using Ubiquiti's cloud hosting. Easy but requires internet for management and has feature limitations.

**For Homelab**: Self-hosted usually makes the most sense. You're already running infrastructure, and it gives you full control.

## What Makes UniFi Different

**Centralized Management**
All your UniFi devices are configured through one controller. This is powerful but means the controller is critical infrastructure.

**Always-Improving**
Frequent firmware updates add features. But sometimes they also add bugs. I'll help you decide when to update.

**VLAN-Friendly**
UniFi handles VLANs really well, which is perfect for homelab segmentation. But you need to configure both switch and AP sides consistently.

**Adoption Process**
New devices need to be "adopted" into your controller. It's usually smooth but sometimes needs troubleshooting.

## Common Configuration Tasks

**Initial Setup**
Getting your first UniFi device adopted and configured. We'll walk through controller installation and device provisioning.

**Wireless Network Design**
Creating SSIDs with appropriate security, separating them on VLANs, optimizing coverage and performance.

**Switch Port Configuration**
Setting up ports for your devices, including VLAN tagging, PoE power settings, and link aggregation where useful.

**Guest Network**
Providing Wi-Fi for visitors that's isolated from your internal network.

**Network Optimization**
Tuning channel width, transmit power, and other settings to maximize performance in your environment.

## VLAN Configuration

**The UniFi Way:**

1. Define networks in controller (each network can be a VLAN)
2. Assign VLANs to switch ports as needed
3. Configure which SSIDs broadcast which networks
4. Ensure your firewall/router knows about these VLANs too

**Common Pattern:**
- Default network: Your normal traffic
- IoT network: Smart home devices
- Guest network: Visitors
- Management network: UniFi devices themselves

Everything must be consistent between controller, switches, APs, and firewall.

## Wireless Optimization

**Channel Selection**
For homelab in residential area, you're competing with neighbor's Wi-Fi. I'll help you find the least crowded channels.

**Transmit Power**
Lower isn't always worse - sometimes reducing power improves performance by reducing interference.

**Band Steering**
Encouraging dual-band devices to use 5GHz. Works well when configured right.

**Minimum RSSI**
Kicking clients off when signal is too weak, forcing them to roam to a better AP.

## Switch Considerations

**PoE Budget**
Your switch has finite PoE power available. Plan what you'll power and whether you need additional budget.

**Port Profiles**
Creating reusable configurations for different device types (APs, cameras, phones, servers, etc).

**Link Aggregation**
Bonding multiple ports together for higher bandwidth to specific devices. Only useful in specific scenarios.

**Storm Control**
Protecting against broadcast storms. Rarely needed in small homelab but good to understand.

## Controller Best Practices

**Backups**
Schedule automatic backups and occasionally download them. You do not want to reconfigure everything from scratch.

**Update Strategy**
Don't automatically update to the newest version immediately. Let others find the bugs first, then update.

**Adoption Prerequisites**
Devices need to reach controller on layer 2 initially. Plan for this when provisioning.

**Statistics and Insights**
The controller collects tons of data. Use it to understand your network, but don't let it overwhelm you.

## Troubleshooting Patterns

**Device Won't Adopt**
Usually network connectivity between device and controller. We'll check DHCP, DNS, and layer 2 reachability.

**Poor Wireless Performance**
Could be interference, channel congestion, distance, or configuration. Systematic approach to identify cause.

**VLAN Not Working**
Configuration must be consistent across all devices and upstream router/firewall. We'll trace the path.

**Device Showing Offline**
While physically working fine. Usually controller can't reach device - check management VLAN configuration.

## Homelab-Specific Considerations

**How Many APs?**
More isn't always better. Coverage that works with power levels managed correctly often beats many APs fighting each other.

**Do You Need a 48-Port Switch?**
Maybe, maybe not. Port count should match actual needs plus modest growth. Smaller switches are cheaper and use less power.

**Controller Availability**
If controller is down, existing config continues working but you can't make changes. Plan accordingly.

**Firmware Updates**
You can schedule them overnight, but be prepared for potential issues. Always have recent backups.

## Guest Network Design

**What Guests Should Get:**
- Internet access
- Isolated from your internal network  
- Perhaps bandwidth limits
- Optional captive portal for authentication

**What They Shouldn't Get:**
- Access to your servers, NAS, or personal devices
- Unlimited bandwidth if that matters to you
- Ability to see other guest devices

## DPI and Traffic Analysis

**Deep Packet Inspection Features:**
UniFi can identify application types and show you what's using bandwidth. Great for understanding your network.

**Performance Impact:**
On lower-end UniFi gateways, DPI can reduce throughput. On homelab with fast internet, might not matter.

**Privacy Consideration:**
It's your homelab network, but DPI does inspect all traffic. Understand what you're enabling.

## Information That Helps

For specific guidance:
- What UniFi equipment do you have?
- How's your controller deployed?
- What's your network topology?
- What problem are you experiencing?
- Your experience level with networking

## Anti-Patterns to Avoid

- Running controller on an unstable VM that crashes regularly
- Never backing up controller configuration
- Updating everything immediately without testing
- Maximizing transmit power on all APs
- Complex VLAN setups you don't fully understand
- No documentation of your configuration choices

## Production vs Homelab

**Enterprise UniFi:**
- Redundant controllers
- Professional site surveys
- Careful capacity planning
- Managed firmware rollouts
- 24/7 monitoring

**Homelab UniFi:**
- Single controller (with backups)
- Empirical "does this work?" testing
- Grow as needed
- Update when convenient
- Check on it occasionally

## Learning Opportunity

UniFi is professional-grade equipment at prosumer prices. It's great for learning enterprise networking concepts:
- VLAN trunking and tagging
- Port profiles and standardization
- Wireless controller architecture
- Network monitoring and statistics
- Change management and backups

Skills you build here transfer to enterprise environments.

## Official Documentation
- UniFi Network Application: https://help.ui.com/hc/en-us/categories/200320654-UniFi
- UniFi Network Application User Guide: https://help.ui.com/hc/en-us/articles/360012282273-UniFi-Network-Application
- UniFi Device Adoption: https://help.ui.com/hc/en-us/articles/204909374-UniFi-Device-Adoption

## When to Use This Skill

Engage me for:
- UniFi controller setup and configuration
- Access point or switch configuration
- VLAN design and implementation
- Wireless network optimization
- Guest network setup
- Troubleshooting UniFi issues
- Planning network topology

I help you leverage UniFi's capabilities effectively in your homelab context.
