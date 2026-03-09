# ITP (Identity Threat Protection) Demo Guide

Complete guide to the ITP demo automation module for Okta Identity Threat Protection demonstrations.

---

## Overview

This module provides three ways to trigger Okta ITP risk events for demos, each producing a different system log entry:

| Mode | System Log Entry | Infrastructure | Realism |
|------|-----------------|----------------|---------|
| **Quick** (`--mode quick`) | "Admin reported user risk" | None | Low — admin API call |
| **Real** (`--mode real`) | "Session hijacking detected" | Lambda + Playwright | High — genuine detection |
| **SSF** (`--mode ssf`) | "Security events provider reported risk" | Lambda (JWKS) + SSM | Medium-High — signed JWT signal |

All three modes support `--monitor` (watch system log for ITP events), `--auto-reset` (reset risk after demo), and work with the entity risk policy to trigger downstream actions (session revocation, MFA challenges, etc.).

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    trigger_itp_demo.py                    │
│         (Main orchestrator — all three modes)            │
├──────────┬──────────────────┬────────────────────────────┤
│          │                  │                            │
│  Quick   │      Real        │          SSF               │
│  Mode    │      Mode        │          Mode              │
│          │                  │                            │
│ PUT      │ ┌──────────────┐ │ ┌────────────────────────┐ │
│ /users/  │ │ session_     │ │ │ ssf_provider.py        │ │
│ {id}/    │ │ authenticator│ │ │                        │ │
│ risk     │ │ (Playwright) │ │ │ 1. Load config from SSM│ │
│          │ ├──────────────┤ │ │ 2. Build SET JWT       │ │
│          │ │ session_     │ │ │ 3. Sign with RS256     │ │
│          │ │ replayer     │ │ │ 4. POST to /security/  │ │
│          │ │ (Lambda/     │ │ │    api/v1/security-    │ │
│          │ │  direct)     │ │ │    events              │ │
│          │ └──────────────┘ │ └────────────────────────┘ │
├──────────┴──────────────────┴────────────────────────────┤
│                  monitor_itp_events.py                    │
│            (Watches system log for ITP events)            │
└──────────────────────────────────────────────────────────┘
```

### SSF Infrastructure (Terraform-managed)

```
┌─────────────────────────────────────────────────────┐
│  AWS                                                │
│                                                     │
│  ┌─────────────┐   ┌─────────────────────────────┐  │
│  │ Lambda      │   │ SSM Parameter Store          │  │
│  │ {env}-ssf-  │   │                             │  │
│  │ jwks        │   │ /{env}/itp/ssf-demo/        │  │
│  │             │   │   ├── private-key (Secure)  │  │
│  │ Returns     │   │   └── provider-config (JSON)│  │
│  │ JWKS JSON   │   │       ├── issuer            │  │
│  └──────┬──────┘   │       ├── jwks_url          │  │
│  ┌──────┴──────┐   │       ├── key_id            │  │
│  │ Function    │   │       └── provider_id       │  │
│  │ URL (public)│   └─────────────────────────────┘  │
│  └─────────────┘                                    │
│       ↑                                             │
└───────│─────────────────────────────────────────────┘
        │
   Okta fetches JWKS
   to verify SET signatures
