# Infrastructure Diagnostics Guide

This guide covers the diagnostic workflows for troubleshooting EC2 instances and network connectivity issues.

## Overview

Two general-purpose diagnostic workflows are available for any EC2 instance in your environment:

| Workflow | Purpose | Key Checks |
|----------|---------|------------|
| `diagnose-instance.yml` | EC2 instance health | Status checks, SSM, security groups, console output |
| `diagnose-connectivity.yml` | Network connectivity | NACLs, route tables, ports, server status |

These complement the service-specific diagnostics (`ad-health-check.yml`, `scim-check-status.yml`) by providing lower-level infrastructure visibility.

---

## EC2 Instance Diagnostics (`diagnose-instance.yml`)

Comprehensive health check for any EC2 instance.

### Usage

```bash
gh workflow run diagnose-instance.yml \
  -f instance_id=i-0abc123def456 \
  -f environment=myorg \
  -f region=us-east-1
```

### What It Checks

1. **Instance Details** — State, type, IPs, launch time, platform, IAM profile, security groups, VPC/subnet
2. **Status Checks** — System status, instance status, scheduled events
3. **SSM Agent** — Ping status, last ping time, agent version, platform info
4. **Security Group Rules** — All inbound rules for all attached security groups
5. **Console Output** — Last 100 lines of serial console output (useful for boot issues)

### When to Use

- Instance is unreachable via SSM
- Instance shows degraded status checks
- Security group rules need verification
- Boot failures need investigation
- Need to verify IAM profile is attached

---

## Network Connectivity Diagnostics (`diagnose-connectivity.yml`)

Diagnose network path issues between components.

### Usage

```bash
gh workflow run diagnose-connectivity.yml \
  -f instance_id=i-0abc123def456 \
  -f environment=myorg \
  -f region=us-east-1
```

### What It Checks

1. **Network ACLs** — Inbound and outbound NACL rules for the instance's subnet
2. **Route Table** — All routes associated with the instance's subnet
3. **Server Status via SSM** — Auto-detects OS (Linux/Windows):
   - **Linux**: Listening ports (`ss`), running services, disk usage, network interfaces
   - **Windows**: TCP connections, running services, disk drives
4. **External Connectivity** — Port scan from GitHub Actions runner to instance public IP (ports 443, 80, 3389, 22)

### When to Use

- SCIM server not reachable from Okta
- OPA gateway can't connect to agents
- AD agent can't reach Okta cloud
- Outbound connectivity issues (NAT, route table)
- NACL blocking traffic unexpectedly

---

## Diagnostic Decision Tree

```
Problem: Can't reach a service
│
├─ Is the instance running?
│  └─ Run: diagnose-instance.yml → Check "Instance Details" (State)
│
├─ Are status checks passing?
│  └─ Run: diagnose-instance.yml → Check "Status Checks"
│
├─ Is SSM working?
│  └─ Run: diagnose-instance.yml → Check "SSM Agent" (PingStatus)
│
├─ Is the service running on the instance?
│  ├─ AD: Run ad-health-check.yml
│  ├─ SCIM: Run scim-check-status.yml
│  └─ Generic: Run diagnose-connectivity.yml → Check "Server Status"
│
├─ Are security groups correct?
│  └─ Run: diagnose-instance.yml → Check "Security Group Rules"
│
├─ Are NACLs blocking traffic?
│  └─ Run: diagnose-connectivity.yml → Check "Network ACLs"
│
└─ Is routing correct?
   └─ Run: diagnose-connectivity.yml → Check "Route Table"
```

## Common Issues

### SSM Agent Not Registered

If `diagnose-instance.yml` shows "SSM Agent not registered":
1. Verify the instance has an IAM role with `AmazonSSMManagedInstanceCore` policy
2. Check the instance can reach SSM endpoints (needs outbound HTTPS)
3. Check console output for SSM agent errors
4. For Windows: SSM agent is pre-installed on Amazon-provided AMIs
5. For Linux: Install with `yum install -y amazon-ssm-agent && systemctl start amazon-ssm-agent`

### NACLs vs Security Groups

- **NACLs** are stateless (need explicit inbound AND outbound rules)
- **Security groups** are stateful (return traffic automatically allowed)
- NACLs are evaluated first, then security groups
- A DENY in NACLs overrides any security group ALLOW

### External Port Scan Shows "Filtered"

The external connectivity test runs from GitHub Actions runners. "Filtered" may mean:
- Security group doesn't allow the port from GitHub's IP ranges
- NACL blocks the port
- No internet gateway / public IP
- This is expected for non-public services — use SSM-based checks instead
