# ITP Demo — Prerequisites Checklist

Everything that must be true before Claude Code (or any automation) can deploy the ITP demo. Organized by demo mode so you know exactly what's needed for your chosen scope.

For architecture, usage details, and troubleshooting, see [ITP Demo Guide](itp-demo.md).

---

## Quick Reference: What Each Mode Needs

| Prerequisite | Quick | SSF | Real | Claude Code Can Help? |
|-------------|:-----:|:---:|:----:|:---------------------:|
| Okta org with ITP license | Yes | Yes | Yes | No (Okta admin) |
| Okta API token (Super Admin) | Yes | Yes | Yes | No (manual, one-time) |
| AWS backend (S3 + DynamoDB + OIDC) | Yes | Yes | Yes | Yes (Terraform) |
| GitHub Environment + secrets | Yes | Yes | Yes | Yes (`gh` CLI) |
| Entity risk policy in org | Yes | Yes | Yes | Yes (scripts) |
| Python 3.11+ | Yes | Yes | Yes | No (system install) |
| Forked & cloned this repo | Yes | Yes | Yes | No (manual) |
| AWS IAM role with ITP permissions | — | Yes | Yes | Yes (IAM policy) |
| `AWS_ROLE_ARN` GitHub secret | — | Yes | Yes | Yes (`gh secret set`) |
| Dedicated test user in Okta | — | — | Yes | Yes (Okta API) |
| TOTP enrollment + seed capture | — | — | Yes | Yes (Okta API) |
| Playwright + chromium | — | — | Yes | Yes (`pip install`) |

---

## Complete Secrets & Credentials Inventory

Every secret and credential needed across all modes, in one place.

### GitHub Environment Secrets (required for all modes)

Set these on your GitHub Environment (environment name must match your directory name):

| Secret | Required For | Value | How to Create |
|--------|-------------|-------|---------------|
| `OKTA_API_TOKEN` | All modes | Okta API token (Super Admin) | Admin Console > Security > API > Tokens |
| `OKTA_ORG_NAME` | All modes | Org subdomain (e.g., `mycompany`) | From your Okta URL |
| `OKTA_BASE_URL` | All modes | `okta.com` or `oktapreview.com` | From your Okta URL |
| `AWS_ROLE_ARN` | SSF + Real | IAM role ARN for GitHub OIDC | Created by `aws-backend/` Terraform |

**Claude Code can help:** If you have the values ready, Claude Code can create the GitHub Environment and set secrets using `gh api` and `gh secret set`.

### SSM Parameters (created during deployment)

These are created as part of the deployment process — you don't need to create them beforehand:

| Parameter | Type | Created By | Required For |
|-----------|------|-----------|-------------|
| `/{env}/itp/ssf-demo/private-key` | SecureString | Terraform | SSF mode |
| `/{env}/itp/ssf-demo/provider-config` | String | Terraform + setup script | SSF mode |
| `/{env}/itp/password` | SecureString | Manual (Claude Code helps) | Real mode |
| `/{env}/itp/totp-secret` | SecureString | Manual (Claude Code helps) | Real mode |

### AWS Backend (first-time setup only)

If this is your first environment, you need the Terraform state backend:

| Resource | Purpose | Created By |
|----------|---------|-----------|
| S3 bucket | Terraform state storage | `aws-backend/` Terraform |
| DynamoDB table | State locking | `aws-backend/` Terraform |
| IAM OIDC provider | GitHub Actions authentication | `aws-backend/` Terraform |
| IAM role | GitHub Actions permissions | `aws-backend/` Terraform |

See [AWS Backend Setup](../getting-started/aws-backend.md) for instructions. The `aws-backend/` directory in the repo has Terraform to create all of these at once.

---

## All Modes (Required)

These prerequisites apply regardless of which demo mode you use.

### Okta Organization

- [ ] **Okta org with ITP license enabled**
  - Identity Threat Protection must be activated on the org
  - Verify: Admin Console > Security > Identity Threat Protection should be accessible
  - The entity risk policy is auto-created by Okta when ITP is enabled

- [ ] **Entity risk policy exists**
  - Okta creates this automatically when ITP is enabled
  - Verify via API:
    ```bash
    curl -s -H "Authorization: SSWS $OKTA_API_TOKEN" \
      "https://$OKTA_ORG_NAME.okta.com/api/v1/policies?type=ENTITY_RISK" | python3 -m json.tool
    ```
  - You should see at least one policy. If no rules are configured, Claude Code can create them during deployment using the entity risk policy scripts.

### Okta API Token

- [ ] **Super Admin API token created**
  - Admin Console > Security > API > Tokens > Create Token
  - Must be created by a Super Admin user
  - This is the one thing that **must be done manually** in the Okta Admin UI — the token is only displayed once at creation time