```

---

## Prerequisites

- **Okta org** with ITP license (Identity Threat Protection)
- **Entity risk policy** configured (import/apply via scripts)
- **AWS account** with Lambda + SSM access (for real and SSF modes)
- **GitHub Environment** with secrets: `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`, `AWS_ROLE_ARN`
- **Python 3.11+** with `requests`, `pyjwt`, `cryptography`, `boto3`, `pyotp`

---

## File Reference

### Core Scripts

| File | Purpose |
|------|---------|
| `scripts/trigger_itp_demo.py` | Main orchestrator — CLI entry point for all three modes |
| `scripts/itp/ssf_provider.py` | SSF provider: key generation, SET building/signing, signal sending |
| `scripts/itp/session_authenticator.py` | Headless browser auth via Playwright (real mode) |
| `scripts/itp/session_replayer.py` | Cookie replay from different context (real mode) |
| `scripts/monitor_itp_events.py` | System log watcher for ITP events |
| `scripts/setup_ssf_provider.py` | Post-Terraform Okta provider registration |
| `scripts/helpers/pem_to_jwks.py` | PEM-to-JWKS converter (Terraform external data source) |

### Entity Risk Policy Scripts

| File | Purpose |
|------|---------|
| `scripts/import_entity_risk_policy.py` | Import entity risk policy config from Okta |
| `scripts/apply_entity_risk_policy.py` | Apply entity risk policy config to Okta |
| `environments/{env}/config/entity_risk_policy.json` | Policy config (rules, actions) |

### Terraform Module

| File | Purpose |
|------|---------|
| `modules/itp-demo/main.tf` | Lambda for cross-region cookie replay (real mode) |
| `modules/itp-demo/ssf_jwks.tf` | Lambda JWKS endpoint + RSA key + SSM (SSF mode) |
| `modules/itp-demo/video_bucket.tf` | S3 bucket for demo video storage |
| `modules/itp-demo/variables.tf` | All module inputs with feature flags |
| `modules/itp-demo/outputs.tf` | Module outputs (conditional on feature flags) |
| `modules/itp-demo/lambda/replayer.py` | Lambda handler for session replay |
| `modules/itp-demo/scripts/pem_to_jwks.py` | PEM to JWKS converter for Terraform |

### GitHub Workflows

| File | Purpose |
|------|---------|
| `.github/workflows/itp-demo-trigger.yml` | Run any demo mode (quick/real/ssf) |
| `.github/workflows/itp-ssf-provider-setup.yml` | One-time Okta provider registration |
| `.github/workflows/itp-entity-risk-policy-import.yml` | Import entity risk policy |
| `.github/workflows/itp-entity-risk-policy-apply.yml` | Apply entity risk policy |
| `.github/workflows/itp-monitor-events.yml` | Standalone event monitoring |

---

## Setup

### Quick Mode Setup

No infrastructure needed. Works immediately with just Okta API credentials.

### Real Mode Setup

1. **Enable the Terraform module** in your environment:
   ```bash
   # Copy example file and uncomment
   cp environments/myorg/terraform/itp_demo.tf.example \
      environments/myorg/terraform/itp_demo.tf
   # Edit to enable: enable_session_replayer = true
   ```

2. **Deploy attacker Lambda** (cross-region cookie replay):
   ```bash
   # Via GitHub Actions
   gh workflow run tf-apply.yml -f environment=myorg

   # This creates a Lambda function ({env}-itp-session-replayer) in eu-west-1
   ```

3. **Create test user** in Okta:
   - Create user with your org's email domain
   - Enroll TOTP factor with provider **OKTA** (not GOOGLE) — Okta Verify TOTP
   - Save the TOTP seed (base32 secret) for SSM storage

4. **Store victim credentials** in SSM:
   ```bash
   aws ssm put-parameter \
     --name /{environment}/itp/password \
     --value "USER_PASSWORD" --type SecureString

   aws ssm put-parameter \
     --name /{environment}/itp/totp-secret \
     --value "TOTP_BASE32_SECRET" --type SecureString
   ```

5. **Install Playwright and dependencies** (for headless browser):
   ```bash
   pip install playwright pyotp
   playwright install chromium
   playwright install-deps chromium  # system dependencies (libgbm, etc.)
   ```

### SSF Mode Setup

Two-step process — Terraform for infrastructure, then register with Okta:

**Step 1: Deploy infrastructure (Terraform)**

```bash
# Enable SSF in your Terraform module:
# enable_ssf_endpoint = true

# Via GitHub Actions (recommended)
gh workflow run tf-apply.yml -f environment=myorg

# This creates:
#   - Lambda function ({env}-ssf-jwks) serving JWKS
#   - Lambda Function URL (public endpoint)
#   - RSA key pair (tls_private_key)
#   - SSM: /{env}/itp/ssf-demo/private-key
#   - SSM: /{env}/itp/ssf-demo/provider-config
```

**Step 2: Register provider with Okta**

```bash
# Via GitHub Actions
gh workflow run itp-ssf-provider-setup.yml -f environment=myorg

# Or locally
export OKTA_ORG_NAME=myorg
export OKTA_API_TOKEN=<your-api-token>
cd scripts && python3 setup_ssf_provider.py \
  --ssm-prefix /myorg/itp/ssf-demo \
  --aws-region us-east-1
```

**Verify:** Check Okta Admin > Security > Security Events Providers — you should see "ITP Demo Signal Source".

### Video Recording Setup (Optional)

Enable the video bucket in your Terraform module:

```hcl
module "itp_demo" {
  source = "../../modules/itp-demo"
  # ...
  enable_video_bucket     = true
  github_actions_role_arn = "arn:aws:iam::123456789012:role/GitHubActions"
}
```

---

## Usage

### Quick Mode

Directly sets user risk via admin API. Instant, no infrastructure.

```bash
# Set user risk to HIGH and monitor
python3 scripts/trigger_itp_demo.py --mode quick \
  --user user@example.com \
  --risk-level HIGH --monitor --auto-reset

