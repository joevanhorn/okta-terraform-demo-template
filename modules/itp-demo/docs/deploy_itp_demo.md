# Prompt: Deploy ITP Demo with Claude Code

Use this prompt with **Claude Code** (running inside this repository) to deploy the ITP (Identity Threat Protection) demo automation step by step. Deployment is progressive — Quick mode works immediately, SSF adds signed JWT signals, Real adds browser-based session hijacking simulation. You can stop at any tier.

**Prerequisites:** Complete the checklist at [`itp-demo-prerequisites.md`](itp-demo-prerequisites.md) before starting.

---

## How to Use

1. Complete the prerequisites checklist for your chosen mode(s)
2. Open Claude Code in this repository root
3. Copy the prompt template below
4. Fill in your configuration values
5. Paste into Claude Code

---

## Prompt Template

```
I want to deploy the ITP (Identity Threat Protection) demo automation for my environment.

ENVIRONMENT DETAILS:
- Environment name: {env_name}
- Okta org: {org_name}.okta.com
- Okta API token: {I have one / I need to create one}
- AWS region: {region} (e.g., us-east-1)
- Attacker region: {attacker_region} (e.g., eu-west-1)
- Demo modes to enable: {quick / quick+ssf / quick+ssf+real}
- Test user email: {email} (required for real mode, leave blank if quick/ssf only)
- First environment in this repo? {yes / no}

DEPLOYMENT STEPS (follow in order):

0. ENVIRONMENT BOOTSTRAP (skip items that already exist)
   Check what's already set up and help me configure anything missing:

   a. AWS Backend (if first environment in this repo):
      - Check if the S3 state bucket exists
      - If not, update aws-backend/variables.tf with my repo name and a unique
        bucket name, then run terraform init && terraform plan in aws-backend/
      - Pause for my approval before terraform apply
      - Save the outputs — especially the IAM role ARN

   b. GitHub Environment + Secrets:
      - Check if GitHub Environment "{env_name}" exists:
        gh api repos/{owner}/{repo}/environments/{env_name}
      - If not, create it:
        gh api repos/{owner}/{repo}/environments/{env_name} -X PUT
      - Check which secrets are set:
        gh secret list --env {env_name}
      - For any missing secrets (OKTA_API_TOKEN, OKTA_ORG_NAME, OKTA_BASE_URL,
        AWS_ROLE_ARN), prompt me for the value and set it:
        gh secret set SECRET_NAME --env {env_name}

   c. AWS IAM Permissions for ITP:
      - Check if the GitHub Actions role has ITP permissions (Lambda, SSM)
      - If not, offer to attach the ITP IAM policy from
        modules/itp-demo/docs/itp-aws-requirements.md
      - The Terraform deployment role needs: Lambda, IAM, SSM, CloudWatch Logs
      - The runtime role needs: SSM read, Lambda invoke, S3 write (for videos)

   d. Environment Directory:
      - Create environments/{env_name}/terraform/ and
        environments/{env_name}/config/ if they don't exist
      - Create provider.tf with S3 backend config and Okta provider
        (use environments/myorg/terraform/provider.tf as a reference)
      - Create variables.tf with okta_org_name, okta_base_url, okta_api_token
      - Add aws provider blocks (primary region + attacker alias if needed)

1. CREATE TERRAFORM CONFIGURATION
   - Copy environments/myorg/terraform/itp_demo.tf.example to
     environments/{env_name}/terraform/itp_demo.tf
   - Set feature flags based on my selected modes:
     * Quick only: enable_session_replayer = false, enable_ssf_endpoint = false,
       enable_video_bucket = false
     * Quick+SSF: enable_session_replayer = false, enable_ssf_endpoint = true,
       enable_video_bucket = false
     * All three: enable_session_replayer = true, enable_ssf_endpoint = true,
       enable_video_bucket = true
   - Set environment = "{env_name}"
   - Set attacker_region = "{attacker_region}"
   - Ensure provider.tf has the aws.attacker provider alias for the attacker region
     (if real mode is enabled)
   - Update the module source path to match the environment's relative path to modules/

2. TERRAFORM PLAN
   - Run terraform init in environments/{env_name}/terraform/
   - Run terraform plan — show me the output and pause for approval
   - Prefer using GitHub workflows when available:
     gh workflow run tf-plan.yml -f environment={env_name}

3. TERRAFORM APPLY
   - After I approve the plan, apply via:
     gh workflow run tf-apply.yml -f environment={env_name}
   - Or locally if no workflow: terraform apply

4. SSF PROVIDER REGISTRATION (if SSF mode enabled)
   - After Terraform creates the JWKS Lambda and SSM parameters, register
     the provider with Okta:
     gh workflow run itp-ssf-provider-setup.yml -f environment={env_name}
   - Or locally:
     python3 scripts/setup_ssf_provider.py --ssm-prefix /{env_name}/itp/ssf-demo
   - Verify registration: python3 scripts/setup_ssf_provider.py --list

5. CREATE TEST USER (if Real mode enabled, skip if user already exists)
   - Check if the test user already exists in Okta:
     curl -s -H "Authorization: SSWS $OKTA_API_TOKEN" \
       "https://{org_name}.okta.com/api/v1/users/{test_user_email}"
   - If the user doesn't exist, ask me for a password and create:
     POST /api/v1/users?activate=true with profile + credentials
   - Check if user has TOTP enrolled:
     GET /api/v1/users/{userId}/factors
     Look for factorType=token:software:totp, provider=OKTA
   - If no OKTA TOTP factor exists, enroll one:
     POST /api/v1/users/{userId}/factors
       {"factorType":"token:software:totp","provider":"OKTA"}
     Capture the sharedSecret from _embedded.activation
     Generate a TOTP code from the seed and activate:
     POST /api/v1/users/{userId}/factors/{factorId}/lifecycle/activate
       {"passCode":"<generated_code>"}
   - If user has non-TOTP factors that would interrupt login (push, webauthn),
     warn me and offer to remove them

6. STORE TEST USER CREDENTIALS IN SSM (if Real mode enabled)
   - Store the password and TOTP seed as SSM SecureString parameters:
     aws ssm put-parameter --name "/{env_name}/itp/password" \
       --value "PASSWORD" --type SecureString
     aws ssm put-parameter --name "/{env_name}/itp/totp-secret" \
       --value "TOTP_SEED" --type SecureString
   - NEVER echo or log the actual credential values
   - If user was created in step 5, use the password from that step and the
     TOTP seed captured during enrollment

7. ENTITY RISK POLICY
   - Import the current policy from Okta:
     gh workflow run itp-entity-risk-policy-import.yml -f environment={env_name}
   - Or locally:
     python3 scripts/import_entity_risk_policy.py \
       --output environments/{env_name}/config/entity_risk_policy.json
   - Check that the policy has rules configured for HIGH risk with actions
   - If no HIGH risk rule exists, create the config JSON with a rule:
     {"name": "High Risk Response",
      "conditions": {"riskLevel": "HIGH"},
      "actions": {"terminateSessions": true, "challengeWithMFA": true}}
   - Apply it:
     python3 scripts/apply_entity_risk_policy.py \
       --config environments/{env_name}/config/entity_risk_policy.json
     Or: gh workflow run itp-entity-risk-policy-apply.yml \
       -f environment={env_name} -f dry_run=false

8. VALIDATE — QUICK MODE
   - Run a quick mode test:
     python3 scripts/trigger_itp_demo.py --mode quick \
       --user {test_user_or_any_user} --risk-level HIGH \
       --monitor --monitor-duration 60 --auto-reset
   - Or via workflow:
     gh workflow run itp-demo-trigger.yml \
       -f environment={env_name} -f mode=quick \
       -f user_email={email} -f risk_level=HIGH
   - Expected: system log shows "Admin reported user risk", policy evaluates,
     risk resets to LOW

9. VALIDATE — SSF MODE (if enabled)
   - Run an SSF mode test:
     python3 scripts/trigger_itp_demo.py --mode ssf \
       --user {test_user_or_any_user} --risk-level HIGH \
       --ssm-prefix /{env_name}/itp \
       --monitor --monitor-duration 60 --auto-reset
   - Or via workflow:
     gh workflow run itp-demo-trigger.yml \
       -f environment={env_name} -f mode=ssf \
       -f user_email={email} -f ssf_risk_level=HIGH
   - Expected: system log shows "Security events provider reported risk",
     policy evaluates, risk resets

10. VALIDATE — REAL MODE (if enabled)
    - Run a real mode test:
      python3 scripts/trigger_itp_demo.py --mode real \
        --user {test_user_email} \
        --ssm-prefix /{env_name}/itp \
        --attacker-lambda {env_name}-itp-session-replayer \
        --attacker-region {attacker_region} \
        --monitor --monitor-duration 120 --auto-reset
    - Or via workflow:
      gh workflow run itp-demo-trigger.yml \
        -f environment={env_name} -f mode=real \
        -f user_email={test_user_email} \
        -f attacker_region={attacker_region}
    - Expected: full event chain — user.risk.detect, policy.entity_risk.evaluate,
      policy.entity_risk.action, user.session.end,
      user.authentication.universal_logout

11. SHOW RESULTS
    - Summarize what was deployed and what each test showed
    - List the resources created (Lambda functions, SSM parameters, S3 bucket)
    - Provide the commands to run each demo mode going forward

RULES:
- Use the existing modules/itp-demo/ module — do NOT create new Terraform resources
- Use existing scripts (trigger_itp_demo.py, setup_ssf_provider.py, etc.)
- Use existing GitHub workflows when available (prefer workflows over local runs)
- Follow CLAUDE.md patterns for this repo (especially $$ escaping for Okta templates)
- Pause before each terraform apply
- Pause before creating SSM parameters with credentials
- Store test user credentials as SSM SecureString only — never in tfvars or code
- For real mode: if the test user doesn't exist yet, offer to create it via API
- For TOTP enrollment: enroll via API, capture the seed, activate — no manual steps
- When creating entity risk policy rules, use dry-run first
- If an environment directory doesn't exist yet, create the full structure:
  environments/{env_name}/terraform/ and environments/{env_name}/config/
- For AWS backend setup, use the aws-backend/ Terraform in the repo
- The S3 backend bucket name must be globally unique — suggest "{org_name}-terraform-state"
```

