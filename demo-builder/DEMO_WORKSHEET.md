# Demo Environment Worksheet

Fill out this worksheet to define your Okta demo environment. You can then:
1. **Use with AI**: Paste this to ChatGPT, Claude, or Gemini with the prompt from `ai-assisted/prompts/generate_demo_config.md`
2. **Convert manually**: Use the answers to fill out `demo-config.yaml.template`

---

## Section 1: Environment Basics

**Environment name** (lowercase, no spaces - used for directory name):
```
_______________________
```

**Email domain** (for auto-generated user emails, e.g., "example.com" or "dept.company.com"):
```
_______________________
```
*Note: Subdomains are supported (e.g., "healthcare.example.com")*

**Company/Demo name**:
```
_______________________
```

**Industry** (check one):
- [ ] Healthcare
- [ ] Financial Services
- [ ] Technology / SaaS
- [ ] Retail / E-commerce
- [ ] Manufacturing
- [ ] Government
- [ ] Education
- [ ] Media / Entertainment
- [ ] Other: _____________

**Company size**:
- [ ] Small (< 50 users)
- [ ] Medium (50-500 users)
- [ ] Large (500-5000 users)
- [ ] Enterprise (5000+ users)

---

## Section 2: Organizational Structure

### Departments

List your departments. Each department will have a manager and employees.

| # | Department Name | Manager Name | Manager Title | # of Employees | Employee Title Pattern |
|---|-----------------|--------------|---------------|----------------|------------------------|
| 1 | ______________ | ____________ | _____________ | ______________ | ______________________ |
| 2 | ______________ | ____________ | _____________ | ______________ | ______________________ |
| 3 | ______________ | ____________ | _____________ | ______________ | ______________________ |
| 4 | ______________ | ____________ | _____________ | ______________ | ______________________ |
| 5 | ______________ | ____________ | _____________ | ______________ | ______________________ |

**Example:**
| # | Department Name | Manager Name | Manager Title | # of Employees | Employee Title Pattern |
|---|-----------------|--------------|---------------|----------------|------------------------|
| 1 | Engineering | Jane Smith | VP of Engineering | 5 | Software Engineer |
| 2 | Marketing | Mike Jones | Marketing Director | 3 | Marketing Specialist |
| 3 | Finance | Carol CFO | Chief Financial Officer | 2 | Financial Analyst |

*Note: At least one department is required. Auto-generated employees will be named like "Eng01_Employee", "Eng02_Employee" with titles like "Software Engineer 1", "Software Engineer 2".*

### Specific Employees (Optional)

If you need specific employee names (instead of auto-generated), list them here:

| Department | First Name | Last Name | Title | Email (optional) |
|------------|------------|-----------|-------|------------------|
| __________ | __________ | _________ | _____ | ________________ |
| __________ | __________ | _________ | _____ | ________________ |
| __________ | __________ | _________ | _____ | ________________ |
| __________ | __________ | _________ | _____ | ________________ |

### Additional Users

Users outside the department structure (contractors, executives, etc.):

| First Name | Last Name | Title | User Type | Department (if any) |
|------------|-----------|-------|-----------|---------------------|
| __________ | _________ | _____ | _________ | ___________________ |
| __________ | _________ | _____ | _________ | ___________________ |
| __________ | _________ | _____ | _________ | ___________________ |

**User Types:** employee, contractor, intern, vendor

---

## Section 3: Groups

Department groups are created automatically. List any additional groups needed:

| Group Name | Description | Include |
|------------|-------------|---------|
| __________ | ___________ | _______ |
| __________ | ___________ | _______ |
| __________ | ___________ | _______ |

**Include options:**
- All managers
- Specific departments (comma-separated)
- Specific user types (contractor, intern, etc.)
- Specific titles

**Example:**
| Group Name | Description | Include |
|------------|-------------|---------|
| Leadership | Department heads and executives | All managers |
| Contractors | External contractors | User type: contractor |
| All Employees | Everyone | Departments: Engineering, Marketing, Finance |

---

## Section 4: Applications

List the applications for your demo:

| App Name | App Type | Display Label | Assign to Groups | Redirect URI |
|----------|----------|---------------|------------------|--------------|
| ________ | ________ | _____________ | ________________ | ____________ |
| ________ | ________ | _____________ | ________________ | ____________ |
| ________ | ________ | _____________ | ________________ | ____________ |
| ________ | ________ | _____________ | ________________ | ____________ |

**App Types:**
- `oauth_web` - Server-side web application (most common)
- `oauth_spa` - Single page app (React, Vue, Angular)
- `oauth_service` - Backend API / machine-to-machine
- `oauth_native` - Mobile or desktop app
- `saml` - Enterprise SSO with SAML