### GitHub Environment

- [ ] **GitHub Environment created** with secrets set

  | Secret | Value | Example |
  |--------|-------|---------|
  | `OKTA_API_TOKEN` | Your Okta API token | `00abc123...` |
  | `OKTA_ORG_NAME` | Org subdomain | `mycompany` |
  | `OKTA_BASE_URL` | Base URL | `okta.com` (or `oktapreview.com`) |

  The environment name must match your directory name (e.g., environment `myorg` for `environments/myorg/`).

  **Claude Code can help:** Create the environment and set secrets:
  ```bash
  # Create GitHub Environment
  gh api repos/{owner}/{repo}/environments/{env_name} -X PUT

  # Set secrets (gh will prompt for values securely)
  gh secret set OKTA_API_TOKEN --env {env_name}
  gh secret set OKTA_ORG_NAME --env {env_name}
  gh secret set OKTA_BASE_URL --env {env_name}
  ```

### AWS Backend (First-Time Setup)

- [ ] **S3 backend and IAM OIDC role exist**
  - If you've already deployed other environments from this repo, this is already done
  - If this is your first environment, deploy the backend infrastructure:
    ```bash
    cd aws-backend
    # Update variables.tf: set state_bucket_name and github_repository
    terraform init && terraform plan
    terraform apply
    # Note the outputs — AWS_ROLE_ARN goes into GitHub secrets
    ```
  - **Claude Code can help:** Claude Code can update `aws-backend/variables.tf` with your repo name and bucket name, then run the Terraform. The IAM role ARN from the output becomes your `AWS_ROLE_ARN` secret.
  - See [AWS Backend Setup](../getting-started/aws-backend.md) for the full guide.

### Local Tools

- [ ] **Python 3.11+** available
  - Verify: `python3 --version`
  - Required packages: `pip install requests pyjwt cryptography boto3 pyotp`
  - Or: `pip install -r requirements.txt` from repo root

- [ ] **Repository forked and cloned**
  - `gh repo fork <template-repo> --clone`
  - Or fork via GitHub UI and `git clone`

---

## Quick Mode — No Additional Prerequisites

Quick mode works with just the base prerequisites above. It calls the Okta admin API directly to set user risk — no AWS infrastructure, no test user, no browser automation.

**What it does:** `PUT /api/v1/users/{id}/risk` with `{"riskLevel": "HIGH"}`

**System log entry:** "Admin reported user risk"

You can run Quick mode immediately after completing the base prerequisites.

---

## SSF Mode — Additional Prerequisites

SSF mode sends a signed JWT (Security Event Token) to Okta's security events API, simulating a third-party security provider reporting risk. This requires AWS infrastructure for the JWKS endpoint and secret storage.

### AWS Account

- [ ] **AWS account** with permissions to deploy:
  - Lambda functions (2 regions if also using Real mode)
  - SSM Parameter Store parameters
  - IAM roles for Lambda execution
  - CloudWatch log groups