# Reset risk to LOW
python3 scripts/trigger_itp_demo.py --mode quick \
  --user user@example.com --risk-level LOW
```

**What happens:**
1. Resolves user by email
2. `PUT /api/v1/users/{id}/risk` with `{"riskLevel": "HIGH"}`
3. System log: "Admin reported user risk"
4. Entity risk policy evaluates
5. (If `--auto-reset`) Resets to LOW

### Real Mode

Two-region session hijacking simulation. Genuine Okta detection.

```bash
# Full simulation with Lambda
python3 scripts/trigger_itp_demo.py --mode real \
  --user itp-demo-test@example.com \
  --ssm-prefix /myorg/itp \
  --attacker-lambda myorg-itp-session-replayer \
  --attacker-region eu-west-1 \
  --monitor --auto-reset

# With video recording + S3 upload
python3 scripts/trigger_itp_demo.py --mode real \
  --user itp-demo-test@example.com \
  --ssm-prefix /myorg/itp \
  --attacker-lambda myorg-itp-session-replayer \
  --record-video /tmp/itp-video \
  --upload-s3 myorg-itp-demo-videos \
  --monitor --auto-reset
```

**What happens:**
1. **Step 1 — Victim auth:** Playwright headless browser authenticates as user (username -> password -> TOTP), captures IDX cookie (macOS Chrome UA)
2. **Step 2 — Attacker uses stolen cookie (with `--record-video`):** A second browser (Windows/Firefox UA) opens, the stolen cookie is injected via `add_cookies()`, and it navigates straight to the Okta dashboard — no credentials, no MFA
3. **Step 3 — Geo-separated replay:** Lambda in eu-west-1 replays cookie (triggers Okta's geo-anomaly detection)
4. **Step 4 — ULO in browser (with `--record-video`):** Both browsers reload every 5s, watching for session termination. When Okta fires ULO, the victim's reload redirects to login — captured in the video
5. **Full event chain observed in system log:**
   1. `user.risk.detect` — risk detected from attacker IP (e.g., Dublin)
   2. `policy.entity_risk.evaluate` — Entity Risk Policy rule matched
   3. `policy.entity_risk.action` — TERMINATE_ALL_SESSIONS scheduled
   4. `user.session.end` — session terminated
   5. `user.authentication.universal_logout` — universal logout issued
6. (If `--auto-reset`) Risk auto-resets to LOW

### SSF Mode

Sends a Shared Signals Framework security event via signed JWT.

```bash
# Send HIGH risk signal
python3 scripts/trigger_itp_demo.py --mode ssf \
  --user user@example.com \
  --risk-level HIGH \
  --ssm-prefix /myorg/itp \
  --monitor --auto-reset
```

**What happens:**
1. Resolves user by email (validates they exist)
2. Loads provider config + private key from SSM
3. Builds Security Event Token (SET) with `user-risk-change` event
4. Signs JWT with RS256 (`typ: secevent+jwt`)
5. `POST /security/api/v1/security-events` (self-authenticating via JWT signature)
6. System log: "Security events provider reported risk"
7. Entity risk policy evaluates
8. (If `--auto-reset`) Sends LOW signal to reset

### GitHub Actions

```bash
# Quick mode
gh workflow run itp-demo-trigger.yml \
  -f environment=myorg \
  -f mode=quick \
  -f user_email=user@example.com \
  -f risk_level=HIGH

# Real mode
gh workflow run itp-demo-trigger.yml \
  -f environment=myorg \
  -f mode=real \
  -f user_email=itp-demo-test@example.com \
  -f attacker_region=eu-west-1

# SSF mode
gh workflow run itp-demo-trigger.yml \
  -f environment=myorg \
  -f mode=ssf \
  -f user_email=user@example.com \
  -f ssf_risk_level=HIGH
```

---

## Entity Risk Policy Management

Entity risk policies define what actions Okta takes when a user's risk level changes (from any trigger — admin API, session hijacking, or SSF signal).

### Import

```bash
# Via workflow
gh workflow run itp-entity-risk-policy-import.yml -f environment=myorg

# Via CLI
python3 scripts/import_entity_risk_policy.py \
  --output environments/myorg/config/entity_risk_policy.json
