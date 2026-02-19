# SCIM Server Auto-Update at Boot

## Problem

The SCIM server (`scim2-mysql-app.py`) runs on an EC2 instance at `/opt/scim-server/`. When we update the file in the repo, we have to manually deploy it via SSM. If the instance reboots, it runs the stale version already on disk.

## Proposed Solution: S3 Pull at Boot

The instance already has an IAM role with AWS access. Add a step to the startup script that pulls the latest SCIM server file from S3 before launching the process.

### How It Works

1. CI (GitHub Actions) uploads `scim2-mysql-app.py` to S3 on push to `main`
2. EC2 startup script pulls from S3 before launching the server
3. Server always runs the latest committed version

### Implementation Steps

#### 1. New GitHub Actions workflow: `deploy-scim-code.yml`

Triggers on push to `main` when `hr-source/scim2-mysql-app.py` changes. Uploads the file to S3:

```yaml
- name: Upload SCIM server to S3
  run: |
    aws s3 cp hr-source/scim2-mysql-app.py \
      s3://${BUCKET}/scim-server/scim2-mysql-app.py
```

#### 2. Update EC2 userdata / systemd service

Add a pre-start step that pulls from S3:

```bash
#!/bin/bash
# /opt/scim-server/start.sh

# Pull latest from S3
aws s3 cp s3://${BUCKET}/scim-server/scim2-mysql-app.py \
  /opt/scim-server/scim2-mysql-app.py

# Start the server
cd /opt/scim-server
exec python3 scim2-mysql-app.py
```

Create a systemd unit so it auto-starts and restarts on failure:

```ini
# /etc/systemd/system/scim-server.service
[Unit]
Description=SCIM 2.0 Server
After=network.target

[Service]
Type=simple
ExecStart=/opt/scim-server/start.sh
Restart=on-failure
RestartSec=5
WorkingDirectory=/opt/scim-server

[Install]
WantedBy=multi-user.target
```

#### 3. S3 bucket path

Use the existing infrastructure bucket or create a dedicated path:
```
s3://<bucket>/scim-server/scim2-mysql-app.py
```

#### 4. IAM permissions

Ensure the EC2 instance role has `s3:GetObject` on the SCIM server path. (Likely already covered by existing permissions.)

### Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| **S3 pull (recommended)** | Simple, instance already has AWS access, works offline from GitHub | Extra S3 upload step in CI |
| Git clone at boot | Always latest from repo | Needs GitHub auth on instance, slower |
| CodeDeploy | Full deployment pipeline | Overkill for a single file |
| Bake into AMI | Immutable infrastructure | Slow iteration, needs AMI rebuild per change |

### Side Benefits

- Systemd service means the server auto-restarts on crash
- S3 versioning gives rollback capability
- Could extend to pull config/env files too