**Example:**
| App Name | App Type | Display Label | Assign to Groups | Redirect URI |
|----------|----------|---------------|------------------|--------------|
| salesforce | oauth_web | Salesforce CRM | Marketing, Leadership | https://login.salesforce.com/callback |
| github | oauth_web | GitHub Enterprise | Engineering | https://github.example.com/callback |
| admin_portal | oauth_spa | Admin Dashboard | Leadership | https://admin.example.com/callback |
| payment_api | oauth_service | Payment API | (none - service app) | (not needed) |

---

## Section 5: OIG Features (Optional)

### Do you have Okta Identity Governance license?
- [ ] Yes
- [ ] No (skip this section)

### Entitlement Bundles

Define access packages (bundle assignments are done in Okta Admin UI):

| Bundle Name | Description |
|-------------|-------------|
| ___________ | ___________ |
| ___________ | ___________ |
| ___________ | ___________ |

**Example:**
| Bundle Name | Description |
|-------------|-------------|
| Basic Employee Access | Standard access for all employees |
| Engineering Tools | Developer tools and source code access |
| Financial Systems | Access to financial applications |

### Access Review Campaigns

Schedule periodic access certifications:

| Campaign Name | Start Date | End Date | Reviewer Type |
|---------------|------------|----------|---------------|
| _____________ | __________ | ________ | _____________ |
| _____________ | __________ | ________ | _____________ |

**Reviewer Types:** MANAGER, APPLICATION_OWNER

**Example:**
| Campaign Name | Start Date | End Date | Reviewer Type |
|---------------|------------|----------|---------------|
| Q1 2025 Access Review | 2025-01-15 | 2025-02-15 | MANAGER |
| Q2 2025 Access Review | 2025-04-15 | 2025-05-15 | MANAGER |

---

## Section 6: Policies (Optional)

### Sign-On Policies

| Policy Name | Apply to Groups | Require MFA? |
|-------------|-----------------|--------------|
| ___________ | _______________ | ____________ |
| ___________ | _______________ | ____________ |

**Example:**
| Policy Name | Apply to Groups | Require MFA? |
|-------------|-----------------|--------------|
| MFA Required for Admins | Leadership | Yes |

### Password Policy

| Setting | Value |
|---------|-------|
| Minimum length | ______ |
| Require lowercase? | Yes / No |
| Require uppercase? | Yes / No |
| Require number? | Yes / No |
| Require symbol? | Yes / No |

---

## Section 7: Active Directory Infrastructure (Optional)

### Deploy AD Domain Controller?
- [ ] No (skip this section)
- [ ] Yes

**Domain configuration:**

| Setting | Value |
|---------|-------|
| AD domain name (e.g., corp.demo.local) | _________________ |
| NetBIOS name (e.g., CORP) | _________________ |
| AWS region(s) | _________________ |
| Instance type | `t3.medium` (default) |

**OU structure** (check all that apply):
- [ ] Use default OUs (Company > Users/Groups/Computers/Service Accounts)
- [ ] Custom OUs (list below):
  - ________________
  - ________________
  - ________________

**Create sample users?**
- [ ] Yes (recommended -- creates 22 users across 7 departments)
- [ ] No

**Install Okta AD Agent?**
- [ ] Yes (installer will be pre-downloaded; requires interactive browser activation)
- [ ] No

---

## Section 8: Generic Database Connector (Optional)

### Deploy Generic DB Connector?
- [ ] No (skip this section)
- [ ] Yes

| Setting | Value |
|---------|-------|
| Database engine | PostgreSQL (default) |
| Instance class (e.g., db.t3.micro) | _________________ |
| Database name | _________________ |
| AWS region | _________________ |

**Sample data:**

| Setting | Value |
|---------|-------|
| Number of sample users | ______ (default: 50) |
| Departments for sample users | _________________ |

**Entitlements / Roles to define:**

| Role Name | Description |
|-----------|-------------|
| _________ | ___________ |
| _________ | ___________ |
| _________ | ___________ |
| _________ | ___________ |

*Example: Administrator, Standard User, Read Only, Support Agent, Billing Manager*

**OPC Agents:**

| Setting | Value |
|---------|-------|
| Number of OPC agents | ______ (1 for single, 2 for HA) |
| Agent instance type | `t3.medium` (default) |
| Use pre-built AMI? | [ ] Yes  [ ] No (install from scratch) |

**Write-back requirements:**
- [ ] Create users in DB when provisioned from Okta
- [ ] Update users in DB when profile changes in Okta
- [ ] Deactivate users in DB when deprovisioned from Okta
- [ ] All of the above (full JML lifecycle)

---

## Section 9: Okta Privileged Access (Optional)

### Enable OPA?
- [ ] No (skip this section)
- [ ] Yes