- [ ] **IAM role for Terraform deployment** (with ITP-specific permissions)
  - Needs Lambda, IAM, SSM, and CloudWatch Logs permissions
  - Scoped IAM policy: see [ITP AWS Requirements](../infrastructure/itp-aws-requirements.md#terraform-deployment-role)
  - **Note:** If you deployed `aws-backend/`, the `GitHubActions-OktaTerraform` role needs the ITP permissions added. Claude Code can help attach the additional policy.

### GitHub Actions OIDC

- [ ] **`AWS_ROLE_ARN` secret** in GitHub Environment
  - This is the role ARN from `aws-backend/` Terraform output
  - Role must trust your GitHub repository via OIDC federation
  - Role needs runtime permissions: SSM read, Lambda invoke
  - Runtime IAM policy: see [ITP AWS Requirements](../infrastructure/itp-aws-requirements.md#github-actions-runtime-role)

  **Claude Code can help:** Set the secret if you have the ARN:
  ```bash
  gh secret set AWS_ROLE_ARN --env {env_name} --body "arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform"
  ```

### Alternative: Local AWS Access

If not using GitHub Actions workflows, you can run SSF setup locally:

- [ ] **AWS CLI configured** with sufficient permissions
  - Verify: `aws sts get-caller-identity`
  - Needs: `ssm:GetParameter`, `ssm:PutParameter`, `lambda:InvokeFunction`

---

## Real Mode — Additional Prerequisites

Real mode performs an actual session hijacking simulation using headless browser authentication and cross-region cookie replay. This requires a dedicated test user and browser automation tools.

### Dedicated Test User

- [ ] **Test user created in Okta**
  - Must be an active user with a known password
  - Use a dedicated demo/test account — not a real user
  - Email domain should match your org

  **Claude Code can help:** Create the test user via Okta API:
  ```bash
  curl -s -X POST \
    -H "Authorization: SSWS $OKTA_API_TOKEN" \
    -H "Content-Type: application/json" \
    "https://$OKTA_ORG_NAME.okta.com/api/v1/users?activate=true" \
    -d '{
      "profile": {
        "firstName": "ITP", "lastName": "Demo Test",
        "email": "itp-test@example.com", "login": "itp-test@example.com"
      },
      "credentials": {
        "password": {"value": "YourSecurePassword123!"}
      }
    }'
  ```

- [ ] **Okta Verify TOTP enrolled** on the test user
  - **Provider must be OKTA** (Okta Verify TOTP), NOT GOOGLE
  - The automation looks for `[data-se="okta_verify-totp"]` in the OIE login flow
  - Must NOT have other MFA factors that would interrupt the flow (e.g., push notifications, security keys)

  **Claude Code can help:** Enroll TOTP factor via API and capture the seed automatically.

- [ ] **TOTP seed (base32 secret) saved**
  - You need the shared secret from TOTP enrollment
  - **Tip:** Enroll TOTP programmatically via Okta API to capture the seed:
    ```bash
    # Step 1: Enroll TOTP factor (returns sharedSecret in response)
    curl -s -X POST \
      -H "Authorization: SSWS $OKTA_API_TOKEN" \
      -H "Content-Type: application/json" \
      "https://$OKTA_ORG_NAME.okta.com/api/v1/users/{userId}/factors" \
      -d '{"factorType":"token:software:totp","provider":"OKTA"}' | python3 -m json.tool

    # Response includes _embedded.activation.sharedSecret — save this value

    # Step 2: Activate by providing a valid TOTP code from the seed
    python3 -c "import pyotp; print(pyotp.TOTP('SHARED_SECRET_HERE').now())"
    # Use the code to activate:
    curl -s -X POST \
      -H "Authorization: SSWS $OKTA_API_TOKEN" \
      -H "Content-Type: application/json" \
      "https://$OKTA_ORG_NAME.okta.com/api/v1/users/{userId}/factors/{factorId}/lifecycle/activate" \
      -d '{"passCode":"123456"}'
    ```
  - The seed will be stored as an SSM SecureString parameter during deployment
  - **Claude Code can do all of this** — just tell it the test user email and desired password

### Playwright Environment

- [ ] **Playwright and chromium installed** (for local runs)
  ```bash
  pip install playwright pyotp
  playwright install chromium
  playwright install-deps chromium  # installs system dependencies (libgbm, etc.)
  ```
  - GitHub Actions runners have chromium available already
  - On headless Linux servers, `playwright install-deps` is required for system libraries

### AWS Infrastructure (same as SSF mode)

- [ ] **AWS account and IAM role** as described in the SSF section above
- [ ] **`AWS_ROLE_ARN` in GitHub Environment** (or local AWS CLI access)
- [ ] Real mode additionally needs the Session Replayer Lambda in a second region (e.g., `eu-west-1`)

---

## Optional: Video Recording

If you want to record demo videos showing the session hijacking in action:

- [ ] **S3 bucket access** for storing demo videos
  - The Terraform module creates the bucket (`{env}-itp-demo-videos`) when `enable_video_bucket = true`
  - GitHub Actions role needs `s3:PutObject` and `s3:GetObject` on the bucket
  - Videos auto-expire after 90 days (configurable via `video_retention_days`)

- [ ] **`github_actions_role_arn`** set in the Terraform module
  - This grants the GitHub Actions OIDC role access to the video bucket
  - Without this, video upload from GitHub Actions will fail

---

## How to Verify Your Prerequisites

Run these commands to validate each prerequisite before starting deployment.

### Okta API Access

```bash
# Set your credentials
export OKTA_ORG_NAME=myorg
export OKTA_API_TOKEN=your-token-here

# Test API access (should return your user profile)
curl -s -H "Authorization: SSWS $OKTA_API_TOKEN" \
  "https://$OKTA_ORG_NAME.okta.com/api/v1/users/me" | python3 -c "
import json, sys
u = json.load(sys.stdin)
print(f'Authenticated as: {u[\"profile\"][\"email\"]}')
print(f'Admin: {u[\"profile\"].get(\"userType\", \"unknown\")}')
"
```

### ITP License / Entity Risk Policy

```bash
# Check for entity risk policy (empty array = ITP not enabled)
curl -s -H "Authorization: SSWS $OKTA_API_TOKEN" \
  "https://$OKTA_ORG_NAME.okta.com/api/v1/policies?type=ENTITY_RISK" | python3 -c "
import json, sys
policies = json.load(sys.stdin)
if policies:
    print(f'Entity risk policy found: {policies[0][\"name\"]} (id: {policies[0][\"id\"]})')
else:
    print('ERROR: No entity risk policy found. Is ITP enabled on this org?')
"
```

### GitHub Environment Secrets

```bash
# Verify GitHub CLI is authenticated
gh auth status

# List environments (check yours exists)
gh api repos/{owner}/{repo}/environments --jq '.environments[].name'
```

### AWS Access (SSF/Real modes)

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check SSM access (should not error)
aws ssm describe-parameters --parameter-filters "Key=Name,Option=Contains,Values=/itp/" \
  --max-results 1 2>&1 | head -5

# Check Lambda access
aws lambda list-functions --query 'Functions[?contains(FunctionName, `itp`)].FunctionName' \
  --output text
```

### Test User (Real mode)

```bash
# Verify test user exists and is active
curl -s -H "Authorization: SSWS $OKTA_API_TOKEN" \
  "https://$OKTA_ORG_NAME.okta.com/api/v1/users/test-user@example.com" | python3 -c "
import json, sys
u = json.load(sys.stdin)
print(f'User: {u[\"profile\"][\"email\"]}')
print(f'Status: {u[\"status\"]}')
"

# Verify TOTP factor is enrolled (look for provider: OKTA, factorType: token:software:totp)
USER_ID=$(curl -s -H "Authorization: SSWS $OKTA_API_TOKEN" \
  "https://$OKTA_ORG_NAME.okta.com/api/v1/users/test-user@example.com" | python3 -c "
import json, sys; print(json.load(sys.stdin)['id'])")

curl -s -H "Authorization: SSWS $OKTA_API_TOKEN" \
  "https://$OKTA_ORG_NAME.okta.com/api/v1/users/$USER_ID/factors" | python3 -c "
import json, sys
factors = json.load(sys.stdin)
for f in factors:
    print(f'{f[\"factorType\"]} / {f[\"provider\"]} — {f[\"status\"]}')
"
```

### Playwright (Real mode)

```bash
# Verify playwright is installed
python3 -c "import playwright; print('playwright installed')"
python3 -c "import pyotp; print('pyotp installed')"

# Verify chromium browser
playwright install --dry-run chromium 2>&1 | head -3
```

---

## What Claude Code Can vs. Cannot Do

The deployment prompt (`modules/itp-demo/docs/deploy_itp_demo.md`) can handle most of the setup, but some things require human action first.

### Must Be Done Manually (before starting Claude Code)

| Task | Why |
|------|-----|
| **Enable ITP license on Okta org** | Requires Okta sales/support or admin console activation |
| **Create Okta API token** | Token value only shown once at creation — can't be retrieved via API |
| **Have AWS account access** | Claude Code can deploy into AWS but can't create the account |
| **Fork and clone this repo** | Claude Code runs inside the cloned repo |
| **Install Python 3.11+** | System-level package installation |

### Claude Code Can Do For You (during deployment)

| Task | How |
|------|-----|
| **Deploy AWS backend** (S3, DynamoDB, OIDC role) | Runs `aws-backend/` Terraform |
| **Create GitHub Environment** | `gh api repos/{owner}/{repo}/environments/{env}` |
| **Set GitHub secrets** | `gh secret set` (will prompt for values securely) |
| **Add ITP IAM permissions to existing role** | Attaches inline policy via AWS CLI |
| **Create environment directory structure** | `mkdir -p environments/{env}/{terraform,config}` |
| **Create test user in Okta** | `POST /api/v1/users` with credentials |
| **Enroll TOTP and capture seed** | `POST /api/v1/users/{id}/factors` + activate |
| **Store credentials in SSM** | `aws ssm put-parameter --type SecureString` |
| **Configure entity risk policy rules** | Import/apply scripts |
| **Deploy all ITP infrastructure** | Terraform plan/apply |
| **Register SSF provider with Okta** | `setup_ssf_provider.py` |
| **Install Playwright + chromium** | `pip install` + `playwright install` |
| **Run validation tests** | All three demo modes |

### The Bottom Line

You need **two things** before Claude Code can take over:
1. An Okta org with ITP enabled and an API token
2. An AWS account you can deploy into (with CLI access or credentials)

Everything else — GitHub Environment setup, AWS backend, test user creation, TOTP enrollment, infrastructure deployment, and validation — Claude Code handles through the deployment prompt.

---

## Next Steps

Once all prerequisites for your chosen mode(s) are met:

1. Open Claude Code in this repository root
2. Follow the deployment prompt: [`modules/itp-demo/docs/deploy_itp_demo.md`](../../modules/itp-demo/docs/deploy_itp_demo.md)
3. Or see the full setup guide: [ITP Demo Guide](itp-demo.md)
