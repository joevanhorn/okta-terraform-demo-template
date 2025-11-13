# Quick Start - Your First Success in 10 Minutes

**Goal:** Import your Okta organization into code and see the results.

**No prior knowledge required** - Just follow these steps!

---

## 🧭 Which Guide Should I Follow?

**Choose your path based on your goal:**

### → **I just want to try this quickly** (10 minutes)
**You're in the right place!** Continue with this Quick Start guide below.
- **What you'll get:** Import your Okta org into code, see how it works
- **What you need:** GitHub account + Okta API token
- **Commitment:** ~10 minutes

### → **I want to set this up properly for production** (30-60 minutes)
**Use the comprehensive setup guide:** [TEMPLATE_SETUP.md](TEMPLATE_SETUP.md)
- **What you'll get:** Production-ready multi-environment setup with AWS backend
- **What you need:** AWS account + GitHub + Okta
- **Commitment:** 30-60 minutes for complete setup

### → **I need detailed secrets configuration help**
**See the secrets guide:** [SECRETS_SETUP.md](SECRETS_SETUP.md)
- Step-by-step GitHub Environment creation
- Detailed troubleshooting for secret issues
- Case-sensitivity warnings and examples

---

## ⚠️ CRITICAL: Before You Start

**GitHub Environment and Secret Names are CASE-SENSITIVE and must match EXACTLY.**

### Common Mistakes That Will Cause Failures:

| What You Create | What You Type in Workflow | Result |
|----------------|---------------------------|--------|
| Environment: `myfirstenv` | Workflow input: `MyFirstEnv` | ❌ **FAILS** |
| Environment: `Production` | Workflow input: `production` | ❌ **FAILS** |
| Secret: `okta_api_token` | Expected: `OKTA_API_TOKEN` | ❌ **FAILS** |

### ✅ Success Pattern:
1. **Environment Name:** Remember exactly how you type it (e.g., `MyFirstEnvironment`)
2. **Workflow Input:** Must match EXACTLY (including capitalization)
3. **Secret Names:** Must be UPPERCASE: `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`

**📝 Pro Tip:** Write down your environment name before you create it!

---

## ⏱️ Time Breakdown

- Prerequisites check: 2 minutes
- GitHub setup: 3 minutes
- Run import: 2 minutes
- View results: 3 minutes

**Total: ~10 minutes**

---

## Step 1: Pre-Flight Validation (2 minutes)

**Complete this validation BEFORE creating any GitHub resources to ensure success.**

### ✅ Pre-Flight Checklist

**Complete ALL items before proceeding:**

- [ ] **GitHub account** with Actions enabled (free tier is fine)
  - [ ] Verified you can create repositories
  - [ ] Verified GitHub Actions is enabled (Settings → Actions → General)
  - [ ] **⚠️ Write down your exact username** (case-sensitive!)

