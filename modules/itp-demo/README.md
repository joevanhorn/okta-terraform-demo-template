# ITP Demo Module

Terraform module for Okta Identity Threat Protection (ITP) demo automation. Deploys AWS infrastructure for three demo modes: Quick (no infra), SSF (signed JWT signals), and Real (session hijacking simulation).

---

## Files in This Module

| File | Purpose |
|------|---------|
| [`main.tf`](main.tf) | Session Replayer Lambda — cross-region cookie replay (real mode) |
| [`ssf_jwks.tf`](ssf_jwks.tf) | SSF JWKS Lambda — public key endpoint + RSA key + SSM parameters (SSF mode) |
| [`video_bucket.tf`](video_bucket.tf) | S3 bucket for demo video recordings (optional) |
| [`variables.tf`](variables.tf) | Module inputs — environment name, feature flags, regions, tags |
| [`outputs.tf`](outputs.tf) | Module outputs — Lambda names/ARNs, JWKS URL, S3 bucket |
| [`lambda/replayer.py`](lambda/replayer.py) | Lambda handler for cross-region cookie replay |
| [`scripts/pem_to_jwks.py`](scripts/pem_to_jwks.py) | PEM-to-JWKS converter (Terraform external data source) |

---

## Related Files

### Documentation

| File | Purpose |
|------|---------|
| [`docs/itp-demo.md`](docs/itp-demo.md) | Complete ITP demo guide — architecture, setup, usage, troubleshooting |
| [`docs/itp-demo-prerequisites.md`](docs/itp-demo-prerequisites.md) | Prerequisites checklist by mode, secrets inventory, verification commands |
| [`docs/itp-aws-requirements.md`](docs/itp-aws-requirements.md) | AWS IAM policies, cross-region deployment, SSM layout, cost estimates |
| [`docs/deploy_itp_demo.md`](docs/deploy_itp_demo.md) | Claude Code deployment prompt — paste into Claude Code to deploy end-to-end |

### Scripts

| File | Purpose |
|------|---------|
| [`scripts/trigger_itp_demo.py`](scripts/trigger_itp_demo.py) | Main CLI — orchestrates all three demo modes |
| [`scripts/setup_ssf_provider.py`](scripts/setup_ssf_provider.py) | Registers SSF provider with Okta (post-Terraform) |
| [`scripts/monitor_itp_events.py`](scripts/monitor_itp_events.py) | Real-time system log watcher for ITP events |
| [`scripts/import_entity_risk_policy.py`](scripts/import_entity_risk_policy.py) | Imports entity risk policy from Okta to JSON |
| [`scripts/apply_entity_risk_policy.py`](scripts/apply_entity_risk_policy.py) | Applies entity risk policy rules to Okta |
| [`scripts/itp/session_authenticator.py`](scripts/itp/session_authenticator.py) | Headless browser authentication via Playwright (real mode) |
| [`scripts/itp/session_replayer.py`](scripts/itp/session_replayer.py) | Cookie replay from local context (real mode) |
| [`scripts/itp/ssf_provider.py`](scripts/itp/ssf_provider.py) | SSF provider registration and SET signal sending |

### GitHub Actions Workflows

| File | Purpose |
|------|---------|
| [`.github/workflows/itp-demo-trigger.yml`](../../.github/workflows/itp-demo-trigger.yml) | Run any demo mode (quick/real/ssf) |
| [`.github/workflows/itp-ssf-provider-setup.yml`](../../.github/workflows/itp-ssf-provider-setup.yml) | One-time SSF provider registration with Okta |
| [`.github/workflows/itp-entity-risk-policy-import.yml`](../../.github/workflows/itp-entity-risk-policy-import.yml) | Import entity risk policy from Okta |
| [`.github/workflows/itp-entity-risk-policy-apply.yml`](../../.github/workflows/itp-entity-risk-policy-apply.yml) | Apply entity risk policy to Okta |
| [`.github/workflows/itp-monitor-events.yml`](../../.github/workflows/itp-monitor-events.yml) | Standalone ITP event monitoring |

### Example Configuration

| File | Purpose |
|------|---------|
| [`examples/itp_demo.tf.example`](examples/itp_demo.tf.example) | Example Terraform config — copy and customize for your environment |

---

## Quick Start

1. **Check prerequisites:** [`docs/itp-demo-prerequisites.md`](docs/itp-demo-prerequisites.md)
2. **Deploy with Claude Code:** [`docs/deploy_itp_demo.md`](docs/deploy_itp_demo.md)
3. **Or deploy manually:** [`docs/itp-demo.md`](docs/itp-demo.md)
