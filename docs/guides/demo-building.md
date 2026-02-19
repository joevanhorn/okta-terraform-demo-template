# Demo Build Guide

**Difficulty:** Beginner | **Time:** 30-60 minutes | **Prerequisites:** Okta API token

Build Okta demos quickly using Terraform with optional AI assistance.

---

## Choose Your Approach

| Approach | Time | Best For |
|----------|------|----------|
| [Quick Template](#quick-template-5-minutes) | 5 min | Testing, first demo |
| [AI-Assisted](#ai-assisted-demo-15-minutes) | 15 min | Custom demos, fast iteration |
| [Manual Build](#manual-build-30-minutes) | 30 min | Learning, full control |

**Recommendation:** Start with Quick Template to test setup, then use AI-Assisted for custom demos.

---

## Quick Template (5 minutes)

Use our pre-built demo template - no coding required.

### Step 1: Set Up Terraform (if not done)

Follow [LOCAL-USAGE.md](./LOCAL-USAGE.md) first if you haven't set up Terraform.

### Step 2: Use the Template

```bash
cd environments/myorg/terraform

# Copy the quickstart template
cp QUICKSTART_DEMO.tf.example demo.tf

# Edit the file
# 1. Uncomment ALL code blocks
# 2. Change @example.com to your email domain
```

### Step 3: Deploy

```bash
terraform init
terraform plan    # Review what will be created
terraform apply   # Type 'yes' to confirm
```

### What You Get

- **5 Users:** Marketing manager, sales rep, engineer, contractor, admin
- **3 Groups:** Marketing, Sales, Engineering
- **1 OAuth App:** Internal Portal with group assignments

### Clean Up

```bash
terraform destroy  # Type 'yes' to confirm
```

---

## AI-Assisted Demo (15 minutes)

Use AI to generate custom demos in seconds.

### Option A: Use Gemini Gem (Easiest)

If you have the Okta Terraform Gem set up:

1. **Open your Gem** at [gemini.google.com/gems](https://gemini.google.com/gems)
2. **Describe your demo:**
   ```
   Create a healthcare demo with:
   - 5 doctors and 3 nurses
   - Clinical Staff and Admin groups
   - Epic EHR OAuth application
   - Patient Portal SAML app
   ```
3. **Copy the generated code** to `environments/myorg/terraform/demo.tf`
4. **Deploy:** `terraform apply`

**Don't have the Gem?** See [ai-assisted/GEM_SETUP_GUIDE.md](./ai-assisted/GEM_SETUP_GUIDE.md)

### Option B: Use Any AI (ChatGPT, Claude, etc.)

1. **Open your AI assistant**
2. **Provide context** (paste these files):
   - `ai-assisted/context/terraform_examples.md`
   - `ai-assisted/context/okta_resource_guide.md`
3. **Describe your demo** (same as above)
4. **Copy code and deploy**

### Option C: Use CLI Tool

```bash
cd ai-assisted

# Set API key
export GEMINI_API_KEY="your-key"

# Generate
python generate.py \
  --prompt "Create healthcare demo with 5 doctors, 3 nurses, Epic EHR app" \
  --provider gemini \
  --output ../environments/myorg/terraform/demo.tf

# Deploy
cd ../environments/myorg/terraform
terraform apply
```

### Demo Scenario Ideas

| Industry | Users | Apps | Request Example |
|----------|-------|------|-----------------|
| **Healthcare** | Doctors, nurses, admins | Epic, Cerner, patient portal | "Healthcare org with HIPAA compliance needs" |
| **Finance** | Traders, analysts, compliance | Bloomberg, Salesforce, trading platform | "Investment firm with SOD requirements" |
| **Retail** | Store managers, associates, corporate | POS system, inventory, HR portal | "Multi-store retail chain" |
| **Tech Startup** | Engineers, product, sales | GitHub, Jira, Salesforce | "SaaS company with dev tools" |
| **Education** | Teachers, students, admins | Canvas LMS, library system | "University with student/staff separation" |

---

## Manual Build (30 minutes)

Build demos step-by-step for full control and learning.

### Step 1: Create Users

Create `environments/myorg/terraform/users.tf`:

```hcl
# Healthcare Demo Users
resource "okta_user" "dr_smith" {
  first_name = "Sarah"
  last_name  = "Smith"
  login      = "sarah.smith@example.com"
  email      = "sarah.smith@example.com"
  department = "Cardiology"
  title      = "Cardiologist"
  status     = "ACTIVE"
}

resource "okta_user" "nurse_jones" {
  first_name = "Michael"
  last_name  = "Jones"
  login      = "michael.jones@example.com"
  email      = "michael.jones@example.com"
  department = "Nursing"
  title      = "RN"
  status     = "ACTIVE"
}

# Add more users as needed
```

### Step 2: Create Groups

Create `environments/myorg/terraform/groups.tf`:

```hcl
resource "okta_group" "clinical_staff" {
  name        = "Clinical Staff"
  description = "Doctors and nurses with patient access"
}

resource "okta_group" "admin_staff" {
  name        = "Administrative Staff"
  description = "Non-clinical administrative personnel"
}

# Add users to groups
resource "okta_group_memberships" "clinical" {
  group_id = okta_group.clinical_staff.id
  users = [
    okta_user.dr_smith.id,
    okta_user.nurse_jones.id,
  ]
}
```

### Step 3: Create Applications

Create `environments/myorg/terraform/apps.tf`:

```hcl
# EHR System (OAuth)
resource "okta_app_oauth" "ehr_system" {
  label                      = "Epic EHR System"
  type                       = "web"
  grant_types                = ["authorization_code", "refresh_token"]
  redirect_uris              = ["https://ehr.example.com/callback"]
  response_types             = ["code"]

  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  # Internal app - hide from dashboard
  login_mode = "DISABLED"
  hide_ios   = true
  hide_web   = true

  # User mapping - note the double $$
  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"
}

# Assign app to clinical staff
resource "okta_app_group_assignment" "ehr_clinical" {
  app_id   = okta_app_oauth.ehr_system.id
  group_id = okta_group.clinical_staff.id
}
```

### Step 4: Deploy

```bash
cd environments/myorg/terraform
terraform fmt       # Format code
terraform validate  # Check syntax
terraform plan      # Review changes
terraform apply     # Deploy
```

### Step 5: Verify in Okta

1. **Users:** Directory → People
2. **Groups:** Directory → Groups
3. **Apps:** Applications → Applications

---

## Adding OIG Features

For Identity Governance demos (entitlement bundles, access reviews):

### Prerequisites

1. **OIG License** - Verify in Okta Admin Console
2. **Enable Entitlement Management** - Per-app in General tab
3. See [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md) for details

### Create Entitlement Bundles

```hcl
# Create bundle definition
resource "okta_entitlement_bundle" "patient_access" {
  name        = "Patient Data Access"
  description = "Access to view and edit patient records"
  status      = "ACTIVE"
}

resource "okta_entitlement_bundle" "admin_access" {
  name        = "Administrative Access"
  description = "Full administrative capabilities"
  status      = "ACTIVE"
}
```

**Important:** Bundles are DEFINITIONS only. Assigning bundles to users/groups is done in Okta Admin UI, not Terraform.

### Create Access Reviews

```hcl
resource "okta_reviews" "quarterly_review" {
  name        = "Q1 2025 Access Review"
  description = "Quarterly review of all user access"

  # Note: Schedule and scope configured in Okta Admin UI
  lifecycle {
    ignore_changes = [schedule, scope]
  }
}
```

---

## Demo Tips

### Before the Demo

- [ ] Run `terraform plan` to ensure no errors
- [ ] Note any credentials (app client IDs/secrets)
- [ ] Clear browser cache for clean Okta login
- [ ] Have Okta Admin Console open

### During the Demo

1. **Show the code** - Explain Infrastructure as Code value
2. **Run terraform plan** - Show what WILL be created
3. **Run terraform apply** - Watch resources appear
4. **Verify in Okta** - Show actual created resources
5. **Make a change** - Modify code and re-apply
6. **Cleanup** - Show `terraform destroy`

### Talking Points

- **Speed:** "I just created 10 users in 30 seconds"
- **Repeatability:** "I can recreate this demo in any org"
- **Audit trail:** "Every change is tracked in Git"
- **Consistency:** "No manual errors, same config every time"
- **Rollback:** "One command to undo everything"

---

## Common Patterns

### Multiple Environments

```bash
# Create production config
mkdir -p environments/production/terraform
cp environments/myorg/terraform/provider.tf environments/production/terraform/

# Set up GitHub Environment with production secrets
# Deploy: terraform apply in that directory
```

### Import Existing Resources

```bash
# Run import workflow (if using GitHub Actions)
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyOrg \
  -f update_terraform=true \
  -f commit_changes=true

# Or import manually
terraform import okta_user.existing "00u1234567890"
```

### Reset Demo

```bash
# Destroy all resources
terraform destroy

# Recreate
terraform apply
```

---

## Troubleshooting

### Common Errors

**"401 Unauthorized"**
- API token invalid or expired
- Create new token in Okta Admin Console

**"Resource already exists"**
- Delete in Okta Admin Console, or
- Import: `terraform import okta_user.name "ID"`

**Template interpolation error**
- Use `$$` not `$` for Okta templates
- `user_name_template = "$${source.login}"`

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more.

---

## Next Steps

### Learn More
- [TERRAFORM-BASICS.md](./TERRAFORM-BASICS.md) - Resource reference
- [LOCAL-USAGE.md](./LOCAL-USAGE.md) - Local Terraform setup
- [ai-assisted/README.md](./ai-assisted/README.md) - AI tools

### Add GitOps
- [GITHUB-BASIC.md](./GITHUB-BASIC.md) - Version control
- [GITHUB-GITOPS.md](./GITHUB-GITOPS.md) - Team collaboration

### Advanced Features
- [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md) - Identity Governance
- [docs/API_MANAGEMENT.md](./docs/API_MANAGEMENT.md) - Python scripts for owners/labels