- [ ] **Okta organization** access:
  - [ ] Have admin access to an Okta organization
  - [ ] **⚠️ Write down your org name** (e.g., `dev-12345678` from URL)
  - [ ] **⚠️ Write down your base URL** (e.g., `okta.com`, `oktapreview.com`)
  - Options:
    - Okta developer account (free: https://developer.okta.com/signup/)
    - Preview organization
    - Production organization (test in dev/staging first!)

- [ ] **Okta API token** created and tested:
  - [ ] Token has these minimum permissions:
    - `okta.groups.manage`
    - `okta.users.manage`
    - `okta.apps.manage`
    - `okta.governance.*` (if using OIG features)
  - [ ] **⚠️ Token copied to secure location** (you won't see it again!)
  - [ ] **Validation:** Test your token works (see validation step below)

### 🔍 Validate Your API Token (Recommended)

Before setting up GitHub, verify your Okta API token works:

```bash
# Replace with your actual values
export OKTA_ORG_NAME="dev-12345678"
export OKTA_BASE_URL="okta.com"
export OKTA_API_TOKEN="your-token-here"

# Test the token
curl -X GET \
  "https://${OKTA_ORG_NAME}.${OKTA_BASE_URL}/api/v1/users?limit=1" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Accept: application/json"
```

**Expected result:** JSON response with user data (or empty array if no users)

**❌ If you see an error:**
- `401 Unauthorized` → Token is invalid or expired, regenerate it
- `404 Not Found` → Org name or base URL is wrong
- `Connection refused` → Check your internet connection

**✅ Success:** Continue to Step 2

### 📝 Information Sheet

**Fill this out NOW (you'll need it in Step 2):**

```
Environment Name I'll Create: ________________
  (Example: MyFirstEnvironment, demo-env, test)
  ⚠️ Remember exact capitalization!

Okta Org Name: ________________
  (From URL: https://[THIS-PART].okta.com)

Okta Base URL: ________________
  (okta.com, oktapreview.com, or okta-emea.com)

Okta API Token: ________________
  (Keep this secure!)
```

### 🔑 How to Get Your Okta API Token

**If you don't have a token yet:**

1. Log into your **Okta Admin Console**
2. Navigate to **Security → API → Tokens**
3. Click **Create Token**
4. Name it: `Terraform GitOps`
5. Click **Create Token**
6. **⚠️ CRITICAL:** Copy the token IMMEDIATELY - you cannot retrieve it later!
   - If you lose it, you must create a new one
   - Store it securely (password manager recommended)

**✅ Token created?** Add it to your Information Sheet above, then continue.

**Need help with secrets setup?** See detailed guide: [SECRETS_SETUP.md](SECRETS_SETUP.md)

---

## Step 2: GitHub Setup (3 minutes)

### 2.1 Use This Template

Click the green **"Use this template"** button at the top of this page.

**Settings:**
- **Owner:** Your GitHub username or organization
- **Repository name:** `my-okta-gitops` (or your choice)
- **Visibility:** **Private** (recommended - contains config data)

Click **"Create repository from template"**

**✅ Success:** You should be redirected to your new repository

**❌ Error: "Template not available"**
- Solution: Make sure you're logged into GitHub
- Solution: Try using this direct link: [Create from template](https://github.com/joevanhorn/okta-terraform-demo-template/generate)

### 2.2 Create GitHub Environment

**⚠️ CRITICAL: Use the EXACT name from your Information Sheet (Step 1)**

In your new repository:

1. Click **Settings** tab (top menu, far right)
   - ❌ **Can't see Settings?** You may need repository admin permissions
2. In left sidebar, scroll down and click **Environments**
   - This is under "Code and automation" section
3. Click **New environment** button (green button, top right)
4. **Environment name:** Type the EXACT name from your Information Sheet
   - Example: `MyFirstEnvironment` (if that's what you wrote down)
   - **⚠️ Case matters!** `myfirstenvironment` ≠ `MyFirstEnvironment`
5. Click **Configure environment**

**✅ Success:** You see the environment configuration page with "Environment secrets" section

**❌ Error: Can't find Environments**
- GitHub Free accounts: Environments are available for public repos or private repos with Pro/Enterprise
- Workaround: Make your repo public temporarily, or use repository secrets instead (less secure)

### 2.3 Add Environment Secrets

**⚠️ Add secrets to your ENVIRONMENT, not repository secrets!**

**How to verify you're in the right place:**
- URL should include: `/settings/environments/YourEnvironmentName`
- Page title should show your environment name
- You should see "Environment secrets" section

---

**Secret 1: OKTA_API_TOKEN**

1. Scroll to **Environment secrets** section
2. Click **Add secret**
3. **Name:** Type exactly: `OKTA_API_TOKEN`
   - ⚠️ **Must be UPPERCASE with underscores**
   - ❌ Wrong: `okta_api_token`, `OKTA-API-TOKEN`, `OktaApiToken`
   - ✅ Correct: `OKTA_API_TOKEN`
4. **Value:** Paste your API token from Information Sheet (Step 1)
   - Copy the entire token
   - No spaces before or after
5. Click **Add secret**

**✅ Secret added:** You should see `OKTA_API_TOKEN` in the secrets list

---

**Secret 2: OKTA_ORG_NAME**

1. Click **Add secret** (again)
2. **Name:** Type exactly: `OKTA_ORG_NAME`
3. **Value:** Your org name from Information Sheet
   - Example: `dev-12345678`
   - ⚠️ Just the org name, not the full URL!
   - ❌ Wrong: `dev-12345678.okta.com`
   - ✅ Correct: `dev-12345678`
4. Click **Add secret**

---

**Secret 3: OKTA_BASE_URL**

1. Click **Add secret** (again)
2. **Name:** Type exactly: `OKTA_BASE_URL`
3. **Value:** Your base URL from Information Sheet
   - Common values:
     - `okta.com` (production orgs)
     - `oktapreview.com` (preview orgs)
     - `okta-emea.com` (EMEA orgs)
   - ⚠️ No `https://`, no trailing slash
   - ❌ Wrong: `https://okta.com`, `okta.com/`
   - ✅ Correct: `okta.com`
4. Click **Add secret**

---

### ✅ Verification Checklist

Before proceeding to Step 3, verify:

- [ ] You see **exactly 3 secrets** listed:
  - `OKTA_API_TOKEN`
  - `OKTA_ORG_NAME`
  - `OKTA_BASE_URL`
- [ ] All names are UPPERCASE with underscores
- [ ] Your environment name is written down (you'll need it in Step 3)

**❌ Common Issues:**

**Issue: "I added secrets but they're not showing up"**
- Check you're viewing the ENVIRONMENT secrets page (not repository secrets)
- URL should include: `/settings/environments/YourEnvironmentName`

**Issue: "I can't remember my environment name"**
- Go to Settings → Environments
- Your environment name is listed there
- **⚠️ Write it down again!**

**Need more help?** See detailed guide: [SECRETS_SETUP.md](SECRETS_SETUP.md#step-by-step-guide)

---

## Step 3: Run Your First Import (2 minutes)

Now let's import your Okta resources into code!

### 3.1 Navigate to Actions

1. Click **Actions** tab (top menu of your repository)
2. You'll see a list of workflows in the left sidebar

**❌ Can't see Actions tab?**
- Actions may be disabled. Go to Settings → Actions → General → Enable Actions

### 3.2 Run Import Workflow

**⚠️ CRITICAL: Use the EXACT environment name from Step 2**

1. In left sidebar, find and click **"Import All Resources from Okta"**
   - Look for this exact name in the workflow list
2. On the right side, click the **"Run workflow"** dropdown button (gray button)
3. Fill in the form fields:

   **Field 1: Use workflow from**
   - Branch: `main` (default, don't change)

   **Field 2: Environment name**
   - Type the EXACT name from your Information Sheet
   - Example: If you created `MyFirstEnvironment`, type exactly: `MyFirstEnvironment`
   - **⚠️ This is the most common failure point!**
   - ❌ Wrong: `myfirstenvironment`, `MyFirstEnv`, `my-first-environment`
   - ✅ Correct: Match exactly what you created in Step 2

   **Field 3: Update Terraform files?**
   - ✅ Check this box (true)

   **Field 4: Commit changes to repository?**
   - ✅ Check this box (true) - We'll create a PR for review

4. Click green **"Run workflow"** button at the bottom

**✅ Workflow started:** You'll see "Workflow run was successfully requested" message

### 3.3 Watch Progress

1. The page refreshes and a new workflow run appears at the top
   - It may take 5-10 seconds to appear
   - Refresh the page if you don't see it
2. Click on the workflow run to watch real-time progress
3. You'll see steps executing in order:
   - ✅ Set up job
   - ✅ Validate environment
   - ✅ Import entitlement bundles (Step 1)
   - ✅ Import access reviews (Step 2)
   - ✅ Import approval sequences (Step 3)
   - ✅ Import risk rules (Step 4)
   - ✅ Sync resource owners (Step 5)
   - ✅ Sync governance labels (Step 6)
   - ✅ Generate Terraform files (Step 7)
   - ✅ Commit files (Step 8)
   - ✅ Create Pull Request (Step 9)
   - ✅ Summary report (Step 10)

**Expected time:** 2-5 minutes depending on your org size

**✅ Success looks like:**
- All steps show green checkmarks ✅
- Summary shows: "Pull request created: #1"
- No red X marks ❌

### 3.4 Common Failures and Recovery

**❌ Error: "Environment MyFirstEnvironment not found"**

**Cause:** Environment name doesn't match exactly

**Solution:**
1. Go to Settings → Environments
2. Check the EXACT name of your environment (including capitalization)
3. Re-run workflow with correct name

**Common mistakes:**
- Created: `MyFirstEnvironment`, Typed: `myfirstenvironment` ❌
- Created: `demo`, Typed: `Demo` ❌
- Created: `my-first-env`, Typed: `my_first_env` ❌

---

**❌ Error: "Secret OKTA_API_TOKEN not found"**

**Cause:** Secret name is wrong or added to wrong location

**Solution:**
1. Go to Settings → Environments → YourEnvironmentName
2. Check you have these EXACT names (UPPERCASE):
   - `OKTA_API_TOKEN`
   - `OKTA_ORG_NAME`
   - `OKTA_BASE_URL`
3. If secrets are in "Repository secrets" instead, move them to environment
4. Re-run workflow

**See detailed fix:** [SECRETS_SETUP.md - Troubleshooting](SECRETS_SETUP.md#troubleshooting-common-issues)

---

**❌ Error: "401 Unauthorized"**

**Cause:** Invalid Okta API token

**Solution:**
1. Go to Okta Admin Console → Security → API → Tokens
2. Verify your token is still active (not expired)
3. If expired, create a new token
4. Update GitHub Environment secret `OKTA_API_TOKEN` with new token
5. Re-run workflow

---

**❌ Error: "405 Method Not Allowed"**

**Cause:** API endpoint issue (rare, usually already fixed)

**What this means:** Some Okta features may not be available in your org

**Solution:**
- This is usually OK - the import will skip unavailable features
- Check the summary report to see what was imported successfully
- If concerned, create an issue in the repository

---

**⚠️ Warning: "No OIG resources found"**

**This is NORMAL if:**
- You're using a new Okta org
- Identity Governance is not enabled
- You don't have entitlement bundles set up yet

**This is OK!** The workflow still succeeded. You can:
- Continue to Step 4 to see the results
- Enable OIG features in Okta and re-run the import later
- See: [OIG_PREREQUISITES.md](OIG_PREREQUISITES.md) for setup help

---

**✅ Workflow succeeded?** Continue to Step 4!

---

## Step 4: View Your Results (3 minutes)

Your Okta resources are now in code! Let's review the Pull Request that was created.

### 4.1 Open the Pull Request

1. In your repository, click the **Pull requests** tab (top menu)
2. You should see a new PR titled: **"Import all resources from Okta environment: YourEnvironmentName"**
3. Click on the PR to open it

**✅ What you'll see:**
- PR description with summary of imported resources
- List of files that will be created/updated
- Detailed summary report at the bottom

### 4.2 Review the Changes

**The PR shows all files that will be added to your repository:**

#### Terraform Configuration Files
```
environments/yourenvname/terraform/
├── oig_entitlements.tf      # Entitlement bundle definitions
├── oig_reviews.tf            # Access review campaign definitions
└── oig_approval_sequences.tf # Approval workflow definitions
```

**What these do:**
- Define your OIG resources as Infrastructure as Code
- Can be version controlled and reviewed
- Apply changes to Okta using `terraform apply`

#### Configuration Files
```
environments/yourenvname/config/
├── owner_mappings.json       # Resource ownership assignments
├── label_mappings.json       # Governance labels
└── risk_rules.json           # Risk rules (SOD policies)
```

**What these do:**
- Manage API-only resources not yet in Terraform provider
- Applied to Okta using Python scripts
- Tracked in version control

#### Import Files (Raw Data)
```
environments/yourenvname/imports/
├── entitlements.json         # Raw entitlement bundle data from API
├── reviews.json              # Raw access review data from API
└── sequences.json            # Raw approval sequence data from API
```

**What these do:**
- Reference data from Okta API
- Useful for troubleshooting and audit trail
- Not used for applying changes

### 4.3 Understand What You Have

**Terraform Files** (`terraform/*.tf`):
- Infrastructure as Code representation of your Okta resources
- Define resource configurations (names, properties, relationships)
- Can be applied to recreate or update resources
- Version controlled and reviewed via Pull Requests

**Config Files** (`config/*.json`):
- API-managed resources (not yet in Terraform provider)
- Resource owners, governance labels, risk rules
- Applied via Python scripts and GitHub Actions workflows
- Tracked in version control like Terraform files

**Import Files** (`imports/*.json`):
- Raw API responses for reference
- Useful for troubleshooting and comparing with Terraform
- Audit trail of what was imported and when

### 4.4 Merge the Pull Request (Optional)

**For your first quick test, you can merge the PR to save the imported configuration:**

1. Review the files in the PR (click on "Files changed" tab)
2. Verify the imported resources look correct
3. Click **"Merge pull request"** button
4. Click **"Confirm merge"**
5. Optionally, delete the branch after merging

**✅ PR Merged:** Your Okta configuration is now saved in your repository!

**⚠️ Important Notes:**
- Merging the PR doesn't change anything in Okta
- These files represent your CURRENT Okta state
- To apply changes TO Okta, you need Terraform (see "What's Next" section)

**❌ Don't want to merge?**
- That's OK! This was just a test import
- You can close the PR without merging
- Delete the environment and try again later
- The import workflow can be run anytime

---

## 🎉 Success! What You Just Did

1. ✅ Created your own GitOps repository from template
2. ✅ Configured GitHub Environment with Okta credentials
3. ✅ Imported your entire Okta organization into code
4. ✅ Generated Terraform configurations for OIG resources
5. ✅ Created configuration files for governance features

**Your Okta organization is now managed as code!**

---

## What's Next?

### Immediate Next Steps

1. **Review Generated Files**
   - Look at the Terraform code generated
   - Understand what resources you have
   - Check for any TODOs that need attention

2. **Set Up Terraform State Backend**
   - Choose between AWS S3, Terraform Cloud, or local
   - See [Backend Setup Wizard](docs/BACKEND_SETUP_WIZARD.md)
   - Required before applying changes

3. **Initialize Terraform**
   ```bash
   cd environments/myfirstenvironment/terraform
   terraform init
   terraform plan
   ```

### Learning Path

**New to this repo?** Follow this path:

1. **[Getting Started Guide](docs/01-GETTING-STARTED.md)** ← Start here
   - Understanding the environment structure
   - Making your first change
   - GitOps workflow basics

2. **[Architecture Overview](docs/02-ARCHITECTURE.md)**
   - How everything fits together
   - Three-layer resource management model
   - State management

3. **[Workflows Guide](docs/03-WORKFLOWS-GUIDE.md)**
   - Which workflow to use when
   - Workflow decision tree
   - Common operations

4. **[OIG Features](docs/04-OIG-FEATURES.md)**
   - Entitlement bundles
   - Access reviews
   - Governance labels and owners

### Common Next Actions

**Want to make changes?**
→ [Making Your First Change](docs/01-GETTING-STARTED.md#making-your-first-change)

**Want to understand workflows?**
→ [Workflows Guide](docs/03-WORKFLOWS-GUIDE.md)

**Want to apply changes to Okta?**
→ [Terraform Operations](docs/01-GETTING-STARTED.md#applying-changes)

**Want to manage governance features?**
→ [Label Management](docs/LABEL_WORKFLOW_GUIDE.md)

**Having issues?**
→ [Troubleshooting Guide](docs/05-TROUBLESHOOTING.md)

---

## Troubleshooting

**Most common issues are covered in Step 3.4 above. See there first!**

**For detailed troubleshooting, see:** [SECRETS_SETUP.md - Troubleshooting](SECRETS_SETUP.md#troubleshooting-common-issues)

### Quick Troubleshooting Checklist

**If your workflow fails, check these in order:**

#### 1. Environment Name Mismatch (Most Common!)

**Check:**
- [ ] Go to Settings → Environments
- [ ] Verify the EXACT name (including capitalization)
- [ ] Compare with what you typed in the workflow input

**Fix:**
- Re-run workflow with the correct environment name

**Example mistakes:**
- Created: `demo`, Typed: `Demo` ❌
- Created: `MyFirstEnvironment`, Typed: `myfirstenvironment` ❌

---

#### 2. Secrets Configuration Error

**Check:**
- [ ] Go to Settings → Environments → YourEnvironmentName
- [ ] Verify you have **3 secrets** with EXACT names:
  - `OKTA_API_TOKEN` (UPPERCASE with underscores)
  - `OKTA_ORG_NAME` (UPPERCASE with underscores)
  - `OKTA_BASE_URL` (UPPERCASE with underscores)
- [ ] Secrets are in the ENVIRONMENT (not repository secrets)

**Fix:**
- Add missing secrets or correct the names
- See [SECRETS_SETUP.md](SECRETS_SETUP.md) for detailed guide

**Example mistakes:**
- `okta_api_token` instead of `OKTA_API_TOKEN` ❌
- Secrets added to repository instead of environment ❌

---

#### 3. Invalid Okta API Token

**Check:**
- [ ] Token still valid in Okta Admin Console
- [ ] Token has required permissions
- [ ] No typos when pasting token

**Fix:**
1. Go to Okta Admin Console → Security → API → Tokens
2. Create new token
3. Update GitHub Environment secret `OKTA_API_TOKEN`
4. Re-run workflow

---

#### 4. Wrong Okta Organization Details

**Check:**
- [ ] `OKTA_ORG_NAME` is correct (e.g., `dev-12345678`)
- [ ] `OKTA_BASE_URL` matches your org (e.g., `okta.com`)
- [ ] No `https://` or trailing slashes

**Test your credentials:**
```bash
# Test if credentials work
export OKTA_ORG_NAME="your-org-name"
export OKTA_BASE_URL="okta.com"
export OKTA_API_TOKEN="your-token"

curl -X GET \
  "https://${OKTA_ORG_NAME}.${OKTA_BASE_URL}/api/v1/users?limit=1" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"
```

**Expected:** JSON response with user data

**❌ Error responses:**
- `401 Unauthorized` → Token invalid
- `404 Not Found` → Org name or base URL wrong

---

### Additional Issues

**Issue: "No OIG resources found" warning**

**This is NORMAL if:**
- You're using a new Okta org
- Identity Governance is not enabled
- No entitlement bundles created yet

**What to do:**
- This is OK! The import still succeeded
- Enable OIG features: [OIG_PREREQUISITES.md](OIG_PREREQUISITES.md)
- Re-run import after enabling OIG

---

**Issue: Workflow creates empty PR**

**Cause:** No changes detected or nothing to import

**What to do:**
- Review workflow logs to see what was imported
- Check if you have any OIG resources in Okta
- This is normal for empty/new orgs

---

**Issue: GitHub Actions disabled or not working**

**Fix:**
1. Go to Settings → Actions → General
2. Set "Actions permissions" to "Allow all actions"
3. Enable workflows under "Workflow permissions"
4. Re-run the workflow

---

**Issue: Can't create GitHub Environment (Free account)**

**Limitation:** GitHub Free requires public repos for Environments feature

**Workarounds:**
1. **Make repo public temporarily:**
   - Settings → General → Change visibility → Public
   - Create environment and add secrets
   - Run workflow
   - Change back to Private if needed

2. **Use repository secrets instead (less secure):**
   - Settings → Secrets and variables → Actions → Repository secrets
   - Add the same 3 secrets there
   - Workflow will use repository secrets if environment not found
   - ⚠️ Warning: These secrets are accessible to all workflows

3. **Upgrade to GitHub Pro:**
   - Enables private repos with Environments
   - Better security and access control

---

**Still having issues?**

1. **Check workflow logs:**
   - Actions → Click the failed workflow run
   - Click on failed step
   - Read error message carefully

2. **Review detailed troubleshooting:**
   - [SECRETS_SETUP.md - Troubleshooting](SECRETS_SETUP.md#troubleshooting-common-issues)
   - [docs/05-TROUBLESHOOTING.md](docs/05-TROUBLESHOOTING.md)

3. **Get help:**
   - [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions)
   - [Open an Issue](https://github.com/joevanhorn/okta-terraform-demo-template/issues)

---

## Quick Reference

### Re-run Import Workflow

**Via GitHub Web UI:**
1. Go to **Actions** tab
2. Click **"Import All Resources from Okta"**
3. Click **"Run workflow"** dropdown
4. Enter your environment name (EXACT match!)
5. Check boxes for "Update Terraform" and "Commit changes"
6. Click **"Run workflow"**

**Via GitHub CLI:**
```bash
# Replace MyFirstEnvironment with your actual environment name
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyFirstEnvironment \
  -f update_terraform=true \
  -f commit_changes=true

# View the running workflow
gh run watch
```

### Verify Your Environment Configuration

**Check environment exists:**
```bash
# Via GitHub CLI
gh api repos/:owner/:repo/environments

# Or via web UI:
# Settings → Environments → should see your environment listed
```

**Check secrets are configured:**
```bash
# Via GitHub CLI
gh secret list -e MyFirstEnvironment

# Expected output:
# OKTA_API_TOKEN
# OKTA_ORG_NAME
# OKTA_BASE_URL
```

### Import Multiple Environments

To manage multiple Okta orgs:

1. **Create additional GitHub Environments:**
   - Settings → Environments → New environment
   - Name examples: `production`, `staging`, `demo-env`

2. **Add secrets to each environment:**
   - Each environment gets its own set of secrets
   - Same secret names, different values

3. **Run import for each environment:**
   - Run workflow specifying each environment name
   - Each creates a separate PR with environment-specific configs

4. **Result:**
```
environments/
├── MyFirstEnvironment/    # From first import
├── production/             # From second import
└── staging/                # From third import
```

---

## Support & Additional Resources

### 📚 Documentation Paths

**Just getting started?**
- You're here! → [QUICKSTART.md](QUICKSTART.md) ← You are here

**Need secrets help?**
- → [SECRETS_SETUP.md](SECRETS_SETUP.md) - Detailed secrets configuration guide

**Want production setup?**
- → [TEMPLATE_SETUP.md](TEMPLATE_SETUP.md) - Complete setup with AWS backend

**Ready for next steps?**
- → [docs/01-GETTING-STARTED.md](docs/01-GETTING-STARTED.md) - Environment structure and making changes
- → [docs/02-ARCHITECTURE.md](docs/02-ARCHITECTURE.md) - How everything fits together
- → [docs/03-WORKFLOWS-GUIDE.md](docs/03-WORKFLOWS-GUIDE.md) - All available workflows

**Need troubleshooting?**
- → [docs/05-TROUBLESHOOTING.md](docs/05-TROUBLESHOOTING.md) - Comprehensive troubleshooting
- → [SECRETS_SETUP.md#troubleshooting](SECRETS_SETUP.md#troubleshooting-common-issues) - Secrets-specific issues

### 💬 Get Help

**Having issues?**
1. Check [Troubleshooting section above](#troubleshooting)
2. Review [SECRETS_SETUP.md](SECRETS_SETUP.md#troubleshooting-common-issues)
3. Search [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions)
4. Create an [Issue](https://github.com/joevanhorn/okta-terraform-demo-template/issues)

**See it in action:**
- [Working Example Repository](https://github.com/joevanhorn/okta-terraform-complete-demo) - Fully configured demo with real data

---

**Ready to start?** → [Step 1: Pre-Flight Validation](#step-1-pre-flight-validation-2-minutes)
