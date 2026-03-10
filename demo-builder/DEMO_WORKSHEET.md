# Demo Environment Deployment Worksheet

Fill out this worksheet and paste it into Claude Code to deploy a complete Okta demo environment.
Only fill in what you need — sections are progressive. Sections 1-4 are required; everything else is optional.

---

## Part 1: Okta Basics (Required)

### Section 1: Environment & Company

**Environment name** (lowercase, no spaces — used for directory and resource naming):
```
example-corp
```

**Okta org name** (subdomain only, e.g., "dev-12345678" or "mycompany"):
```
_______________________
```

**Okta base URL** (okta.com for production, oktapreview.com for developer/sandbox):
```
okta.com
```

**Email domain** (for auto-generated user emails):
```
example-corp.com
```

**Company name** (used in resource descriptions):
```
Example Corp
```

**Industry** (used for realistic demo scenario):
```
Technology
```
Options: Technology, Financial Services, Healthcare, Retail, Manufacturing, Government, Education, Other

**Company size** (affects number of default groups and complexity):
```
Medium (100-500)
```
Options: Small (< 100), Medium (100-500), Large (500-5000), Enterprise (5000+)

---

### Section 2: Users & Organization

#### Departments

Define departments and how many users to auto-generate per department.

| Department | Manager Count | Employee Count | Titles (comma-separated) |
|------------|--------------|----------------|--------------------------|
| Engineering | 1 | 5 | Software Engineer, Senior Engineer, Staff Engineer, QA Engineer |
| Marketing | 1 | 3 | Marketing Manager, Content Specialist, Campaign Manager |
| Sales | 1 | 4 | Account Executive, Sales Manager, SDR, Solutions Engineer |
| Finance | 1 | 2 | Financial Analyst, Controller |
| HR | 1 | 2 | HR Generalist, Recruiter |
| IT | 1 | 3 | Systems Administrator, Help Desk Analyst, Network Engineer |

#### Specific Employees (optional)

Add named employees when you need specific people in your demo.

| First Name | Last Name | Email | Department | Title | User Type | Manager Email |
|-----------|-----------|-------|-----------|-------|-----------|---------------|
| | | | | | | |

#### Additional Users (optional)

| Category | Count | Details |
|----------|-------|---------|
| Contractors | 0 | User type: Contractor, expiration: 90 days |
| Executives (C-suite) | 0 | CEO, CTO, CFO, CISO |
| Service accounts | 0 | For API integrations |

---

### Section 3: Groups

Department groups are auto-created from Section 2. Define additional groups here.

| Group Name | Description | Rule (who gets added) |
|-----------|-------------|----------------------|
| All Employees | All full-time employees | User type = Employee |
| All Contractors | All contractors | User type = Contractor |
| All Managers | All department managers | Title contains "Manager" or "Director" or "VP" |
| IT-Admins | IT administrators | Department = IT AND Title contains "Admin" |

---

### Section 4: Applications

| App Name | Type | Label | Assigned Groups | Notes |
|----------|------|-------|-----------------|-------|
| Salesforce | saml | Salesforce | Sales, All Managers | Enterprise SSO |
| Slack | oauth_web | Slack Enterprise | All Employees | redirect_uri: https://slack.com/oauth/callback |
| GitHub | oauth_web | GitHub Enterprise | Engineering | redirect_uri: https://github.com/oauth/callback |
| ServiceNow | saml | ServiceNow | IT, All Managers | ITSM platform |
| Workday | saml | Workday HCM | HR, All Managers | HR system |

**App types**: `oauth_web`, `oauth_spa`, `oauth_service`, `oauth_native`, `saml`

---

## Part 2: Identity Governance (Optional — requires OIG license)

### Section 5: Entitlements, Reviews & Governance

**Enable OIG features?**
```
Yes
```

#### Entitlement Management

Entitlement bundles are built **per-app** from entitlement values that are synced into each application. The workflow is:

1. Apps are deployed (Section 4)
2. Entitlement management is enabled on each app (API call)
3. Entitlements are imported/synced from their source (SCIM connector, Generic DB Connector, etc.)
4. Bundles are created in Okta Admin UI or Terraform, referencing specific app entitlements

Which apps from Section 4 should have entitlement management enabled?