---

## Example: Filled-In Prompt

```
I want to deploy the ITP (Identity Threat Protection) demo automation for my environment.

ENVIRONMENT DETAILS:
- Environment name: acme-corp
- Okta org: acme-corp.okta.com
- Okta API token: I have one
- AWS region: us-east-1
- Attacker region: eu-west-1
- Demo modes to enable: quick+ssf+real
- Test user email: itp-test@acme-corp.com
- First environment in this repo? yes

DEPLOYMENT STEPS (follow in order):
[... same steps as above ...]
```

---

## What Claude Code Will Do

### Phase 0: Environment Bootstrap (first-time only)

Checks what infrastructure already exists and sets up anything missing:
- Deploys AWS backend (S3, DynamoDB, OIDC role) if this is the first environment
- Creates GitHub Environment and sets secrets (`OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`, `AWS_ROLE_ARN`)
- Adds ITP-specific IAM permissions to the GitHub Actions role
- Creates `environments/{env}/terraform/` with `provider.tf` and `variables.tf`

### Phase 1: ITP Infrastructure (Terraform)

1. Creates `environments/{env}/terraform/itp_demo.tf` from the example file
2. Configures feature flags based on your selected modes
3. Ensures `provider.tf` has the `aws.attacker` provider alias
4. Runs `terraform init` and `terraform plan`
5. Pauses for your approval before `terraform apply`

