# Prompt: Deploy Full Environment from Worksheet

Use this prompt to have Claude Code deploy a complete Okta demo environment from a filled-out Demo Deployment Worksheet.

---

## How to Use

1. Fill out `demo-builder/DEMO_WORKSHEET.md`
2. Open Claude Code in this repository root
3. Paste the following:

```
I have a completed Demo Deployment Worksheet. Please deploy the full
environment following the instructions in
ai-assisted/prompts/deploy_full_environment.md.

HERE IS MY COMPLETED WORKSHEET:
[Paste your filled worksheet here]
```

---

## Deployment Phases

Execute these phases in order. PAUSE before every `terraform apply` and every workflow that modifies infrastructure. Skip phases for sections the user left disabled.

### Phase 0: Parse Worksheet

1. Extract all configuration values from the worksheet
2. Identify which optional sections are enabled (look for "Yes" or filled-in values)
3. Validate required fields:
   - Section 1: environment name, Okta org name, email domain are required
   - Section 14: AWS region and S3 bucket name are required if any infrastructure sections are enabled
4. Build a summary showing:
   - Environment name and Okta org
   - Which sections are enabled
   - Number of users, groups, and apps to create
   - Which infrastructure components will be deployed
5. Present the summary and ask the user to confirm before proceeding

### Phase 1: Environment Bootstrap

#### AWS Backend (if first environment in this repo)

If the user indicated "First environment in this repo? = Yes":

```bash
cd aws-backend
terraform init
terraform plan    # PAUSE — show plan and confirm
terraform apply
```

Save the `github_actions_role_arn` output — needed for GitHub secrets.

#### GitHub Environment + Secrets

Create the GitHub Environment and set secrets:

```bash
# Create GitHub Environment
gh api repos/{owner}/{repo}/environments/{env_name} -X PUT

# Set required secrets (prompt user for values they haven't provided)
gh secret set OKTA_ORG_NAME --env {env_name} --body "{okta_org_name}"
gh secret set OKTA_BASE_URL --env {env_name} --body "{okta_base_url}"
gh secret set OKTA_API_TOKEN --env {env_name} --body "{api_token}"  # Ask user
gh secret set AWS_ROLE_ARN --env {env_name} --body "{role_arn}"     # If AWS sections enabled
```

If OPA is enabled (Section 12), also set:
```bash
gh secret set OKTAPAM_KEY --env {env_name} --body "{key}"        # Ask user
gh secret set OKTAPAM_SECRET --env {env_name} --body "{secret}"  # Ask user
gh secret set OKTAPAM_TEAM --env {env_name} --body "{team}"      # Ask user
gh secret set OKTAPAM_API_HOST --env {env_name} --body "{host}"  # Ask user
```

#### Environment Directory

```bash
mkdir -p environments/{env_name}/{terraform,imports,config}
```

#### provider.tf

