# Getting Started

**You're here because you completed the [QUICKSTART.md](../QUICKSTART.md)!** 🎉

You've successfully:
- ✅ Created your repository from template
- ✅ Set up GitHub Environment with Okta credentials
- ✅ Imported your Okta organization into code

**Now what?** This guide covers your next steps.

---

## Table of Contents

1. [Understanding What You Have](#understanding-what-you-have)
2. [Setting Up Terraform State Backend](#setting-up-terraform-state-backend)
3. [Making Your First Change](#making-your-first-change)
4. [Applying Changes to Okta](#applying-changes-to-okta)
5. [Working with Multiple Environments](#working-with-multiple-environments)
6. [Daily Workflow](#daily-workflow)
7. [Next Steps](#next-steps)

---

## Understanding What You Have

Let's explore what the import created in your repository.

### Directory Structure

```
your-repo/
├── environments/
│   └── myfirstenvironment/        # Your environment
│       ├── terraform/             # Infrastructure as Code
│       │   ├── provider.tf        # Terraform & Okta provider config
│       │   ├── variables.tf       # Variable definitions
│       │   ├── oig_entitlements.tf   # Your entitlement bundles
│       │   └── oig_reviews.tf     # Your access review campaigns
│       ├── config/                # API-managed resources
│       │   ├── owner_mappings.json   # Resource owners
│       │   └── label_mappings.json   # Governance labels
│       └── imports/               # Raw API data (reference)
│           ├── entitlements.json  # Raw bundle data
│           └── reviews.json       # Raw review data
├── scripts/                       # Python automation scripts
├── .github/workflows/             # GitHub Actions workflows
└── docs/                          # Documentation (you are here)
```

### Three Types of Files

**1. Terraform Files (`.tf` extension)**
- Located in `environments/*/terraform/`
- Infrastructure as Code representing your Okta resources
- Can be applied to create, update, or delete resources
- Managed via GitOps workflow (PR → Review → Apply)
- **Example:** `oig_entitlements.tf` contains your entitlement bundle definitions

**2. Config Files (`.json` extension)**
- Located in `environments/*/config/`
- API-managed resources not yet in Terraform provider
- Applied via Python scripts and workflows
- **Example:** `owner_mappings.json` assigns owners to resources

**3. Import Files (`.json` extension)**
- Located in `environments/*/imports/`
- Raw API responses for audit and troubleshooting
- Read-only reference, not used in daily operations
- **Example:** `entitlements.json` shows original API data

---

## Setting Up Terraform State Backend

**⚠️ Important:** Before making changes, set up a state backend for team collaboration.

### Why You Need a Backend

**Without backend:** State stored locally, can't collaborate, no locking
**With backend:** Team collaboration, state locking, version history, disaster recovery

### Choose Your Backend

Click your situation:

**👤 Working alone? Testing only?**
→ [Local Backend](#option-1-local-backend-testing-only) (2 minutes)

**👥 Working with a team? Production use?**
→ [Backend Setup Wizard](./BACKEND_SETUP_WIZARD.md) (Choose AWS S3 or Terraform Cloud)

### Option 1: Local Backend (Testing Only)

For quick testing without team collaboration:

```bash
cd environments/myfirstenvironment/terraform

# Edit provider.tf and remove the backend "s3" block entirely
# Or comment it out:
# terraform {
#   # backend "s3" { ... }
# }

# Initialize
terraform init
```

**⚠️ Warning:** Local state cannot be shared with team. Use only for testing!

### Option 2: Team Backend

See [Backend Setup Wizard](./BACKEND_SETUP_WIZARD.md) for step-by-step guide to:
- **AWS S3** - Best for teams, full control
- **Terraform Cloud** - Easiest for individuals/small teams

---

## Making Your First Change

Let's make a simple change to see the GitOps workflow in action.

### Step 1: Create a Feature Branch

```bash
# Clone your repository (if not already)
git clone https://github.com/YOUR-USERNAME/your-repo.git
cd your-repo

# Create feature branch
git checkout -b feature/my-first-change
```

### Step 2: Make a Change

Let's add a description to an entitlement bundle:

```bash
# Open the entitlements file
cd environments/myfirstenvironment/terraform
vim oig_entitlements.tf
```

Find an entitlement bundle and add a description:

```hcl
resource "okta_entitlement_bundle" "example" {
  name        = "Existing Bundle Name"
  description = "This is my first change!"  # ← Add this line
  status      = "ACTIVE"

  # ... rest of configuration
}
```

### Step 3: Validate Locally

```bash
# Format the code
terraform fmt

# Validate syntax
terraform validate

# See what would change
terraform plan
```

**Expected output:**
```
Terraform will perform the following actions:

  # okta_entitlement_bundle.example will be updated in-place
  ~ resource "okta_entitlement_bundle" "example" {
      + description = "This is my first change!"
        # ...
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

### Step 4: Commit and Push

```bash
# Stage your changes
git add oig_entitlements.tf

# Commit with descriptive message
git commit -m "feat: Add description to example entitlement bundle

- Added descriptive text to help users understand bundle purpose
- This is my first change to test the GitOps workflow"

# Push to GitHub
git push -u origin feature/my-first-change
```

### Step 5: Create Pull Request

```bash
# Using GitHub CLI
gh pr create \
  --title "Add description to entitlement bundle" \
  --body "Testing GitOps workflow with a simple description change"

# Or use GitHub web UI:
# Go to your repository → Pull requests → New pull request
```

### Step 6: Review Automated Plan

GitHub Actions will automatically:
1. Run `terraform plan` on your PR
2. Post the results as a comment
3. Run validation checks

**Look for:**
- ✅ All checks passing (green)
- 📝 Plan output showing your change
- 👀 Review the plan carefully

### Step 7: Merge

Once the plan looks good:
1. Get approval (if required by branch protection)
2. Click **Merge pull request**
3. Delete the feature branch

**🎉 Congratulations!** You just completed your first GitOps change!

---

## Applying Changes to Okta

**⚠️ IMPORTANT:** Merging to main doesn't automatically apply changes to Okta. This is intentional for safety.

**What merging a PR does:**
- ✅ Updates your repository code
- ✅ Triggers automatic `terraform plan` (shows what would change)
- ❌ **Does NOT** apply changes to Okta

**What you must do manually:**
- 🎯 Trigger `terraform-apply-with-approval.yml` workflow
- 🎯 Review and approve the apply (if environment protection configured)
- 🎯 Wait for apply to complete
- 🎯 Verify changes in Okta Admin Console

### Manual Apply Workflow

**Step 1: Trigger Apply Workflow**

```bash
gh workflow run terraform-apply-with-approval.yml \
  -f environment=myfirstenvironment
```

Or via GitHub web UI:
1. Go to **Actions** tab
2. Select **Terraform Apply with Approval**
3. Click **Run workflow**
4. Select your environment
5. Click green **Run workflow** button

**Step 2: Approval Gate (If Configured)**

If your environment has protection rules:
1. Approver receives notification
2. Reviews the plan output
3. Approves or rejects
4. Workflow continues or stops

**Step 3: Apply Runs**

Terraform applies your changes to Okta.

**Step 4: Verify in Okta**

1. Log into Okta Admin Console
2. Navigate to the resource you changed
3. Verify the change was applied

---

## Working with Multiple Environments

As you grow, you'll want separate environments for dev/staging/prod.

### Creating Additional Environments

**Step 1: Create Directory Structure**

```bash
# Create new environment
mkdir -p environments/myorg/{terraform,config,imports}

# Copy template files
cp environments/myorg/terraform/provider.tf environments/myorg/terraform/
cp environments/myorg/terraform/variables.tf environments/myorg/terraform/
```

**Step 2: Update Backend Configuration**

Edit `environments/myorg/terraform/provider.tf`:

```hcl
terraform {
  backend "s3" {
    bucket = "okta-terraform-demo"
    key    = "Okta-GitOps/production/terraform.tfstate"  # ← Change this!
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}
```

**Step 3: Create GitHub Environment**

1. Settings → Environments → New environment
2. Name: `Production`
3. Add protection rules:
   - ✅ Required reviewers (2+ for production)
   - ✅ Wait timer (5-10 minutes)
4. Add secrets: `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`

**Step 4: Import Production Resources**

```bash
gh workflow run import-all-resources.yml \
  -f tenant_environment=Production \
  -f update_terraform=true \
  -f commit_changes=true
```

### Environment Promotion Pattern

```
Development → Staging → Production
    ↓            ↓          ↓
  Test        Validate   Deploy
```

**Workflow:**
1. Make changes in development
2. Test thoroughly
3. Apply to development
4. Cherry-pick or replicate to staging
5. Test in staging (like production)
6. Apply to staging
7. Cherry-pick or replicate to production
8. Get approvals
9. Apply to production

---

## Daily Workflow

Once set up, here's your typical workflow:

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/add-new-users

# 2. Make changes
cd environments/myenv/terraform
vim users.tf  # Add new users

# 3. Validate
terraform fmt
terraform validate
terraform plan

# 4. Commit and push
git add users.tf
git commit -m "feat: Add marketing team users"
git push -u origin feature/add-new-users

# 5. Create PR
gh pr create

# 6. Review automated plan
# 7. Get approval and merge

# 8. Apply to Okta
gh workflow run terraform-apply-with-approval.yml -f environment=myenv
```

### Syncing from Okta (Drift Detection)

Detect manual changes made in Okta Admin Console:

```bash
# Run import to see what changed
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyEnv \
  -f update_terraform=false \
  -f commit_changes=false

# Review diff in workflow artifacts
# Decide: update Terraform or revert Okta changes
```

### Managing Governance Features

**Sync and apply resource owners:**
```bash
# Sync current state from Okta
python3 scripts/sync_owner_mappings.py \
  --output environments/myenv/config/owner_mappings.json

# Edit owners
vim environments/myenv/config/owner_mappings.json

# Apply to Okta
gh workflow run apply-owners.yml \
  -f environment=myenv \
  -f dry_run=false
```

**Manage governance labels:**
```bash
# Edit labels
vim environments/myenv/config/label_mappings.json

# Create PR (validates syntax)
git add config/label_mappings.json
git commit -m "feat: Add privileged access label"
gh pr create

# After merge, auto dry-run runs
# Review output, then manual apply
gh workflow run apply-labels-from-config.yml \
  -f environment=myenv \
  -f dry_run=false
```

---

## Next Steps

### Immediate Next Steps

1. **Set up backend** (if you haven't)
   → [Backend Setup Wizard](./BACKEND_SETUP_WIZARD.md)

2. **Understand architecture**
   → [02-ARCHITECTURE.md](./02-ARCHITECTURE.md)

3. **Learn workflows**
   → [03-WORKFLOWS-GUIDE.md](./03-WORKFLOWS-GUIDE.md)

### Common Tasks

**Build a demo environment**
→ [DEMO_BUILD_GUIDE.md](../DEMO_BUILD_GUIDE.md)

**Manage OIG features**
→ [04-OIG-FEATURES.md](./04-OIG-FEATURES.md)

**Troubleshoot issues**
→ [05-TROUBLESHOOTING.md](./05-TROUBLESHOOTING.md)

**Use AI to generate code**
→ [ai-assisted/README.md](../ai-assisted/README.md)

### Learning More

**Understand GitOps patterns:**
- [GitOps Workflow Guide](./GITOPS_WORKFLOW.md)
- [Workflows Reference](./WORKFLOWS.md)

**Deep dive into OIG:**
- [OIG Features Guide](./04-OIG-FEATURES.md)
- [Label Management Workflow](./LABEL_WORKFLOW_GUIDE.md)
- [OIG Prerequisites](../OIG_PREREQUISITES.md)

**Production deployment:**
- [Security Best Practices](../SECURITY.md)
- [Rollback Guide](./ROLLBACK_GUIDE.md)
- [AWS Backend Setup](./AWS_BACKEND_SETUP.md)

---

## Common Questions

### Q: Can I skip the backend setup?

**A:** For testing, yes. For production or team collaboration, no.

Local state works for learning but quickly becomes problematic:
- Can't collaborate with team
- No state locking (risk of corruption)
- No version history (can't rollback)
- No disaster recovery

See [Backend Setup Wizard](./BACKEND_SETUP_WIZARD.md) for easy setup.

### Q: How do I know what will change before applying?

**A:** Always run `terraform plan` first:

```bash
cd environments/myenv/terraform
terraform plan
```

GitHub Actions also runs plan automatically on PRs and posts results.

### Q: What if I make a mistake?

**A:** You have several recovery options:

1. **Just merged bad PR:** Revert the commit
2. **Already applied:** Rollback via Terraform
3. **State corrupted:** Restore from S3 versioning

See [Rollback Guide](./ROLLBACK_GUIDE.md) for details.

### Q: Why are entitlement assignments not in Terraform?

**A:** Terraform manages bundle **definitions**, not **assignments**.

User/group assignments must be managed in:
- Okta Admin Console (manual)
- Okta API (programmatic)

This is a provider limitation, not a bug.

### Q: How do I add more entitlement bundles?

**A:** Two ways:

**Option 1: Import existing from Okta**
```bash
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyEnv
```

**Option 2: Create new in Terraform**
```hcl
resource "okta_entitlement_bundle" "new_bundle" {
  name   = "My New Bundle"
  status = "ACTIVE"
  # ... configuration
}
```

### Q: Where do I find workflow documentation?

**A:**
- Quick reference: [03-WORKFLOWS-GUIDE.md](./03-WORKFLOWS-GUIDE.md)
- Detailed docs: [WORKFLOWS.md](./WORKFLOWS.md)
- GitOps patterns: [GITOPS_WORKFLOW.md](./GITOPS_WORKFLOW.md)

---

## Getting Help

**Stuck? Need help?**

1. Check [05-TROUBLESHOOTING.md](./05-TROUBLESHOOTING.md)
2. Search [GitHub Issues](https://github.com/joevanhorn/okta-terraform-demo-template/issues)
3. Ask in [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions)
4. Review [working example repo](https://github.com/joevanhorn/okta-terraform-complete-demo)

**Found a bug or have a suggestion?**
[Create an issue](https://github.com/joevanhorn/okta-terraform-demo-template/issues/new)!

---

## Summary

You now know how to:
- ✅ Understand the repository structure
- ✅ Set up a state backend
- ✅ Make your first change via GitOps
- ✅ Apply changes to Okta
- ✅ Work with multiple environments
- ✅ Follow the daily workflow

**Next:** Choose your learning path from [docs/00-README.md](./00-README.md)!