**Resources created by Terraform:**
- Session Replayer Lambda in attacker region (real mode)
- SSF JWKS Lambda with public Function URL (SSF mode)
- RSA key pair for JWT signing (SSF mode)
- SSM parameters for SSF config and private key (SSF mode)
- S3 bucket for demo videos (optional)
- IAM roles and CloudWatch log groups

### Phase 2: Okta + AWS Configuration

6. Registers SSF provider with Okta (SSF mode) — links your JWKS endpoint to your org
7. Creates test user in Okta via API (real mode) — if the user doesn't already exist
8. Enrolls TOTP factor on the test user via API — captures the seed programmatically
9. Stores test user credentials in SSM as SecureString (real mode)
10. Imports entity risk policy from Okta — creates HIGH risk rules if none exist

### Phase 3: Validation

11. Runs Quick mode test — sets risk HIGH, monitors system log, auto-resets
12. Runs SSF mode test — sends signed JWT, monitors for provider-reported risk
13. Runs Real mode test — authenticates user, replays cookie cross-region, monitors full event chain

### Estimated Time

| Mode | Bootstrap (first time) | Infrastructure | Post-setup | Validation | Total |
|------|----------------------|---------------|------------|------------|-------|
| Quick only | +5 min | 0 min | 2 min | 2 min | ~5-10 min |
| Quick + SSF | +5 min | 5 min | 3 min | 5 min | ~15-20 min |
| All three | +5 min | 5 min | 5 min | 10 min | ~25-30 min |

(Bootstrap only runs once. Terraform apply via GitHub Actions adds ~3-5 min for workflow startup.)

---

## Troubleshooting