| App Name | Enable Entitlements? | Entitlement Source |
|----------|---------------------|-------------------|
| Salesforce | Yes | Okta integration (automatic) |
| Slack | No | — |
| GitHub | No | — |
| ServiceNow | Yes | Okta integration (automatic) |
| Workday | Yes | Okta integration (automatic) |

**Entitlement source options**: `Okta integration (automatic)`, `SCIM server (Section 11)`, `Generic DB Connector (Section 10)`, `Manual`

Note: Entitlement bundles are created **after** entitlements are synced into apps — not before. Bundle definitions and user/group assignments are managed in Okta Admin UI or via Terraform once entitlements are available. See `RESOURCE_EXAMPLES.tf` for the `okta_entitlement_bundle` Terraform pattern.

#### Access Review Campaigns

| Campaign Name | Start Date | End Date | Reviewer Type |
|---------------|-----------|----------|---------------|
| Q1 Access Review | 2025-01-15 | 2025-02-15 | MANAGER |
| Privileged Access Review | 2025-01-01 | 2025-01-31 | APP_OWNER |

#### Resource Owners

**Enable resource owners?**
```
Yes
```

**Owner assignment strategy:**
```
Auto-assign app owners based on primary group assignment
```
Options: Auto-assign app owners based on primary group assignment, Manual mapping (provide config/owner_mappings.json), Skip

#### Governance Labels

**Enable governance labels?**
```
Yes
```

**Label admin entitlements automatically?**
```
Yes
```

#### Entitlement Management Settings

**Auto-enable entitlement management on apps?**
```
Yes
```

#### Risk Rules / SOD Policies

**Enable risk rules?**
```
No
```

If Yes, define rules:

| Rule Name | Description | Condition |
|-----------|-------------|-----------|
| | | |

---

### Section 6: Lifecycle Management

**Enable Joiner/Mover/Leaver lifecycle management?**
```
No
```

If Yes, configure:

| Feature | Enable? |
|---------|---------|
| Joiner workflows (new hire onboarding) | Yes |
| Mover workflows (department transfers) | Yes |
| Leaver workflows (offboarding) | Yes |
| Contractor lifecycle (expiration tracking) | Yes |
| OIG integration (entitlement bundles for lifecycle) | No |

**Organization name** (for lifecycle resource naming):
```
Example Corp
```

**User types to create:**

| User Type Name | Display Name | Description |
|---------------|-------------|-------------|
| Employee | Employee | Full-time employee |
| Contractor | Contractor | External contractor |

**Contractor lifecycle settings:**

| Setting | Value |
|---------|-------|
| Warning notification (days before expiration) | 30 |
| Final notice (days before expiration) | 7 |

**Create lifecycleStatus profile attribute?**
```
Yes
```

**Departments to auto-assign groups** (pulls from Section 2 by default):
```
Use departments from Section 2
```

---

## Part 3: Security (Optional)

### Section 7: Policies

#### Sign-On Policies

| Policy Name | Assigned Groups | MFA Required? | Allow Passwordless? |
|-------------|----------------|---------------|-------------------|
| Default Policy | Everyone | No | No |
| Secure Access | All Employees | Yes | Yes |
| Admin Access | IT-Admins | Yes (always) | No |

#### Password Policies

| Policy Name | Min Length | Complexity | Expiry (days) | Lockout Attempts |
|-------------|-----------|-----------|---------------|-----------------|
| Default | 8 | Low | 90 | 10 |
| High Security | 12 | High | 60 | 5 |

#### Entity Risk Policy Rules (for ITP)

| Risk Level | Terminate Sessions? | Challenge with MFA? |
|------------|--------------------|--------------------|
| HIGH | Yes | Yes |
| MEDIUM | No | Yes |

---

### Section 8: Identity Threat Protection (ITP)

**Enable ITP demo?** (requires ITP license on org)
```
No
```

If Yes, configure:

#### Demo Modes

| Mode | Enable? | What It Does |
|------|---------|-------------|
| Quick | Yes | Admin API sets user risk — instant, no infrastructure needed |
| SSF | No | Signed JWT signal via Security Events API — needs Lambda |
| Real | No | Session hijacking simulation — needs Lambda + test user |

#### ITP Settings