```

### Apply

```bash
# Dry run first
gh workflow run itp-entity-risk-policy-apply.yml \
  -f environment=myorg -f dry_run=true

# Apply
gh workflow run itp-entity-risk-policy-apply.yml \
  -f environment=myorg -f dry_run=false
```

### Configuration Format

```json
{
  "policy_id": "rst1yr8u11qDt6moD1d8",
  "policy_name": "Entity Risk Policy",
  "rules": [
    {
      "name": "High Risk Response",
      "conditions": {
        "riskLevel": "HIGH"
      },
      "actions": {
        "terminateSessions": true,
        "challengeWithMFA": true
      }
    }
  ]
}
```

---

## How SSF Works (Technical Details)

### Security Event Token (SET)

A SET is a JWT with `typ: secevent+jwt` containing a security event per RFC 8417. The payload structure:

```json
{
  "iss": "https://xxxx.lambda-url.us-east-1.on.aws/",
  "jti": "unique-uuid",
  "iat": 1709654321,
  "aud": "https://{org_name}.okta.com",
  "events": {
    "https://schemas.okta.com/secevent/okta/event-type/user-risk-change": {
      "subject": {
        "user": {
          "format": "email",
          "email": "user@example.com"
        }
      },
      "event_timestamp": 1709654321,
      "initiating_entity": "admin",
      "reason_admin": {
        "en": "Critical security activity detected"
      },
      "current_level": "high",
      "previous_level": "low"
    }
  }
}
```

### Verification Flow

1. Python builds SET payload and signs with RS256 using private key from SSM
2. `POST /security/api/v1/security-events` with `Content-Type: application/secevent+jwt`
3. Okta reads `iss` claim, finds matching registered provider
4. Okta fetches JWKS from the provider's registered `jwks_url` (our Lambda Function URL)
5. Okta verifies JWT signature using the public key from JWKS
6. If valid, Okta processes the risk event and updates the user's entity risk score

### Key Details

- The security events endpoint is **self-authenticating** — no SSWS token needed for the POST
- SSWS token is only needed for provider registration (`POST /api/v1/security-events-providers`)
- The `issuer` registered with Okta must exactly match the `iss` claim in the SET
- Okta accepts `200` or `202` status codes on success
- The Lambda Function URL serves JWKS with `Cache-Control: public, max-age=3600`

---

## Video Recording & S3 Upload

When `--record-video` and `--upload-s3` are both set, the demo records **two browsers simultaneously** — victim and attacker — capturing the full session hijacking story:

**Victim browser** (Chrome/Mac UA):
1. Login flow — user enters credentials, completes MFA, lands on dashboard
2. Dashboard idle — stays open while attacker activity happens
3. Session terminated — page reload redirects to login (ULO kicks in)

**Attacker browser** (Firefox/Windows UA):
1. Stolen cookie injected via `add_cookies()` — no login page
2. Navigates to Okta dashboard — lands directly, no credentials needed
3. Stays open showing the attacker's view of the hijacked session

Both browsers reload every 5s watching for session termination. When Okta's entity risk policy fires `TERMINATE_ALL_SESSIONS` (Universal Logout), the victim's session is revoked and the next reload redirects to the login page.

**S3 upload details:**
- Two `.webm` files uploaded (victim + attacker)
- S3 key format: `{date}/{user}_{timestamp}_{filename}.webm`
- A presigned URL (valid 7 days) is printed for each video
- Upload happens AFTER both browsers close (videos aren't finalized until then)

The S3 bucket (`{env}-itp-demo-videos`) is managed by the Terraform module with:
- Configurable auto-expiration (default 90 days)
- AES256 encryption
- Public access blocked
- GitHub Actions OIDC role has write access (when configured)

---

## Event Monitoring

The `monitor_itp_events.py` script watches the system log for ITP-related events:

```bash
# Standalone monitoring
python3 scripts/monitor_itp_events.py \
  --duration 120 --user user@example.com

# Via workflow
gh workflow run itp-monitor-events.yml \
  -f environment=myorg \
  -f user_filter=user@example.com \
  -f duration_seconds=120