### Terraform Issues

**"No valid credential sources found"**
- AWS credentials not configured. Set `AWS_ROLE_ARN` in GitHub Environment or configure local AWS CLI.

**"Error: Unsupported provider alias"**
- Missing `aws.attacker` provider alias in `provider.tf`. Add:
  ```hcl
  provider "aws" {
    alias  = "attacker"
    region = "eu-west-1"
  }
  ```

**Plan shows drift on `provider-config` SSM parameter**
- Expected behavior. The `lifecycle { ignore_changes = [value] }` on the SSM parameter prevents Terraform from overwriting the provider_id added by `setup_ssf_provider.py`.

### SSF Mode Issues

**"Invalid JWT" (400) from security events endpoint**
- JWKS URL not accessible — verify Lambda Function URL: `curl <jwks_url>`
- `kid` mismatch — the `kid` in JWT header must match JWKS
- `iss` mismatch — the `iss` claim must exactly match the registered provider's issuer

**"Provider not found" (400)**
- Provider not registered. Run: `python3 scripts/setup_ssf_provider.py --list`
- If no providers listed, re-run the setup workflow

**SSF signal accepted but no system log events**
- Entity risk policy may not have a HIGH risk rule. Import and check:
  ```bash
  python3 scripts/import_entity_risk_policy.py --output /tmp/policy.json
  cat /tmp/policy.json
  ```

### Real Mode Issues

**Authentication fails / screenshot at `/tmp/itp-auth-failure.png`**
- Wrong password in SSM — update: `aws ssm put-parameter --name /{env}/itp/password --value "NEW_PASSWORD" --type SecureString --overwrite`
- TOTP expired during auth — retry (timing issue)
- User has additional MFA factors — remove all except OKTA TOTP
- TOTP provider is GOOGLE instead of OKTA — re-enroll with provider OKTA

**"chromium executable not found"**
- Run: `playwright install chromium && playwright install-deps chromium`

**Lambda invocation fails**
- Check Lambda exists: `aws lambda get-function --function-name {env}-itp-session-replayer`
- Check Lambda region matches `--attacker-region`
- Check IAM role has `lambda:InvokeFunction` permission

**No `user.risk.detect` event after cookie replay**
- Cookie may have expired — the IDX cookie has a short TTL
- Retry the full flow (authenticate + replay must happen within ~60 seconds)
- Verify the attacker Lambda is in a different region than the victim auth

### General Issues

**No system log events appearing**
- System log has a ~30 second delay. Use `--monitor-duration 120` for more time.
- Check user exists: the `--user` email must match an active Okta user
- Verify entity risk policy has active rules

**Risk doesn't reset**
- Use `--auto-reset` flag, or manually:
  ```bash
  python3 scripts/trigger_itp_demo.py --mode quick \
    --user user@example.com --risk-level LOW
  ```

For detailed troubleshooting, see [ITP Demo Guide — Troubleshooting](itp-demo.md#troubleshooting).

---

## Running Demos After Deployment

Once deployed, use these commands to run demos anytime:

### Quick Mode (instant, no infrastructure)
```bash
python3 scripts/trigger_itp_demo.py --mode quick \
  --user user@example.com --risk-level HIGH --monitor --auto-reset
```

### SSF Mode (signed JWT signal)
```bash
python3 scripts/trigger_itp_demo.py --mode ssf \
  --user user@example.com --risk-level HIGH \
  --ssm-prefix /{env}/itp --monitor --auto-reset
```

### Real Mode (session hijacking simulation)
```bash
python3 scripts/trigger_itp_demo.py --mode real \
  --user itp-test@example.com \
  --ssm-prefix /{env}/itp \
  --attacker-lambda {env}-itp-session-replayer \
  --attacker-region eu-west-1 \
  --monitor --auto-reset
```

### Real Mode with Video Recording
```bash
python3 scripts/trigger_itp_demo.py --mode real \
  --user itp-test@example.com \
  --ssm-prefix /{env}/itp \
  --attacker-lambda {env}-itp-session-replayer \
  --record-video /tmp/itp-video \
  --upload-s3 {env}-itp-demo-videos \
  --monitor --auto-reset
```

### Via GitHub Actions (any mode)
```bash
gh workflow run itp-demo-trigger.yml \
  -f environment={env} \
  -f mode=quick \
  -f user_email=user@example.com \
  -f risk_level=HIGH
```

For the full CLI reference, see [ITP Demo Guide — CLI Reference](itp-demo.md#cli-reference).