| Setting | Value |
|---------|-------|
| Attacker region (for Lambda) | eu-west-1 |
| Video recording S3 bucket | No |
| Video retention (days) | 90 |

#### Test User for Real Mode (required if Real mode enabled)

| Setting | Value |
|---------|-------|
| Test user email | itp-demo-test@example-corp.com |
| Create test user via API? | Yes |

Note: Claude Code will create the user, set a password, enroll TOTP, and store credentials in SSM Parameter Store.

---

## Part 4: Infrastructure (Optional — requires AWS)

### Section 9: Active Directory

**Deploy AD Domain Controller on AWS?**
```
No
```

If Yes, configure:

| Setting | Value | Module Variable |
|---------|-------|-----------------|
| AD domain name | corp.example-corp.local | `ad_domain_name` |
| NetBIOS name | CORP | `ad_netbios_name` |
| AWS region | us-east-1 | `aws_region` |
| Region short code | use1 | `region_short` |
| Instance type | t3.medium | `instance_type` |
| Create sample users/OUs | Yes | `create_sample_users` |
| Create new VPC | Yes | `create_vpc` |
| VPC CIDR | 10.0.0.0/16 | `vpc_cidr` |
| Enable RDP access | No | `enable_rdp` |
| Assign Elastic IP | No | `assign_elastic_ip` |

**Install Okta AD Agent?**
```
Yes
```
Note: AD Agent installation is automated via SSM, but the agent activation requires interactive browser login. Claude Code will run the install workflow and give you instructions for activation.

---

### Section 10: Database Connector & OPC Agents

**Deploy Generic Database Connector?**
```
No
```

If Yes, configure:

#### Database Settings

| Setting | Value |
|---------|-------|
| Database engine | PostgreSQL |
| RDS instance class | db.t3.micro |
| Database name | okta_connector |
| VPC CIDR | 10.5.0.0/16 |

#### Database Roles / Entitlements

Define roles that will be provisioned in the database and surfaced as entitlements in Okta.

| Role Name | Description |
|-----------|-------------|
| read_only | Read-only access to application data |
| read_write | Read and write access to application data |
| admin | Full administrative access |
| reports | Access to reporting views |

#### OPC Agent Settings

| Setting | Value | Module Variable |
|---------|-------|-----------------|
| Number of agents | 1 | `instance_number` |
| Instance type | t3.medium | `instance_type` |
| Connector type | generic-db | `connector_type` |
| Use prebuilt AMI | No | `use_prebuilt_ami` |

#### Write-Back (Provisioning to App)

| Capability | Enable? |
|-----------|---------|
| Create users in database | Yes |
| Update users in database | Yes |
| Deactivate users in database | Yes |

Note: Write-back requires "Provisioning to App" to be enabled in Okta. This is also required for entitlement import to work.

---

### Section 11: SCIM Server

**Deploy SCIM server for entitlement discovery?**
```
No
```

If Yes, configure:

| Setting | Value |
|---------|-------|
| Domain name | scim.demo-example-corp.example.com |
| Route53 Zone ID | _________________ |
| Instance type | t3.micro |
| Auth mode | Bearer token |

**Entitlements source:**
```
Use default roles
```
Options: Use default roles, Custom entitlements file (provide path)

Note: SCIM server enables Okta to discover entitlements from external systems for OIG governance.

---

### Section 12: Okta Privileged Access (OPA)

**Enable OPA?** (requires OPA license on org)
```
No
```

If Yes, configure:

#### Security Policy Tiers

