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

## Section 7: Infrastructure (Optional)

### Do you need AWS infrastructure for your demo?
- [ ] No (skip this section)
- [ ] Yes

### Active Directory
- [ ] Deploy AD Domain Controller
- Domain name: ______________
- NetBIOS name: _____________

### SCIM Server
- [ ] Deploy SCIM test server

### Okta Privileged Access (OPA)
- [ ] Enable OPA resources

---

## Section 8: Output Preferences

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

### Option A: AI-Assisted (Recommended)

1. Copy this entire filled-out worksheet
2. Open ChatGPT, Claude, or Gemini
3. Paste this prompt:
   ```
   Generate a demo-config.yaml file from this worksheet for the Okta Terraform Demo Template repository. Output only the YAML, no explanations.

   [Paste your filled worksheet here]
   ```
4. Save the output as `demo-builder/my-demo.yaml`
5. Run: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`

### Option B: Manual

1. Copy `demo-builder/demo-config.yaml.template` to `demo-builder/my-demo.yaml`
2. Edit the YAML using your worksheet answers
3. Run: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`

### Option C: Use Pre-built Example

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