Generate `environments/{env_name}/terraform/provider.tf` with:
- S3 backend using the state bucket and key prefix from Section 14
- Okta provider with `api_token` auth (NOT OAuth — see CLAUDE.md gotcha #9)
- AWS provider (if any infrastructure sections enabled)
- oktapam provider (if Section 12 OPA is enabled) — commented out by default, with note to uncomment after secrets are set

#### variables.tf

Generate `environments/{env_name}/terraform/variables.tf` with all required variables:
- `okta_org_name`, `okta_base_url`, `okta_api_token`
- `aws_region` (if infrastructure enabled)
- `environment` (set to env_name)

### Phase 2: Okta Resources

Generate Terraform files from Sections 2-4:

#### users.tf (from Section 2)

- Create `okta_user` resources for each department's managers and employees
- Auto-generate employee names using department prefix if no specific names given
- Set `department`, `title`, `user_type` attributes
- Use `lifecycle { ignore_changes = [manager_id] }` on all users
- Create `okta_link_value` resources for manager relationships
- Handle contractors with `user_type = "Contractor"`
- Handle executives with their specified titles

CRITICAL: Use `$$` for any Okta template strings (e.g., `$${source.login}`).

#### groups.tf (from Section 3)

- Create `okta_group` for each department (auto-generated from Section 2)
- Create `okta_group` for each additional group from Section 3
- Create `okta_group_rule` for groups with rules (e.g., "User type = Employee")

#### group_memberships.tf

- Create `okta_group_memberships` for static group assignments
- Group rules handle dynamic assignments

#### apps.tf (from Section 4)

For each application:
- `oauth_web` → `okta_app_oauth` with `grant_types = ["authorization_code"]`
- `oauth_spa` → `okta_app_oauth` with `grant_types = ["authorization_code"]`, `token_endpoint_auth_method = "none"`
- `oauth_service` → `okta_app_oauth` with `grant_types = ["client_credentials"]`, `hide_ios = true`, `hide_web = true`
- `oauth_native` → `okta_app_oauth` with `grant_types = ["authorization_code"]`, `type = "native"`
- `saml` → `okta_app_saml` with appropriate settings

Set `redirect_uris` from the Notes column if provided.

CRITICAL: For service apps, set `hide_ios = true`, `hide_web = true`, `login_mode = "DISABLED"` (see CLAUDE.md gotcha #5).

#### app_assignments.tf

- Create `okta_app_group_assignment` for each app-to-group assignment from Section 4

#### policies.tf (from Section 7, if provided)

- Create `okta_policy_signon` for sign-on policies
- Create `okta_policy_password` for password policies
- Create `okta_policy_rule_signon` for MFA rules

#### Deploy Okta Resources

```bash
cd environments/{env_name}/terraform
terraform init
terraform plan    # PAUSE — show plan and confirm
```

Then trigger the apply workflow:

```bash
gh workflow run tf-apply.yml -f environment={env_name}
```

Wait for approval and completion. Verify:

```bash
gh run list --workflow=tf-apply.yml --limit 1
```

### Phase 3: Identity Governance (if Section 5 enabled)

#### oig.tf

Generate from Section 5:

- `okta_access_review_campaign` for each campaign in the table

NOTE: Entitlement bundles are NOT generated at this stage. Bundles are per-app and
reference specific entitlement values that must first be synced into each application.
Bundle creation happens after:
1. Apps are deployed and entitlement management is enabled (see Entitlement Management Settings below)
2. Entitlements are imported/synced from their source (SCIM, Generic DB Connector, Okta integration)
3. The user creates bundles in Okta Admin UI or adds `okta_entitlement_bundle` resources to Terraform
   referencing specific app entitlements (see `RESOURCE_EXAMPLES.tf` for the pattern)

CRITICAL: When creating `okta_entitlement_bundle` resources in Terraform, entitlement values must
be alphabetically ordered by `external_value` (see CLAUDE.md gotcha #11).

#### Deploy OIG Resources

```bash
terraform plan    # PAUSE — show plan and confirm
gh workflow run tf-apply.yml -f environment={env_name}
```

#### Resource Owners (if enabled)

If owner strategy is "Auto-assign":

```bash
# Sync current owners first
python3 scripts/sync_owner_mappings.py \
  --output environments/{env_name}/config/owner_mappings.json

# Apply owners
python3 scripts/apply_resource_owners.py \
  --config environments/{env_name}/config/owner_mappings.json \
  --dry-run    # PAUSE — show dry run and confirm

python3 scripts/apply_resource_owners.py \
  --config environments/{env_name}/config/owner_mappings.json
```

Or via workflow:

```bash
gh workflow run oig-owners.yml -f environment={env_name} -f dry_run=false
```

#### Governance Labels (if enabled)

If "Label admin entitlements automatically" is Yes:

```bash
python3 scripts/apply_admin_labels.py --dry-run    # PAUSE — review
python3 scripts/apply_admin_labels.py
```

Or via workflow:

```bash
gh workflow run labels-apply.yml -f label_type=admin -f environment={env_name} -f dry_run=false
```

#### Entitlement Management Settings

Enable entitlement management on each app marked "Yes" in the worksheet's Entitlement Management table.
This is a prerequisite for entitlement import/sync and bundle creation.

```bash
python3 scripts/manage_entitlement_settings.py --action list    # Review current state

# Enable on specific apps, or use auto mode to enable on all eligible apps
gh workflow run oig-manage-entitlements.yml \
  -f mode=auto -f environment={env_name} -f dry_run=true    # PAUSE — review

gh workflow run oig-manage-entitlements.yml \
  -f mode=auto -f environment={env_name} -f dry_run=false
```

After entitlements are synced into apps (via Okta integration, SCIM, or DB Connector), the user
can create entitlement bundles in Okta Admin UI or add `okta_entitlement_bundle` Terraform resources.

#### Risk Rules (if enabled)

If risk rules are defined in the worksheet:

1. Generate `environments/{env_name}/config/risk_rules.json` from the worksheet table
2. Apply:

```bash
python3 scripts/apply_risk_rules.py \
  --config environments/{env_name}/config/risk_rules.json \
  --dry-run    # PAUSE — review

python3 scripts/apply_risk_rules.py \
  --config environments/{env_name}/config/risk_rules.json
```

Or via workflow:

```bash
gh workflow run oig-risk-rules-apply.yml -f environment={env_name} -f dry_run=false
```

#### Manual Follow-Up Notice

Print a notice:
```
MANUAL STEPS REQUIRED after entitlements sync into apps:
  1. Create entitlement bundles referencing specific app entitlements:
     Admin Console → Identity Governance → Entitlement Bundles → Create Bundle
     (Or add okta_entitlement_bundle resources to Terraform — see RESOURCE_EXAMPLES.tf)
  2. Assign bundles to users/groups:
     Admin Console → Identity Governance → Entitlement Bundles → [Bundle] → Assignments
     (Bundle assignments are NOT managed by Terraform)
```

### Phase 4: Lifecycle Management (if Section 6 enabled)

#### lifecycle.tf

Generate using `modules/lifecycle-management`:

```hcl
module "lifecycle" {
  source = "../../../modules/lifecycle-management"

  organization_name          = "{company_name}"
  enable_joiner_patterns     = {joiner_enabled}
  enable_mover_patterns      = {mover_enabled}
  enable_leaver_patterns     = {leaver_enabled}
  enable_contractor_lifecycle = {contractor_enabled}
  enable_oig_integration     = {oig_integration_enabled}
  create_lifecycle_status_attribute = {create_lifecycle_status}

  user_types = [
    # From worksheet user types table
  ]

  departments = [
    # From Section 2 department list
  ]

  contractor_config = {
    warning_days     = {warning_days}
    final_notice_days = {final_notice_days}
  }
}
```

#### Deploy

```bash
terraform plan    # PAUSE — show plan and confirm
gh workflow run tf-apply.yml -f environment={env_name}
```

### Phase 5: Active Directory (if Section 9 enabled)

#### Create AD Infrastructure Directory

Use the AD module directly, or create a local wrapper:

```bash
mkdir -p environments/{env_name}/ad-infrastructure
```

#### Generate AD Terraform

Generate `environments/{env_name}/ad-infrastructure/main.tf` (references `modules/ad-domain-controller`):

```hcl
module "ad_dc" {
  source = "../../../modules/ad-domain-controller"

  environment        = "{env_name}"
  aws_region         = "{aws_region}"           # From worksheet
  region_short       = "{region_short}"         # From worksheet
  ad_domain_name     = "{ad_domain_name}"       # From worksheet
  ad_netbios_name    = "{ad_netbios_name}"      # From worksheet
  instance_type      = "{instance_type}"        # From worksheet
  create_sample_users = {create_sample_users}   # From worksheet
  create_vpc         = {create_vpc}             # From worksheet
  vpc_cidr           = "{vpc_cidr}"             # From worksheet
  enable_rdp         = {enable_rdp}             # From worksheet
  assign_elastic_ip  = {assign_elastic_ip}      # From worksheet
}
```

Generate `environments/{env_name}/ad-infrastructure/provider.tf` with S3 backend:
- State key: `Okta-GitOps/{env_name}/ad-infrastructure/{region}/terraform.tfstate`

#### Deploy via Workflow

```bash
gh workflow run ad-deploy.yml \
  -f environment={env_name} \
  -f regions='["{aws_region}"]' \
  -f action=plan    # PAUSE — review plan

gh workflow run ad-deploy.yml \
  -f environment={env_name} \
  -f regions='["{aws_region}"]' \
  -f action=apply
```

Wait for completion (AD bootstrap takes 5-10 minutes).

#### Verify AD Health

```bash
gh workflow run ad-health-check.yml \
  -f environment={env_name} \
  -f region={aws_region}
```

#### Install Okta AD Agent (if enabled)

```bash
gh workflow run ad-install-okta-agent.yml \
  -f environment={env_name} \
  -f region={aws_region}
```

Print notice:
```
MANUAL STEP REQUIRED: The Okta AD Agent is installed but requires interactive
browser-based activation. Connect via SSM Session Manager and run:
  sudo /opt/OktaProvisioningAgent/configure_agent.sh
```

### Phase 6: Database Connector + OPC (if Section 10 enabled)

#### Create Infrastructure Directories

Use the modules directly, or create local wrappers:

```bash
mkdir -p environments/{env_name}/generic-db-infrastructure
mkdir -p environments/{env_name}/opc-infrastructure-v2
```

#### Generate Generic DB Terraform

Generate `environments/{env_name}/generic-db-infrastructure/main.tf` (references `modules/generic-db-connector`) with:
- RDS PostgreSQL instance
- VPC, subnets, security groups
- Secrets Manager for credentials
- S3 backend for state

#### Deploy Generic DB

```bash
gh workflow run generic-db-deploy.yml \
  -f environment={env_name} \
  -f action=plan    # PAUSE — review

gh workflow run generic-db-deploy.yml \
  -f environment={env_name} \
  -f action=apply
```

#### Initialize Database Schema

```bash
gh workflow run generic-db-schema-init.yml \
  -f environment={env_name} \
  -f action=initialize
```

#### Generate OPC Agent Terraform

Generate `environments/{env_name}/opc-infrastructure-v2/main.tf` using `modules/opc-agent`:

```hcl
module "opc_agents" {
  source = "../../../modules/opc-agent"

  for_each = {
    "{connector_type}-1" = { instance_number = 1 }
    # Add more if instance count > 1
  }

  environment        = "{env_name}"
  region_short       = "{region_short}"
  connector_type     = "{connector_type}"     # From worksheet
  instance_type      = "{instance_type}"      # From worksheet
  instance_number    = each.value.instance_number
  vpc_id             = "{vpc_id}"             # From DB infrastructure output
  subnet_id          = "{subnet_id}"          # From DB infrastructure output
  security_group_ids = ["{sg_id}"]            # From DB infrastructure output
  use_prebuilt_ami   = {use_prebuilt_ami}     # From worksheet
}
```

#### Deploy OPC Agent

```bash
gh workflow run opc-deploy.yml \
  -f environment={env_name} \
  -f action=plan    # PAUSE — review

gh workflow run opc-deploy.yml \
  -f environment={env_name} \
  -f action=apply
```

#### Install OPC Agent Software

```bash
gh workflow run opc-install-agent.yml \
  -f environment={env_name} \
  -f target_agent=all
```

Print notice:
```
MANUAL STEP REQUIRED: After OPC agent installation, connect via SSM and run:
  sudo /opt/OktaProvisioningAgent/configure_agent.sh
This requires interactive browser login to activate the agent with your Okta org.

IMPORTANT: For entitlement import to work, you must also:
1. Enable "Provisioning to App" in the Okta app settings
2. Configure the "Update User" SQL query
See MEMORY.md for details on this undocumented requirement.
```

### Phase 7: SCIM Server (if Section 11 enabled)

#### Deploy SCIM Server

```bash
gh workflow run deploy-scim-server.yml \
  -f environment={env_name} \
  -f domain_name="{domain_name}"       # From worksheet
  -f route53_zone_id="{zone_id}"       # From worksheet
  -f instance_type="{instance_type}"   # From worksheet
  -f action=plan    # PAUSE — review

gh workflow run deploy-scim-server.yml \
  -f environment={env_name} \
  -f domain_name="{domain_name}" \
  -f route53_zone_id="{zone_id}" \
  -f instance_type="{instance_type}" \
  -f action=apply
```

If using custom entitlements file, pass it:
```bash
-f entitlements_file="{custom_file}"
```

Print notice:
```
IMPORTANT SCIM NOTES:
- Okta requires entitlement schema URN: urn:okta:scim:schemas:core:1.0:Entitlement
  (NOT the standard IETF URN)
- When configuring the bearer token in Okta, prefix it with "Bearer " — Okta's
  scim2headerauth sends the token WITHOUT the "Bearer " prefix
- JDBC drivers must be in /opt/OktaOnPremScimServer/userlib/ (not just /installers/)
```

### Phase 8: OPA (if Section 12 enabled)

#### Generate OPA Terraform

Generate in the main `environments/{env_name}/terraform/` directory:

**opa_resources.tf** — Resource groups, projects, enrollment tokens:
- `oktapam_group` for each enabled tier
- `oktapam_resource_group` and `oktapam_project` for server management
- `oktapam_server_enrollment_token` for each project

**opa_security_policies.tf** — Security policies for each enabled tier:

CRITICAL rules for OPA Terraform:
1. Always set `type = "default"` on `oktapam_security_policy_v2` resources
2. Password checkout rules MUST come BEFORE SSH rules (matches API return order)
3. `admin_level_permissions = true` CANNOT be combined with `sudo_command_bundles`
4. `password_checkout_ssh` requires `account_selector_type = "username"` with specific usernames
5. Use the sudo command bundles from the worksheet tier table

Generate `oktapam_sudo_command_bundle` resources for each tier's commands.

Generate `oktapam_security_policy_v2` for each enabled tier following this pattern:

```hcl
resource "oktapam_security_policy_v2" "tier_name" {
  name        = "Tier-Display-Name"
  type        = "default"    # CRITICAL — prevents drift
  description = "..."
  active      = true
  principals  = { user_groups = [oktapam_group.tier_group.id] }

  rules = [
    # If password checkout enabled for this tier:
    {
      name          = "password-checkout"
      resource_type = "server_based_resource"
      resource_selector = {
        server_based_resource = {
          selectors = [{
            server_label = {
              account_selector_type = "username"
              account_selector      = { usernames = ["root", "postgres"] }
              server_selector       = { labels = { "system.os_type" = "linux" } }
            }
          }]
        }
      }
      privileges = [{
        password_checkout_ssh = { password_checkout_ssh = true }
      }]
    },
    # SSH access rule (MUST come AFTER password checkout):
    {
      name          = "ssh-access"
      resource_type = "server_based_resource"
      resource_selector = {
        server_based_resource = {
          selectors = [{
            server_label = {
              account_selector_type = "none"
              account_selector      = {}
              server_selector       = { labels = { "system.os_type" = "linux" } }
            }
          }]
        }
      }
      privileges = [{
        principal_account_ssh = {
          principal_account_ssh  = true
          admin_level_permissions = false    # or true for Full Admin tier
          sudo_display_name      = "Tier Display Name"
          sudo_command_bundles   = [oktapam_sudo_command_bundle.tier_bundle.id]
        }
      }]
    }
  ]
}
```

#### Uncomment oktapam Provider

Uncomment the `oktapam` provider block in `provider.tf` if it was commented out.

#### Deploy OPA

```bash
terraform plan    # PAUSE — review
```

Use the OPA plan workflow for targeted planning:
```bash
gh workflow run opa-plan.yml -f environment={env_name}
```

Then apply via the standard apply workflow:
```bash
gh workflow run tf-apply.yml -f environment={env_name}
```

IMPORTANT: `OKTAPAM_API_HOST` is NOT `app.scaleft.com` — it must be set as a GitHub Environment secret.

### Phase 9: SAML Federation (if Section 13 enabled)

#### Generate federation.tf

Use `modules/saml-federation`:

```hcl
module "federation" {
  source = "../../../modules/saml-federation"

  federation_mode = "{mode}"            # "sp" or "idp" from worksheet
  federation_name = "{federation_name}" # From worksheet
  okta_org_name   = var.okta_org_name

  # SP mode settings (if mode = "sp")
  idp_name        = "{idp_name}"
  idp_issuer      = "{idp_issuer}"
  idp_sso_url     = "{idp_sso_url}"
  idp_certificate = "{idp_certificate}"
  provisioning_action = "{jit_enabled ? "AUTO" : "DISABLED"}"
  enable_routing_rule = {routing_enabled}
  routing_domain_suffix = "{routing_domain}"

  # IdP mode settings (if mode = "idp")
  app_label       = "{app_label}"
  sp_org_name     = "{partner_subdomain}"
  sp_acs_url      = "{partner_acs_url}"
  sp_audience     = "{partner_audience}"
  assigned_group_ids = [for g in okta_group.groups : g.id if contains({assigned_groups}, g.name)]
}
```

#### Deploy

```bash
terraform plan    # PAUSE — review
gh workflow run tf-apply.yml -f environment={env_name}
```

### Phase 10: ITP Demo (if Section 8 enabled)

#### Generate itp_demo.tf

Use `modules/itp-demo`:

```hcl
module "itp_demo" {
  source = "../../../modules/itp-demo"

  attacker_region = "{attacker_region}"    # From worksheet, default "eu-west-1"
  function_name   = "itp-demo-session-replayer"

  providers = {
    aws           = aws
    aws.attacker  = aws.attacker    # Only if real mode enabled
  }
}
```

If real or SSF mode is enabled, add the attacker region provider alias:

```hcl
provider "aws" {
  alias  = "attacker"
  region = "{attacker_region}"
}
```

#### Deploy ITP Infrastructure (if SSF or Real mode enabled)

```bash
terraform plan    # PAUSE — review
gh workflow run tf-apply.yml -f environment={env_name}
```

#### SSF Provider Setup (if SSF mode enabled)

```bash
gh workflow run itp-ssf-provider-setup.yml -f environment={env_name}
```

#### Create Test User (if Real mode enabled and "Create via API" = Yes)

Use the Okta API to:
1. Create the test user with a temporary password
2. Activate the user
3. Enroll a TOTP factor and capture the shared secret
4. Store credentials in SSM Parameter Store:

```bash
aws ssm put-parameter \
  --name "/{env_name}/itp-demo/password" \
  --type SecureString \
  --value "{password}"    # PAUSE — confirm before storing credentials

aws ssm put-parameter \
  --name "/{env_name}/itp-demo/totp-secret" \
  --type SecureString \
  --value "{totp_secret}"
```

#### Configure Entity Risk Policy (from Section 7 risk rules)

If entity risk policy rules are defined:

```bash
# Import current policy
python3 modules/itp-demo/scripts/import_entity_risk_policy.py \
  --output environments/{env_name}/config/entity_risk_policy.json

# Check if HIGH risk rule exists, if not create one
# Apply policy
python3 scripts/apply_risk_rules.py \
  --config environments/{env_name}/config/risk_rules.json
```

### Phase 11: Validation

Run validation checks for each deployed component:

#### Quick Mode ITP Test (if ITP enabled)

```bash
python3 modules/itp-demo/scripts/trigger_itp_demo.py --mode quick \
  --user {test_email} --risk-level HIGH --monitor --auto-reset
```

Or via workflow:
```bash
gh workflow run itp-demo-trigger.yml \
  -f environment={env_name} -f mode=quick \
  -f user_email={test_email} -f risk_level=HIGH \
  -f auto_reset=true
```

#### SSF Mode Test (if SSF enabled)

```bash
python3 modules/itp-demo/scripts/trigger_itp_demo.py --mode ssf \
  --user {test_email} --risk-level HIGH --monitor --auto-reset
```

#### Real Mode Test (if Real mode enabled)

```bash
python3 modules/itp-demo/scripts/trigger_itp_demo.py --mode real \
  --user {test_email} \
  --password-ssm /{env_name}/itp-demo/password \
  --totp-ssm /{env_name}/itp-demo/totp-secret \
  --attacker-lambda itp-demo-session-replayer \
  --attacker-region {attacker_region} \
  --monitor --auto-reset
```

#### AD Health Check (if AD deployed)

```bash
gh workflow run ad-health-check.yml \
  -f environment={env_name} \
  -f region={aws_region}
```

#### DB Connectivity (if DB deployed)

```bash
gh workflow run generic-db-schema-init.yml \
  -f environment={env_name} \
  -f action=verify
```

#### OPA Connectivity (if OPA deployed)

```bash
gh workflow run opa-plan.yml -f environment={env_name}
```
A successful plan confirms OPA API connectivity.

### Phase 12: Summary

Print a deployment summary:

```
============================================================
DEPLOYMENT COMPLETE: {env_name}
============================================================

Environment: {env_name}
Okta Org:    {okta_org_name}.{okta_base_url}
Directory:   environments/{env_name}/

RESOURCES CREATED:
  Users:       {user_count}
  Groups:      {group_count}
  Apps:        {app_count}
  Policies:    {policy_count}

GOVERNANCE (if enabled):
  Entitlement-enabled apps: {entitlement_app_count}
  Campaigns:   {campaign_count}
  Owners:      {owner_status}
  Labels:      {label_status}

INFRASTRUCTURE (if deployed):
  AD:          {ad_status}
  Database:    {db_status}
  OPC Agent:   {opc_status}
  SCIM Server: {scim_status}
  OPA:         {opa_status}
  ITP Demo:    {itp_status}
  Federation:  {federation_status}

DEMO COMMANDS:
  ITP Quick:   python3 modules/itp-demo/scripts/trigger_itp_demo.py --mode quick --user {email} --monitor --auto-reset
  ITP SSF:     python3 modules/itp-demo/scripts/trigger_itp_demo.py --mode ssf --user {email} --monitor --auto-reset
  ITP Real:    python3 modules/itp-demo/scripts/trigger_itp_demo.py --mode real --user {email} --password-ssm /{env}/itp-demo/password --totp-ssm /{env}/itp-demo/totp-secret --monitor --auto-reset

MANUAL FOLLOW-UP STEPS:
  [ ] Create entitlement bundles after entitlements sync into apps (Admin UI or Terraform)
  [ ] Assign entitlement bundles to users/groups in Okta Admin UI
  [ ] Activate AD Agent (if deployed) — interactive browser login required
  [ ] Activate OPC Agent (if deployed) — interactive browser login required
  [ ] Configure SCIM app in Okta (if SCIM deployed)
  [ ] Test federation with partner org (if federation deployed)

DOCUMENTATION:
  Worksheet:   demo-builder/DEMO_WORKSHEET.md
  ITP Guide:   modules/itp-demo/docs/itp-demo.md
  AD Guide:    modules/ad-domain-controller/docs/active-directory.md
  API Scripts: docs/reference/api-management.md
  Workflows:   docs/reference/workflow-reference.md
============================================================
```

---

## Rules

These rules MUST be followed during deployment:

### Terraform Rules
- Use existing modules in `modules/` — do NOT create new Terraform resource definitions from scratch
- Use `$$` for all Okta template strings (e.g., `$${source.login}`) — see CLAUDE.md gotcha #1
- Entitlement values MUST be alphabetically ordered by `external_value` — see CLAUDE.md gotcha #11
- Use API token authentication, NOT OAuth — see CLAUDE.md gotcha #9
- For service apps: set `hide_ios = true`, `hide_web = true`, `login_mode = "DISABLED"`
- Infrastructure stacks go in separate directories (`ad-infrastructure/`, `generic-db-infrastructure/`, etc.)
- Each infrastructure stack has its own `provider.tf` with S3 backend

### Workflow Rules
- Use existing workflows in `.github/workflows/` — prefer workflows over local `terraform apply`
- Use existing scripts in `scripts/` — do NOT write new Python scripts
- PAUSE before every `terraform apply` or workflow that modifies infrastructure
- PAUSE before creating SSM parameters with credentials

### OPA Rules
- Always set `type = "default"` on `oktapam_security_policy_v2` resources
- Password checkout rules MUST come BEFORE SSH rules (API return order)
- `admin_level_permissions = true` CANNOT be combined with `sudo_command_bundles`
- `password_checkout_ssh` requires `account_selector_type = "username"`
- OPA API host is NOT `app.scaleft.com` — use `OKTAPAM_API_HOST` secret

### Governance Rules
- Entitlement bundles are per-app — they reference specific entitlement values synced into each application
- Bundles can only be created AFTER entitlements are synced into apps (not before)
- Bundle creation and user/group assignments are MANUAL (Okta Admin UI) or via Terraform (see RESOURCE_EXAMPLES.tf)
- Resource owners and labels use Python scripts (not Terraform provider)
- Labels use two-phase workflow (validate on PR, apply on merge)
- Store credentials as SSM SecureString only

### ITP Rules
- For real mode: create test user + enroll TOTP via API
- Store ITP credentials in SSM, never in Terraform state or config files
- Always auto-reset risk level after demo tests

---

## Key Workflows Used

| Phase | Workflow | Purpose |
|-------|----------|---------|
| 2, 3, 4 | `tf-apply.yml` | Apply Okta Terraform resources |
| 3 | `oig-owners.yml` | Sync and apply resource owners |
| 3 | `labels-apply.yml` | Apply governance labels |
| 3 | `oig-manage-entitlements.yml` | Enable entitlement management on apps |
| 3 | `oig-risk-rules-apply.yml` | Apply risk rules |
| 5 | `ad-deploy.yml` | Deploy AD Domain Controller |
| 5 | `ad-health-check.yml` | Verify AD health |
| 5 | `ad-install-okta-agent.yml` | Install Okta AD Agent |
| 6 | `generic-db-deploy.yml` | Deploy Generic DB infrastructure |
| 6 | `generic-db-schema-init.yml` | Initialize database schema |
| 6 | `opc-deploy.yml` | Deploy OPC Agent infrastructure |
| 6 | `opc-install-agent.yml` | Install OPC Agent software |
| 7 | `deploy-scim-server.yml` | Deploy SCIM server |
| 8 | `opa-plan.yml` | Plan OPA resources |
| 10 | `itp-ssf-provider-setup.yml` | Set up SSF provider |
| 10 | `itp-demo-trigger.yml` | Trigger ITP demo |
| 11 | Various | Validation checks |

---

## Troubleshooting

### Terraform Apply Fails

- **"Template interpolation" error**: Use `$$` for Okta template strings
- **"Inconsistent result after apply" on entitlements**: Check value ordering (must be alphabetical)
- **"Permission denied" creating OAuth apps**: Use API token auth, not OAuth
- **State lock timeout**: Run `terraform force-unlock {LOCK_ID}`

### OPA Drift

- **Perpetual plan changes**: Check `type = "default"` is set, rule ordering matches API (password checkout before SSH)
- **"admin_level_permissions" conflict**: Cannot combine with `sudo_command_bundles` in same privilege block

### AD Issues

- **Bootstrap timeout**: AD setup takes 5-10 minutes, wait for health check to pass
- **Agent activation fails**: Must use interactive browser login via SSM session

### Generic DB Issues

- **Entitlements not importing**: Enable "Provisioning to App" (downstream provisioning) — this is undocumented but required
- **JDBC driver not found**: Copy driver to `/opt/OktaOnPremScimServer/userlib/`

### SCIM Issues

- **401 on test connection**: Add "Bearer " prefix to token in Okta config
- **Entitlements not discovered**: Use `urn:okta:scim:schemas:core:1.0:Entitlement` (NOT standard IETF URN)

### ITP Issues

- **Quick mode not triggering**: Check entity risk policy has a HIGH risk rule
- **SSF mode fails**: Verify SSF provider setup completed successfully
- **Real mode login fails**: Check credentials in SSM, verify TOTP enrollment

---

## Dependency Order

Infrastructure components must be deployed in this order:

```
Phase 1: Bootstrap (always first)
Phase 2: Okta Resources (always second — groups needed by later phases)
Phase 3: Identity Governance (depends on Phase 2 apps and groups)
Phase 4: Lifecycle Management (depends on Phase 2 users and groups)
Phase 5: Active Directory (independent infrastructure)
Phase 6: Database + OPC (independent, but OPC needs DB VPC outputs)
Phase 7: SCIM Server (independent infrastructure)
Phase 8: OPA (depends on Phase 2 for group references, Phase 5/6 for server enrollment)
Phase 9: SAML Federation (depends on Phase 2 for group references)
Phase 10: ITP Demo (depends on Phase 2 for test user, Phase 7 for entity risk policy)
Phase 11: Validation (depends on all previous phases)
Phase 12: Summary (always last)
```