| Tier | Enable? | OPA Group | Example Sudo Commands |
|------|---------|-----------|----------------------|
| Read-Only | Yes | PAM-ReadOnly-Users | tail, cat, less, ps, top, df, free, uptime |
| Operator | Yes | PAM-Operators | systemctl restart/stop/start, chmod, chown, rm /tmp/* |
| Database Admin | No | PAM-Database-Admins | psql, mysql, sqlplus, pg_dump, mysqldump |
| Full Admin | No | PAM_ADMINISTRATORS | All commands + admin_level_permissions |

#### Password Checkout

**Enable password checkout for service accounts?**
```
No
```

If Yes, which accounts?
```
root, postgres
```

#### OPA Gateway

**Deploy OPA Gateway on EC2?**
```
No
```

#### Server Enrollment

Which servers should be enrolled in OPA? (check all that apply)

| Server | Enroll? |
|--------|---------|
| AD Domain Controller | No |
| OPC Agents | No |
| SCIM Server | No |

Note: OPA credentials (`OKTAPAM_KEY`, `OKTAPAM_SECRET`, `OKTAPAM_TEAM`, `OKTAPAM_API_HOST`) must be set as GitHub Environment secrets before deployment.

---

## Part 5: Advanced (Optional)

### Section 13: SAML Federation

**Enable SAML federation?**
```
No
```

**Federation mode:**
```
sp
```
Options: `sp` (this org receives assertions from an external IdP), `idp` (this org sends assertions to a partner org)

#### SP Mode Settings (this org as Service Provider)

| Setting | Value |
|---------|-------|
| Federation name | Partner Federation |
| External IdP name | Partner IdP |
| IdP issuer / entity ID | _________________ |
| IdP SSO URL | _________________ |
| IdP certificate (PEM) | (provide file path or paste inline) |
| Enable JIT provisioning | Yes |
| Enable IdP routing rule | No |
| Routing domain suffix | _________________ |

#### IdP Mode Settings (this org as Identity Provider)

| Setting | Value |
|---------|-------|
| Federation name | Partner Federation |
| SAML app label | Federation to Partner |
| Partner org subdomain | _________________ |
| Partner ACS URL | _________________ |
| Partner audience / entity ID | _________________ |
| Assign to groups | All Employees |

---

## Part 6: Deployment

### Section 14: Deployment Configuration

| Setting | Value |
|---------|-------|
| AWS region (primary) | us-east-1 |
| S3 state bucket name | okta-terraform-demo |
| S3 state key prefix | Okta-GitOps |
| First environment in this repo? | No |
| GitHub Environment name | (same as environment name from Section 1) |

**Deployment approach:**
```
All at once
```
Options: All at once (deploy everything in one session), Incremental (deploy section by section, confirming each)

#### GitHub Secrets Reference

These secrets must be set on the GitHub Environment before deployment:

| Secret Name | Required? | Description |
|-------------|-----------|-------------|
| `OKTA_ORG_NAME` | Yes | Okta org subdomain |
| `OKTA_BASE_URL` | Yes | okta.com or oktapreview.com |
| `OKTA_API_TOKEN` | Yes | API token with Super Admin scope |
| `AWS_ROLE_ARN` | Yes (if using AWS) | IAM role ARN for GitHub OIDC |
| `OKTAPAM_KEY` | If OPA enabled | OPA service user key |
| `OKTAPAM_SECRET` | If OPA enabled | OPA service user secret |
| `OKTAPAM_TEAM` | If OPA enabled | OPA team name |
| `OKTAPAM_API_HOST` | If OPA enabled | OPA API host (NOT app.scaleft.com) |

---

## How to Deploy

1. Open Claude Code in the `ofcto-workforce-taskvantage` repository root
2. Paste this prompt:

   ```
   I have a completed Demo Deployment Worksheet. Please deploy the full
   environment following the instructions in
   ai-assisted/prompts/deploy_full_environment.md.

   HERE IS MY COMPLETED WORKSHEET:
   [Paste your filled worksheet here]
   ```

3. Claude Code will:
   - Parse the worksheet and validate your configuration
   - Create the environment directory structure
   - Generate Terraform for all Okta resources
   - Deploy infrastructure in dependency order
   - Configure governance (owners, labels, risk rules)
   - Set up ITP demo (if enabled)
   - Validate each component
4. Review and approve each `terraform apply` when prompted

---

## Tips

- **Start small**: Fill out Sections 1-4 only for your first run. You can always add infrastructure later.
- **Use real data**: Replace "example-corp" with your actual demo company name and domain.
- **Check licenses**: Sections 5-6 require OIG, Section 8 requires ITP, Section 12 requires OPA.
- **AWS prerequisites**: Sections 9-12 require an AWS account with the `AWS_ROLE_ARN` secret configured.
- **Federation needs a partner**: Section 13 requires coordination with another Okta org.
- **Keep the worksheet**: Save your filled-out worksheet — you can re-run it to recreate the environment.

---

*Worksheet version: 2.0*
*For help: See demo-builder/README.md or ai-assisted/prompts/deploy_full_environment.md*