```

Events watched:
- `user.risk.detect` — Risk detected (session hijacking, admin API, SSF signal)
- `policy.entity_risk.evaluate` — Entity risk policy rule evaluated
- `policy.entity_risk.action` — Entity risk policy action taken (e.g., TERMINATE_ALL_SESSIONS)
- `user.session.end` — Session terminated (policy action)
- `user.authentication.universal_logout` — Universal logout issued

---

## Demo Recommendations

### For Sales Engineers

**Best demo flow:**
1. Show the entity risk policy in Okta Admin (what actions are configured)
2. Run SSF mode (`--mode ssf`) — most realistic, shows "Security events provider reported risk"
3. Show system log updating in real-time
4. Show entity risk policy evaluating and taking action
5. Reset with `--auto-reset`

**Why SSF over Quick:**
- "Security events provider reported risk" sounds like CrowdStrike/Zscaler/etc. detected a threat
- "Admin reported user risk" sounds like someone clicked a button manually
- SSF mode takes the same 2 seconds but creates a much better story

### For Deep Demos

Use Real mode (`--mode real`) to show genuine session hijacking detection — this demonstrates Okta's actual threat detection engine, not just policy evaluation from an external signal.

---

## CLI Reference

### Common Options (All Modes)

| Flag | Description |
|------|-------------|
| `--mode` | Demo mode: `quick`, `real`, or `ssf` |
| `--user` | Target user email |
| `--monitor` | Watch system log for ITP events after trigger |
| `--monitor-duration` | Event monitoring duration in seconds (default: 60) |
| `--auto-reset` | Reset user risk to LOW after demo |
| `--ssm-prefix` | SSM path prefix (e.g., `/{env}/itp`) — auto-derives credential paths |

### Real Mode Options

| Flag | Description |
|------|-------------|
| `--password` | User password (or `ITP_DEMO_PASSWORD` env var) |
| `--password-ssm` | SSM parameter name for password |
| `--totp-secret` | TOTP secret (or `ITP_DEMO_TOTP_SECRET` env var) |
| `--totp-ssm` | SSM parameter name for TOTP secret |
| `--attacker-region` | AWS region for attacker Lambda (default: `eu-west-1`) |
| `--attacker-lambda` | Lambda function name for cookie replay |
| `--record-video DIR` | Record browser session video to directory |
| `--upload-s3 BUCKET` | Upload recorded video to S3 bucket (requires `--record-video`) |
| `--aws-profile` | AWS profile for SSM, Lambda, and S3 access |

### SSF Mode Options

| Flag | Description |
|------|-------------|
| `--risk-level` | Risk level: `HIGH` or `LOW` |
| `--ssf-config-ssm` | SSM path for provider config (auto-derived from `--ssm-prefix`) |
| `--private-key-ssm` | SSM path for private key (auto-derived from `--ssm-prefix`) |

---

## Troubleshooting

### SSF Signal Returns 400 "Invalid JWT"
- Verify the JWKS URL is accessible: `curl <function_url>`
- Ensure the `kid` in the JWT header matches the `kid` in JWKS
- Check that the `iss` claim matches the registered provider's issuer

### SSF Signal Returns 400 "Provider not found"
- Run `python3 scripts/setup_ssf_provider.py --list` to verify registration
- Ensure `iss` in JWT matches the registered issuer exactly (including trailing slash)

### SSF Signal Returns 403
- Verify the org has ITP/security events feature enabled
- Check that the API token has sufficient permissions

### Lambda JWKS URL Not Accessible
- Check Lambda Function URL exists: `aws lambda get-function-url-config --function-name {env}-ssf-jwks`
- Verify the function returns valid JSON: `curl <function_url>`

### Terraform Plan Shows Drift on provider-config SSM
- Expected — the `lifecycle { ignore_changes = [value] }` on the SSM parameter means Terraform won't overwrite the provider_id added by the setup script

### Real Mode Auth Fails
- Check password/TOTP in SSM are current
- Verify Playwright chromium is installed: `playwright install chromium`
- Install system dependencies: `playwright install-deps chromium`
- Check if user has additional MFA factors beyond TOTP
- **OIE TOTP field**: The password input uses `credentials.passcode`, but the TOTP input uses `credentials.totp` — these are different fields in OIE. The authenticator handles both automatically.
- **TOTP provider**: Must be OKTA (Okta Verify TOTP), not GOOGLE. The OIE authenticator selector looks for `[data-se="okta_verify-totp"]`.
- **TOTP timing**: If TOTP fails with "invalid passcode", the code may have expired during the authentication flow. Retry usually works.
- **Screenshot debugging**: On auth failure, a screenshot is saved to `/tmp/itp-auth-failure.png`

---

## AWS Requirements

See [ITP AWS Requirements](../infrastructure/itp-aws-requirements.md) for detailed AWS setup including IAM policies, cross-region deployment, and SSM parameter layout.