**Security policy tiers** (check all that apply):
- [ ] Read-Only (view logs, system status)
- [ ] Operator (restart services, manage jobs)
- [ ] Admin (full access, create/delete resources)
- [ ] Database Admin (database tools, password checkout)
- [ ] Custom tier: _________________________

**Which servers need PAM enrollment?**
- [ ] AD Domain Controller(s)
- [ ] SCIM Server
- [ ] OPC Agent instances
- [ ] OPA Gateway
- [ ] Other: _________________________

**Password checkout:**
- [ ] Enable password checkout for service accounts
- [ ] Not needed

**OPA Gateway:**
- [ ] Deploy OPA Gateway on EC2
- [ ] Not needed (agent-only)

---

## Section 10: SCIM Server (Optional)

### Deploy SCIM Server?
- [ ] No (skip this section)
- [ ] Yes

| Setting | Value |
|---------|-------|
| Domain name (e.g., scim.demo.example.com) | _________________ |
| Route53 Zone ID | _________________ |
| Instance type | `t3.micro` (default) |
| Authentication mode | [ ] Bearer token  [ ] Basic auth |

**Custom entitlements:**
- [ ] Use default roles (5 standard roles)
- [ ] Use custom entitlements file: ________________

---

## Section 11: Deployment Preferences

| Setting | Value |
|---------|-------|
| AWS region (primary) | _________________ |
| Environment name prefix | _________________ |
| S3 state bucket name | _________________ |
| Deployment approach | [ ] All at once  [ ] Incremental (Okta first, then infra) |

**GitHub Environment setup:**
- [ ] Create GitHub Environment with secrets automatically
- [ ] I'll set up GitHub Environment manually

**Required GitHub Environment secrets** (for reference):

| Secret | Purpose |
|--------|---------|
| `OKTA_ORG_NAME` | Okta org (e.g., your-org) |
| `OKTA_BASE_URL` | Okta domain (e.g., okta.com) |
| `OKTA_API_TOKEN` | Okta API token |
| `AWS_ROLE_ARN` | AWS OIDC role for GitHub Actions |
| `OKTAPAM_KEY` | OPA API key (if OPA enabled) |
| `OKTAPAM_SECRET` | OPA API secret (if OPA enabled) |
| `OKTAPAM_TEAM` | OPA team name (if OPA enabled) |

---

## Section 12: Output Preferences

**Output format:**
- [ ] Separate files (users.tf, groups.tf, apps.tf, etc.) - Recommended
- [ ] Single file (demo.tf)

**Include comments in generated code?**
- [ ] Yes (recommended for learning)
- [ ] No (cleaner code)

**Run validation after generation?**
- [ ] Yes (recommended)
- [ ] No

---

## Next Steps

Once you've filled out this worksheet:

### Option A: Claude Code Full Deployment (Recommended)

The fastest path -- Claude Code deploys everything end-to-end.

1. Open Claude Code in this repository
2. Paste this prompt along with your completed worksheet:
   ```
   I have a completed Demo Deployment Worksheet. Please deploy the full
   environment following the instructions in ai-assisted/prompts/deploy_full_environment.md.

   HERE IS MY COMPLETED WORKSHEET:
   [Paste your filled worksheet here]
   ```
3. Claude Code will create all Terraform, deploy infrastructure, and verify
4. Review and approve each `terraform apply` as prompted

See [Full Environment Deployment Prompt](../ai-assisted/prompts/deploy_full_environment.md) for details.

### Option B: AI-Assisted YAML Generation

Generate a YAML config from the worksheet using any AI, then build.

1. Copy this entire filled-out worksheet
2. Open ChatGPT, Claude, or Gemini
3. Paste this prompt:
   ```
   Generate a demo-config.yaml file from this worksheet for the Okta Terraform Demo Template repository. Output only the YAML, no explanations.

   [Paste your filled worksheet here]
   ```
4. Save the output as `demo-builder/my-demo.yaml`
5. Run: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`

### Option C: Manual

1. Copy `demo-builder/demo-config.yaml.template` to `demo-builder/my-demo.yaml`
2. Edit the YAML using your worksheet answers
3. Run: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`

### Option D: Use Pre-built Example

1. Browse `demo-builder/examples/` for similar scenarios
2. Copy and customize
3. Run: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`

---

## Tips

1. **Start small** - Begin with 1-2 departments and expand later
2. **Use realistic names** - Makes demos more relatable
3. **Don't overthink user counts** - You can always add more later
4. **Choose industry-appropriate apps** - Healthcare = Epic, Finance = Bloomberg, etc.
5. **Skip OIG initially** - Add entitlements after basic demo works

---

*Worksheet version: 1.0*
*For help: See demo-builder/README.md*
