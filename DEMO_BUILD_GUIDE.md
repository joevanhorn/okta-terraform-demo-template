# Demo Build Guide for Sales Engineers

**Build impressive Okta demos in minutes, not hours!**

This guide shows you how to use this template to rapidly create demo environments for customer presentations.

---

## 🤔 What is This Approach?

This template uses **Infrastructure as Code (IaC)** - managing Okta through code files instead of clicking in the Admin Console.

**Why use code instead of clicking?**
- ✅ **Speed:** Create 50 users in 2 minutes (not 2 hours of clicking)
- ✅ **Replication:** Copy entire demo to new Okta org instantly
- ✅ **Version Control:** Undo mistakes easily, save different demo versions
- ✅ **Sharing:** Share demo blueprints with team members
- ✅ **Consistency:** Every demo is identical - no missed steps

**How it works:**
1. You write (or AI generates) simple code files describing what you want
2. Tool called "Terraform" reads these files
3. Terraform calls Okta APIs to create the resources
4. Resources appear in your Okta org - just like you created them manually!

**Do I need to be a developer?** No! This guide assumes zero coding experience. If you can follow a recipe, you can do this.

**Optional:** This template also supports **GitOps workflow** (team collaboration through pull requests), but it's not required for building demos. This guide focuses on the quick, direct approach for individual use.

---

## ⚡ Before You Start: Choose Your Path

**Path 1: I want demos FAST and I'm okay learning some command line**
→ Use **AI-Assisted method** (recommended for most SEs)
→ Time: 30-45 min first time, 10 min after
→ You'll learn: Basic terminal commands, terraform basics

**Path 2: I prefer clicking in Okta Admin Console**
→ Build demos manually in Okta (not using this tool)
→ Time: 2-3 hours per demo
→ **Trade-off:** Hard to replicate, no version control, error-prone

**Path 3: I want to learn this deeply for technical sales calls**
→ Start with **Manual Method**, then try AI-Assisted
→ Time: 3-4 hours learning, but you'll understand every detail
→ **Benefit:** Can answer deep technical questions from customers

**This guide covers Paths 1 and 3.** Choose AI-Assisted for speed, Manual for learning.

---

## 💻 What You'll Need

### Software (One-Time Setup)

**Required:**

- [ ] **Terminal/Command Line** access
  - **Mac:** Built-in Terminal app (search "Terminal" in Spotlight)
  - **Windows:** PowerShell or [Windows Terminal](https://apps.microsoft.com/detail/9N0DX20HK701)
  - **Never used terminal?** [5-minute basics](https://www.youtube.com/results?search_query=command+line+basics)

- [ ] **Text Editor** for viewing/editing code files
  - **Recommended:** [VS Code](https://code.visualstudio.com/) (free, beginner-friendly)
  - **Alternatives:** Sublime Text, Atom, or even Notepad++
  - **Mac built-in:** TextEdit (but use plain text mode)

- [ ] **Python 3.9+** (for AI-assisted method only)
  - Check if installed: Open terminal, type `python3 --version`
  - If not installed: [Download Python](https://www.python.org/downloads/)

**Optional but helpful:**

- [ ] **Git** (for saving different demo versions)
  - Check if installed: `git --version`
  - Install: [git-scm.com](https://git-scm.com/downloads)
  - **Can skip for now** - learn later if you want version control

### Okta Access

- [ ] **Okta Admin Console** access with Super Admin role
- [ ] **API Token** created (or know how to create one)
- [ ] **Demo Okta Org** (don't use production!)
  - Ideally: `yourname-demo.oktapreview.com`
  - Not recommended: Using production org for demos

### Prerequisites from QUICKSTART

Before building demos, complete the [QUICKSTART.md](./QUICKSTART.md):
- ✅ Repository created from template
- ✅ GitHub Environment configured
- ✅ Initial import completed
- ✅ Terraform backend set up *(where your demo configs are stored - like a save file)*

**Haven't done QUICKSTART yet?** That's your first step! Takes ~15 minutes.

---

## 🎯 What You'll Learn

This guide covers:

- **Quick Method:** Use AI to generate demo environments in 5-10 minutes *(after initial setup)*
- **Manual Method:** Build custom demos step-by-step to understand how it works
- **Demo Scenarios:** Pre-built patterns for common use cases
- **Live Demo Tips:** Best practices for presenting to customers
- **Troubleshooting:** Fix common issues quickly

**Time Investment:**
- Quick method (first time): **30-45 minutes** *(includes learning curve)*
- Quick method (subsequent): **5-10 minutes**
- Manual method: **30-60 minutes**
- Deep learning: **2-3 hours** *(understand everything)*

---

## Table of Contents

1. [Quick Demo Builder (AI-Assisted)](#quick-demo-builder-ai-assisted)
2. [Manual Demo Building](#manual-demo-building)
3. [Common Demo Scenarios](#common-demo-scenarios)
4. [Demo Presentation Tips](#demo-presentation-tips)
5. [Troubleshooting Demos](#troubleshooting-demos)
6. [Common First-Time Mistakes](#common-first-time-mistakes)

---

## Quick Demo Builder (AI-Assisted)

**Fastest way to create demos!** Use AI to generate Terraform code in minutes.

### Prerequisites Check

Before starting:
- ✅ Python 3.9+ installed (`python3 --version`)
- ✅ AI API key (Gemini, OpenAI, or Anthropic)
- ✅ Completed [QUICKSTART.md](./QUICKSTART.md)
- ✅ Know your environment name from QUICKSTART (e.g., `myfirstenvironment`)

**Don't have an AI API key?**
- **Gemini (Google):** Free tier available at [ai.google.dev](https://ai.google.dev/)
- **OpenAI:** Requires payment at [platform.openai.com](https://platform.openai.com/)
- **Anthropic:** Available at [console.anthropic.com](https://console.anthropic.com/)

### Step 1: Install AI-Assisted Tool

**Open your terminal and run:**

```bash
# Navigate to the ai-assisted directory in your repository
cd ai-assisted

# Install required Python packages
pip install -r requirements.txt
# This downloads the AI helper libraries - takes 1-2 minutes

# Set your API key (choose ONE of these)
export GEMINI_API_KEY="your-key-here"           # If using Google Gemini
export OPENAI_API_KEY="your-key-here"           # If using OpenAI
export ANTHROPIC_API_KEY="your-key-here"        # If using Anthropic
```

**What this does:** Installs the AI tools and configures your API key so the tool can talk to the AI service.

**Time:** 2-3 minutes

### Step 2: Generate Demo Environment

**Example: Marketing team with Salesforce app**

```bash
# IMPORTANT: Replace 'myfirstenvironment' with YOUR environment name from QUICKSTART!
# (The one you created when you first set up the repository)

python generate.py \
  --prompt "Create a marketing team demo with 5 users, 2 groups (Marketing-Team and Marketing-Managers), and a Salesforce app with SSO. Include entitlement bundles for user and admin access." \
  --provider gemini \
  --output ../environments/myfirstenvironment/terraform/marketing-demo.tf \
  --validate
```

**What this does:**
1. Sends your plain-English prompt to AI (Gemini/OpenAI/Anthropic)
2. AI generates complete Terraform code (.tf file)
3. Validates the code syntax automatically
4. Saves the file to your environment's terraform directory

**Output you'll see:**
```
✓ Connecting to Gemini AI...
✓ Generating Terraform code...
✓ Code generated (127 lines)
✓ Syntax validation passed
✓ Saved to: ../environments/myfirstenvironment/terraform/marketing-demo.tf

Summary:
- 5 users
- 2 groups
- 1 application (Salesforce)
- 2 entitlement bundles
```

**Time:** 2-5 minutes

**Customize the prompt:** Change user names, group names, apps, or add more resources by editing the prompt text.

### Step 3: Review Generated Code

**Look at what the AI created:**

```bash
# Navigate to your environment
cd ../environments/myfirstenvironment/terraform

# View the generated code (optional but recommended)
cat marketing-demo.tf
# Or open in VS Code: code marketing-demo.tf
```

**You'll see something like:**
```hcl
resource "okta_user" "marketing_user_1" {
  first_name = "Sarah"
  last_name  = "Johnson"
  login      = "sarah.johnson@company.com"
  email      = "sarah.johnson@company.com"
}
# ... more users, groups, apps, etc.
```

**Don't worry if you don't understand it all!** Terraform will handle the details.

**Time:** 2 minutes (or skip if you trust the AI)

### Step 4: Preview Changes (Safety Check!)

**ALWAYS run this before applying:**

```bash
# Preview what will be created (safe - doesn't change anything!)
terraform plan
```

**What this does:** Shows you exactly what Terraform will create in Okta - like a shopping cart preview before checkout.

**Output you'll see:**
```
Terraform will perform the following actions:

  # okta_user.marketing_user_1 will be created
  + resource "okta_user" "marketing_user_1" {
      + first_name = "Sarah"
      + last_name  = "Johnson"
      + email      = "sarah.johnson@company.com"
      ...
    }

  # okta_group.marketing_team will be created
  + resource "okta_group" "marketing_team" {
      + name = "Marketing-Team"
      ...
    }

Plan: 8 to add, 0 to change, 0 to destroy.
```

**Read this carefully!** Make sure it's creating what you expect.

**Time:** 1 minute

### Step 5: Create Resources in Okta

**Now make it real:**

```bash
# CREATE resources in your Okta org
terraform apply
```

**You'll be prompted:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
```

**Type:** `yes` (exactly, not "y" or "Yes")

**What happens now:**
1. Terraform reads your .tf files
2. Connects to your Okta org using your API token
3. Calls Okta REST APIs to create users, groups, apps, etc.
4. Takes 1-3 minutes depending on number of resources

**Output you'll see:**
```
okta_user.marketing_user_1: Creating...
okta_user.marketing_user_1: Creation complete after 2s [id=00u123...]
okta_group.marketing_team: Creating...
okta_group.marketing_team: Creation complete after 1s [id=00g456...]
...

Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
```

**Time:** 3-5 minutes

**What just happened?** Terraform called Okta's APIs and created all the resources. You can verify by logging into Okta Admin Console → Directory → People → You'll see Sarah Johnson and other users!

### Step 6: Assign Entitlements (Manual Step)

**Why manual?** Terraform creates entitlement bundle **definitions** (like creating an empty access package), but Okta currently requires you to assign them to users through the Admin Console.

**This is a current limitation** of the Terraform Okta provider - future versions may automate this step. For now, think of it like: Terraform builds the bundles, you hand them out.

**How to assign:**

1. **Log into Okta Admin Console**
2. **Navigate:** Identity Governance → Entitlement Bundles
3. **Find your bundles:** Look for "Salesforce User Access" and "Salesforce Admin Access"
4. **Click one:** Click the bundle name
5. **Click "Assign"**
6. **Select users/groups:**
   - For "User Access": Select the "Marketing-Team" group
   - For "Admin Access": Select specific admin users
7. **Click "Save"**
8. **Repeat** for other bundles

**Time:** 2-3 minutes

**Pro tip:** After doing this 2-3 times, it becomes muscle memory!

### ✅ Step 7: Verify Your Demo

**Check everything works:**

1. **Okta Admin Console:**
   - Directory → People: See all 5 users
   - Directory → Groups: See Marketing-Team and Marketing-Managers
   - Applications → Applications: See Salesforce app
   - Identity Governance → Entitlement Bundles: See your bundles with assignments

2. **Test sign-in (optional):**
   - Open incognito browser
   - Go to your Okta org URL
   - Sign in as one of the demo users (you'll need to set/reset password first)
   - Verify they see Salesforce app on dashboard

**Total Time: ~15 minutes first time, ~10 minutes after learning!**

---

## Manual Demo Building

**For custom scenarios or learning how Terraform works.**

**Why do this manually?**
- Understand exactly what's happening
- Customize beyond what AI generates
- Answer detailed customer questions confidently
- Troubleshoot issues more easily

### Understanding Terraform Files

Terraform uses `.tf` files (the `.tf` extension means "Terraform file") with this structure:

```hcl
# This is a resource block - tells Terraform to create something
resource "okta_user" "john_doe" {
  first_name = "John"
  last_name  = "Doe"
  login      = "john.doe@company.com"
  email      = "john.doe@company.com"
}
```

**Breaking it down:**
- `resource` - Keyword meaning "create this thing"
- `"okta_user"` - Type of thing to create (Okta user)
- `"john_doe"` - Internal name you give it (used to reference it)
- `first_name`, `last_name`, etc. - Properties/settings

**Think of it like:** A form you'd fill out in Okta Admin Console, but written as code.

### Step 1: Create Demo File

```bash
# Navigate to your environment
# REPLACE 'myfirstenvironment' with YOUR environment name!
cd environments/myfirstenvironment/terraform

# Create new file for your demo
# Use a text editor - examples:
code sales-team-demo.tf          # VS Code
nano sales-team-demo.tf          # Terminal editor
# Or: Create file in text editor and save to this directory
```

**File naming:** Name it whatever makes sense - `sales-demo.tf`, `my-first-demo.tf`, etc. The `.tf` extension is what matters.

### Step 2: Add Users

**Copy/paste this into your file:**

```hcl
# Sales Representative
resource "okta_user" "alice_sales" {
  first_name = "Alice"
  last_name  = "Johnson"
  login      = "alice.johnson@company.com"
  email      = "alice.johnson@company.com"
}

# Sales Manager
resource "okta_user" "bob_manager" {
  first_name = "Bob"
  last_name  = "Smith"
  login      = "bob.smith@company.com"
  email      = "bob.smith@company.com"
}
```

**Customize:** Change names, emails to match your demo story.

**What this does:** Creates 2 users in Okta when you apply.

### Step 3: Create Groups

**Add this to your file:**

```hcl
resource "okta_group" "sales_team" {
  name        = "Sales Team"
  description = "All sales representatives"
}

resource "okta_group" "sales_managers" {
  name        = "Sales Managers"
  description = "Sales team managers"
}
```

**What this does:** Creates 2 groups that you can assign users and apps to.

### Step 4: Assign Users to Groups

**Add this to your file:**

```hcl
resource "okta_group_memberships" "sales_team_members" {
  group_id = okta_group.sales_team.id
  users = [
    okta_user.alice_sales.id,
    okta_user.bob_manager.id,
  ]
}

resource "okta_group_memberships" "sales_managers_members" {
  group_id = okta_group.sales_managers.id
  users = [
    okta_user.bob_manager.id,
  ]
}
```

**What this does:**
- Adds Alice and Bob to "Sales Team" group
- Adds Bob to "Sales Managers" group
- Notice Bob is in both groups (that's okay!)

**See the references?** `okta_user.alice_sales.id` refers to the Alice user we defined earlier. Terraform links them automatically.

### Step 5: Add Application

**Add this to your file:**

```hcl
resource "okta_app_oauth" "salesforce" {
  label                    = "Salesforce"
  type                     = "web"
  grant_types              = ["authorization_code"]
  redirect_uris            = ["https://login.salesforce.com/services/oauth2/callback"]
  response_types           = ["code"]

  # Make visible to users on their Okta dashboard
  hide_ios = false
  hide_web = false
}

# Assign Sales Team group to the app
resource "okta_app_group_assignment" "salesforce_sales_team" {
  app_id   = okta_app_oauth.salesforce.id
  group_id = okta_group.sales_team.id
}
```

**What this does:**
- Creates a Salesforce application in Okta
- Assigns the "Sales Team" group to it
- All users in Sales Team can now see/access Salesforce

### Step 6: Apply Your Demo

**Now create everything in Okta:**

```bash
# Format code (makes it pretty, optional but nice)
terraform fmt

# Validate syntax (catches typos and errors)
terraform validate
# Should say: "Success! The configuration is valid."

# Preview what will be created (ALWAYS DO THIS!)
terraform plan
# Read the output carefully - does it look right?

# Create everything in Okta!
terraform apply
```

**When prompted, type:** `yes`

**What happens:**
1. Terraform reads your .tf file
2. Figures out the order (users first, then groups, then memberships, then apps)
3. Calls Okta APIs to create each resource
4. Takes 2-3 minutes

**Output you'll see:**
```
okta_user.alice_sales: Creating...
okta_user.alice_sales: Creation complete after 2s
okta_user.bob_manager: Creating...
okta_user.bob_manager: Creation complete after 2s
okta_group.sales_team: Creating...
...

Apply complete! Resources: 5 added, 0 changed, 0 destroyed.
```

**Time:** 20-30 minutes total for custom demo

**Verify:** Log into Okta Admin Console and see your users, groups, and app!

---

## Common Demo Scenarios

Pre-built scenarios for common customer use cases.

### Scenario 1: Basic User Lifecycle

**Customer Use Case:** "Show me how Okta handles user provisioning and app access"

**What to build:**
- 3-5 users (various roles)
- 2-3 groups (department-based)
- 1-2 apps with group assignments
- Demonstrate: Create user → Add to group → Automatically gets app access

**Demo Story:**
"New marketing person joins → Add to Marketing group → Automatically gets HubSpot access"

**Time:** 15 minutes

**AI Prompt:**
```
Create a user lifecycle demo with:
- 5 users: 2 marketing (Sarah M, Mike M), 2 sales (Alice S, Bob S), 1 IT admin (Carol A)
- 3 groups: Marketing, Sales, IT-Admins
- 2 apps: Salesforce (for sales group), HubSpot (for marketing group)
- Assign appropriate groups to each app
```

**What to show customer:**
1. User exists → Not in any groups → No app access
2. Add user to Marketing group
3. Boom! User automatically has HubSpot on their dashboard

### Scenario 2: Entitlement Bundles

**Customer Use Case:** "Show me OIG (Okta Identity Governance) entitlement management"

**What OIG means:** Okta Identity Governance - Okta's features for access requests, approvals, and reviews.

**What to build:**
- Users and groups (from Scenario 1)
- 2-3 entitlement bundles:
  - "Salesforce User Access" (basic access)
  - "Salesforce Admin Access" (elevated privileges)
  - "Marketing Tools Bundle" (HubSpot + others)
- Demonstrate: User requests access → Manager approves → Access granted

**Demo Story:**
"New contractor needs Salesforce → Requests 'User Access' bundle → Manager approves → Gets access automatically"

**Time:** 20 minutes

**AI Prompt:**
```
Create entitlement bundles demo:
- 5 users across sales and marketing
- 2 groups: Sales, Marketing
- Salesforce app with 2 entitlement bundles:
  * "Salesforce User Access" (basic)
  * "Salesforce Admin Access" (admin privileges)
- HubSpot app with 1 entitlement bundle:
  * "Marketing Tools Bundle"
- Make bundles ACTIVE status
```

**Remember:** After terraform apply, assign bundles manually in Okta Admin UI (see Step 6 in Quick Demo Builder).

**What to show customer:**
1. User goes to Okta Access Request portal
2. Searches for "Salesforce"
3. Requests "User Access" bundle
4. Manager gets notification
5. Manager approves
6. User gets access (demo the approval flow in Okta)

### Scenario 3: Access Reviews

**Customer Use Case:** "Show me governance and compliance - quarterly access reviews"

**What to build:**
- Complete Scenario 2 first (users, groups, apps, bundles)
- Add access review campaigns:
  - Quarterly app access review (review ALL app access)
  - Monthly admin access review (review admin entitlements only)
- Demonstrate: Review launches → Manager reviews assignments → Approves/revokes access

**Demo Story:**
"Every quarter, managers review who has access to what. Contractor left? Revoke access immediately."

**Time:** 25 minutes

**AI Prompt:**
```
Create access review demo:
- Build on previous entitlement bundles setup
- Create quarterly access review campaign for all application access
- Create monthly access review campaign for admin entitlements only
- Configure reviewers as group owners (managers)
- Set up schedule: Quarterly on first Monday at 9am
```

**Note:** Access review **schedules and scopes** require manual configuration after terraform import. See the REQUIRED TODO comments in generated files.

**What to show customer:**
1. Campaign launches automatically (quarterly)
2. Manager receives email notification
3. Manager logs in, sees review dashboard
4. Reviews each user's access: Keep or Revoke
5. Submits review
6. System automatically revokes any denied access

### Scenario 4: Full Governance Stack

**Customer Use Case:** "Show me everything - complete OIG feature showcase"

**What to build:**
- Everything from Scenarios 1-3
- Resource owners assigned (who's responsible for each app/group)
- Governance labels applied (categorize resources: "Critical", "Confidential", etc.)
- Catalog entries configured (access request settings)
- Approval workflows (who approves access requests)

**Demo Story:**
"Complete governance: users request access → approval chain → automatic provisioning → regular reviews → audit reports"

**Time:** 45-60 minutes

**Best approach:** Use AI + manual tuning

```bash
# Generate base structure with AI
cd ai-assisted
python generate.py --interactive --provider gemini
# Answer questions interactively: users, groups, apps, etc.

# Fine-tune manually
cd ../environments/myfirstenvironment/terraform
code governance-demo.tf  # Or vim, nano, etc.

# Apply in stages (safer for large demos)
terraform apply -target=okta_user    # Create users first
terraform apply -target=okta_group   # Then groups
terraform apply                       # Everything else
```

**What to show customer:**
1. Complete user lifecycle
2. Access request process with approvals
3. Entitlement bundles and catalogs
4. Access review campaigns
5. Audit reports and compliance dashboards
6. (Optional) Automated provisioning to downstream apps

---

## Demo Presentation Tips

### Before the Demo

**Preparation Checklist (10 minutes before customer call):**

1. **Verify demo is working:**
   ```bash
   cd environments/myfirstenvironment/terraform
   terraform plan
   # Should show "No changes" - means your demo is stable
   ```

2. **Open all tabs:**
   - Okta Admin Console (logged in, on People page)
   - Okta End User Dashboard (logged in as demo user)
   - Terminal (in terraform directory, showing last `terraform plan` output)
   - (Optional) GitHub repository if showing collaboration features

3. **Have backup ready:**
   - Screenshots of expected results (in case live demo breaks)
   - Pre-built demo environment (if first one fails)
   - Written talking points

4. **Test your demo flow once:**
   - Walk through the story yourself
   - Make sure users exist, apps work, etc.
   - Reset any state (e.g., pending access requests)

### During the Demo

**DO:**
- ✅ **Start with "why"** - Business problem first, solution second
  - "Manual provisioning takes 3 days and errors happen..."
  - "With automation, it's instant and consistent"

- ✅ **Show outcomes, not syntax**
  - Focus on: "50 users created in 2 minutes"
  - Not: "See this resource block syntax..."

- ✅ **Use `terraform plan` to show "what if"**
  - Safe preview before making changes
  - Shows diff of what will change

- ✅ **Highlight ease of replication**
  - "We can deploy this exact demo to your org in 10 minutes"

- ✅ **Keep it simple**
  - Don't show every Terraform feature
  - Focus on business value

**DON'T:**
- ❌ **Debug live** - If something breaks, switch to backup screenshots
- ❌ **Get lost in technical details** - Customer cares about outcomes
- ❌ **Assume audience knows Terraform** - Explain as you go
- ❌ **Run destructive commands** without confirming
  - Never `terraform destroy` during demo (unless showing cleanup)
- ❌ **Show sensitive information**
  - API tokens, passwords, internal org names

### Demo Flow Templates

**5-Minute Version (Perfect for discovery calls):**

1. **Problem** (1 min)
   - "Manual user provisioning takes hours..."
   - "Errors happen, access is inconsistent"
   - "Hard to track who has access to what"

2. **Solution** (1 min)
   - "With Infrastructure as Code, we automate everything"
   - "Create users, groups, apps instantly"
   - "Everything documented in code - audit ready"

3. **Demo** (2 min)
   - Show simple terraform apply creating 5 users
   - Show users appearing in Okta Admin Console
   - Show users' dashboard with apps

4. **Verify** (1 min)
   - Log into Okta as one of the new users
   - Show they have appropriate app access
   - Quick!

**15-Minute Version (Perfect for technical deep-dive):**

1. **Problem + Context** (2 min)
   - Business problem
   - Current manual process pain points
   - Compliance/audit requirements

2. **Architecture Overview** (3 min)
   - Show diagram (if you have one)
   - Explain: Code → Terraform → Okta APIs
   - Benefits: Version control, automation, consistency

3. **Demo - Create** (3 min)
   - Show terraform plan (preview)
   - Run terraform apply
   - Create users, groups, apps
   - Verify in Okta console

4. **Demo - Change** (3 min)
   - Modify the code (add a user)
   - Show terraform plan (only shows diff)
   - Apply the change
   - Show it's non-destructive

5. **Demo - Governance** (2 min) - *OPTIONAL, advanced*
   - Show access request flow
   - Or show access review
   - Or show rollback capability
   - **Skip this unless customer specifically interested in GitOps team collaboration**

6. **Cleanup** (2 min)
   - Show terraform destroy (optional)
   - Discuss: How to get started
   - Next steps

**Note about GitOps:** If customer asks "How does your team collaborate on this?", THEN show:
- Pull request workflow
- Code review process
- Automated validation
- Otherwise, skip - it's advanced and not needed for demos

### Handling Questions

**Common Questions & Talking Points:**

**Q: "Is this only for Okta?"**
A: No! Terraform works with 3,000+ providers - AWS, Azure, databases, SaaS apps. Companies use it to manage their entire infrastructure. We're just showing the Okta piece.

**Q: "What if I make a mistake?"**
A: Two safety nets:
1. `terraform plan` shows changes BEFORE making them (preview mode)
2. Everything is in version control (git) - you can rollback to any previous state
3. Bonus: Terraform tracks state, so it knows how to undo changes

**Q: "Can non-technical people use this?"**
A: Absolutely! Two approaches:
1. **Direct use:** With AI generation, you just describe what you want in plain English
2. **GitOps workflow:** Business users create "access requests" (pull requests), technical team approves and applies

**Q: "How do we learn this?"**
A:
1. This template is ready to fork and use immediately
2. Comprehensive documentation included
3. AI can generate code from plain English descriptions
4. Training available (hashicorp.com/training)

**Q: "What about state files and backends?"**
A: Great question! (Shows they're technical)
- State files track what's been created (like a database)
- Stored securely in S3 or Terraform Cloud
- Encrypted, versioned (can rollback), locked (prevents conflicts)
- Think of it like: "Git for infrastructure"

**Q: "How long does setup take?"**
A:
- Initial setup: 2-3 hours (one time)
- Building a demo: 10-30 minutes
- Deploying to new org: 5 minutes (after setup)

**Q: "Do you have examples for [our industry]?"**
A:
- We have templates for common scenarios (show ai-assisted/prompts/)
- Can customize for financial services, healthcare, retail, etc.
- Happy to build a proof-of-concept with your use cases

---

## Troubleshooting Demos

### Demo Won't Apply

**Issue:** `terraform apply` fails with errors

**Common Causes & Solutions:**

**1. Authentication problem:**
```bash
# Check if environment variables are set
echo $TF_VAR_okta_api_token
echo $TF_VAR_okta_org_name

# If empty, you need to set them
# Check QUICKSTART.md for setup instructions
```

**2. Syntax error in .tf file:**
```bash
# Validate your code
terraform fmt     # Auto-formats code
terraform validate  # Checks for errors

# Look for error message, fix the issue
# Common: Missing quotes, brackets, commas
```

**3. Resource already exists:**
```
Error: User with login alice@example.com already exists
```
**Fix:** Either delete the existing user in Okta, or change the email in your .tf file

**4. API token expired or lacks permissions:**
```
Error: 401 Unauthorized
```
**Fix:** Generate new API token in Okta Admin Console with correct permissions

### Demo Shows Wrong Org

**Issue:** Resources created in wrong Okta organization (e.g., production instead of demo!)

**Cause:** Using wrong environment secrets or wrong configuration

**How to check:**
```bash
# Verify which org you're targeting
echo $TF_VAR_okta_org_name
# Should show your DEMO org, not production!

# Check terraform backend configuration
cd environments/myfirstenvironment/terraform
cat provider.tf | grep backend
```

**Fix:**
1. Double-check GitHub Environment secrets
2. Verify you're using correct environment name
3. See [SECURITY.md](./SECURITY.md) for environment vs repository secrets

**Prevention:**
- Always use dedicated demo Okta org (yourname-demo.okta.com)
- Never point demos at production
- Set up separate GitHub Environments for each Okta org

### Can't Find Created Resources

**Issue:** Terraform says "Apply complete!" but you don't see resources in Okta

**Solutions:**

**1. Check correct org:**
- Verify you're logged into the right Okta org
- URL should match your `OKTA_ORG_NAME` variable
- Easy to have multiple tabs open to different orgs!

**2. Refresh the page:**
- Sometimes Okta Admin Console needs a refresh
- Wait 5-10 seconds, then refresh browser

**3. Check terraform state:**
```bash
# See what Terraform thinks it created
terraform state list

# Get details about specific resource
terraform state show okta_user.alice_sales

# If shown here, it WAS created - check Okta again
```

**4. Check Okta System Log:**
- Security → Reports → System Log
- Filter by your API token
- See if creation events are logged

### Demo is Slow

**Issue:** `terraform apply` takes 5+ minutes

**This is normal if:**
- Creating 50+ users
- Creating many groups with memberships
- First run in new environment

**Solutions to speed up:**

**1. Use targeted applies:**
```bash
# Apply users first (parallel creation)
terraform apply -target=okta_user

# Then groups
terraform apply -target=okta_group

# Then everything else
terraform apply
```

**2. Reduce scope:**
- Create 5 users instead of 50 for demo purposes
- Focus on key features, not quantity
- Can always show "this scales to thousands"

**3. Pre-build demos:**
- Build demo environment ahead of time
- During customer call, just show existing environment
- Make small changes to demonstrate capabilities

**Typical timings:**
- 5-10 resources: 1-2 minutes
- 20-50 resources: 3-5 minutes
- 100+ resources: 5-10 minutes

---

## Common First-Time Mistakes

Learn from others' mistakes! These are the top issues new users hit:

### Mistake 1: Running `terraform apply` Before `terraform plan`

**Problem:** You don't know what's about to change - surprises happen!

**Symptom:** "Wait, it deleted my test user! I didn't mean to do that!"

**Fix:** ALWAYS run `terraform plan` first
```bash
# Right order:
terraform plan    # Preview - safe, no changes
# Read output carefully
terraform apply   # Only if plan looks good
```

**Why it happens:** In a hurry, muscle memory from other tools

### Mistake 2: Using Wrong Okta Org

**Problem:** Created 50 demo users in PRODUCTION org instead of demo org

**Symptom:** Production org suddenly has test users, apps, groups

**Fix:** Double-check org before EVERY apply:
```bash
# Check which org you're targeting
echo $TF_VAR_okta_org_name
# Better see "demo" not "production"!

# Also check URL when verifying
# https://yourname-demo.okta.com ✅
# https://yourcompany.okta.com ❌
```

**Prevention:**
- Use dedicated demo org
- Name it obviously: `yourname-demo.okta.com`
- Never save production credentials locally

### Mistake 3: Forgetting to Assign Entitlement Bundles

**Problem:** Created bundles with Terraform but users can't access anything

**Symptom:** "I created entitlement bundles but they're empty - no users assigned!"

**Fix:** Remember this is a TWO-STEP process:
1. Terraform creates bundle DEFINITIONS
2. YOU assign bundles to users manually in Okta Admin Console

**Steps:**
1. Run `terraform apply` (creates bundles)
2. Log into Okta Admin Console
3. Identity Governance → Entitlement Bundles
4. Click bundle → Assign → Select users/groups → Save

**Why:** Current limitation of Terraform Okta provider - can't manage assignments yet

### Mistake 4: Not Cleaning Up After Demo

**Problem:** Demo resources accumulate, org gets cluttered, confusion in future demos

**Symptom:** "Which users are from which demo? Is this old data?"

**Fix:** Always destroy demo resources after use:
```bash
cd environments/myfirstenvironment/terraform

# See what will be deleted
terraform plan -destroy

# Delete everything
terraform destroy
# Type: yes

# Takes 2-5 minutes
```

**When to clean up:**
- After customer demo (if no follow-up needed)
- Before building new demo
- Weekly cleanup of old demos

**Exception:** Keep a "baseline" demo environment for quick showings

### Mistake 5: Editing Files in Wrong Directory

**Problem:** Made changes to template files instead of your environment files

**Symptom:** Changes don't appear when you apply, or affect wrong environment

**Fix:** Always work in YOUR environment directory:
```bash
# ❌ Wrong:
cd environments/production/terraform    # Template example
cd environments/staging/terraform       # Template example

# ✅ Right:
cd environments/myfirstenvironment/terraform  # YOUR environment
cd environments/yourname-demo/terraform       # Or whatever you named it
```

**Tip:** Double-check with `pwd` (print working directory) before editing files

### Mistake 6: Committing Secrets to Git

**Problem:** Accidentally committed API token or credentials to git repository

**Symptom:** GitHub security alerts, or worse, someone uses your credentials

**Fix:**
1. **Immediately revoke** the exposed token in Okta
2. Generate new token
3. Update GitHub Environment secrets
4. Remove from git history (see [SECURITY.md](./SECURITY.md))

**Prevention:**
- Never store secrets in .tf files
- Use environment variables: `$TF_VAR_okta_api_token`
- Check .gitignore includes `.env`, `*.tfvars`
- GitHub Environments keep secrets separate

### Mistake 7: Using Wrong AI Provider

**Problem:** Set OPENAI_API_KEY but ran with `--provider gemini`

**Symptom:**
```
Error: GEMINI_API_KEY not found
```

**Fix:** Match your API key to provider:
```bash
# If you have Google Gemini key:
export GEMINI_API_KEY="your-key"
python generate.py --provider gemini ...

# If you have OpenAI key:
export OPENAI_API_KEY="your-key"
python generate.py --provider openai ...

# If you have Anthropic key:
export ANTHROPIC_API_KEY="your-key"
python generate.py --provider anthropic ...
```

### Mistake 8: Expecting Instant Results

**Problem:** Ran `terraform apply`, immediately checked Okta, resources not there yet

**Symptom:** "It says complete but I don't see anything!"

**Reality:**
- Small demos (5-10 resources): Ready in 30 seconds
- Medium demos (20-50 resources): Takes 2-3 minutes
- Large demos (100+ resources): Takes 5-10 minutes

**Fix:**
- Wait for `Apply complete!` message
- Give Okta 10-30 seconds to process
- Refresh browser
- Check terraform state: `terraform state list`

---

## Cleaning Up Demos

### Destroy Everything

**When demo is done, clean up:**

```bash
cd environments/myfirstenvironment/terraform

# Preview what will be DELETED (safety check)
terraform plan -destroy
# Read carefully - is this the right demo?

# Delete all resources from Okta
terraform destroy
```

**You'll be prompted:**
```
Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value:
```

**Type:** `yes` (exactly)

**What happens:**
1. Terraform deletes app assignments
2. Then apps
3. Then group memberships
4. Then groups
5. Finally users

**Time:** 2-5 minutes

**Verify:** Check Okta Admin Console - resources should be gone

### Selective Cleanup

**Delete only specific resources:**

```bash
# Delete one specific user
terraform destroy -target=okta_user.demo_user1

# Delete all users (keeps groups and apps)
terraform destroy -target=okta_user

# Delete all groups
terraform destroy -target=okta_group
```

**Use case:** Update demo by removing some resources while keeping others

### Reset Demo to Previous Version

**If you saved versions with git:**

```bash
# See available versions
git tag
# Shows: demo-v1, demo-v2, demo-v3

# Restore specific version
git checkout demo-v1
terraform apply

# Or destroy and rebuild
terraform destroy
git checkout demo-v2
terraform apply
```

**If you didn't use git:** Just rebuild from scratch (fast with AI method!)

---

## Quick Reference

### Demo Building Checklist

**Before customer demo:**
- [ ] Demo environment tested (run `terraform plan` - shows "No changes")
- [ ] Resources visible in Okta Admin Console
- [ ] Test user can log in successfully
- [ ] Apps appear on test user's dashboard
- [ ] Entitlement bundles assigned (if using)
- [ ] Backup screenshots ready (in case demo breaks)
- [ ] Browser tabs open: Okta Admin, Okta User Dashboard, Terminal
- [ ] Talking points prepared
- [ ] Know how to recover if something goes wrong

### Command Cheat Sheet

```bash
# Navigate to your environment
cd environments/YOUR-ENV-NAME/terraform

# Preview changes (SAFE - doesn't change anything)
terraform plan

# Create/update resources (asks for confirmation)
terraform apply

# Delete all resources (asks for confirmation)
terraform destroy

# Format code (makes it pretty)
terraform fmt

# Check for syntax errors
terraform validate

# See what Terraform manages
terraform state list

# See details of specific resource
terraform state show okta_user.alice_sales

# Generate demo with AI
cd ai-assisted
python generate.py --interactive --provider gemini
```

### Time Estimates (Realistic)

| Task | First Time | After Learning |
|------|-----------|----------------|
| Initial setup (QUICKSTART) | 30-45 min | N/A |
| AI-assisted demo | 30-45 min | 10-15 min |
| Manual demo | 60-90 min | 30 min |
| Entitlement assignment | 5 min | 2-3 min |
| Verify demo works | 10 min | 5 min |
| Customer demo presentation | 5-15 min | 5-15 min |
| Cleanup | 5 min | 2-3 min |

---

## Next Steps

### After Building Your First Demo

**1. Learn more about the workflow** (optional, for team collaboration):
→ [01-GETTING-STARTED.md](./docs/01-GETTING-STARTED.md#making-your-first-change)
- Only needed if collaborating with team
- Explains pull requests and GitOps workflow
- Can skip if working solo

**2. Understand the architecture** (optional, for technical curiosity):
→ [02-ARCHITECTURE.md](./docs/02-ARCHITECTURE.md)
- Deep dive into how it works
- For answering technical customer questions
- Not required for building demos

**3. Explore OIG features** (important if demoing governance):
→ [04-OIG-FEATURES.md](./docs/04-OIG-FEATURES.md)
- Okta Identity Governance features
- Entitlement bundles, access reviews, catalogs
- Read if doing Scenario 2, 3, or 4

**4. Master workflows** (reference guide):
→ [03-WORKFLOWS-GUIDE.md](./docs/03-WORKFLOWS-GUIDE.md)
- Complete workflow reference
- GitHub Actions automation
- For advanced usage

**5. Build advanced demos** (when ready):
→ [ai-assisted/README.md](./ai-assisted/README.md)
- Advanced AI generation techniques
- Custom prompts
- Complex scenarios

---

## Resources

### Example Demos

- **[Working Repository](https://github.com/joevanhorn/okta-terraform-complete-demo)** - See real demos in action
  - Browse the code
  - See what actual demos look like
  - Copy patterns you like

### Documentation

**Getting Started:**
- [QUICKSTART.md](./QUICKSTART.md) - Initial setup (do this first!)
- [docs/01-GETTING-STARTED.md](./docs/01-GETTING-STARTED.md) - Making changes
- [SECURITY.md](./SECURITY.md) - Security best practices

**Reference:**
- [docs/03-WORKFLOWS-GUIDE.md](./docs/03-WORKFLOWS-GUIDE.md) - Workflow reference
- [docs/ROLLBACK_GUIDE.md](./docs/ROLLBACK_GUIDE.md) - Recovery procedures
- [docs/05-TROUBLESHOOTING.md](./docs/05-TROUBLESHOOTING.md) - Common issues

### Learning Resources

**Terraform:**
- [Terraform Okta Provider Docs](https://registry.terraform.io/providers/okta/okta/latest/docs) - Official reference
- [Terraform Learn](https://learn.hashicorp.com/terraform) - Interactive tutorials
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)

**Okta:**
- [Okta Developer Docs](https://developer.okta.com/) - API documentation
- [Okta Admin Guide](https://help.okta.com/) - Feature documentation
- [Okta Identity Governance](https://help.okta.com/okta_help.htm?type=oie&id=ext-oig-main) - OIG features

**Command Line Basics:**
- [Command Line Crash Course](https://www.youtube.com/results?search_query=command+line+basics) - Video tutorials
- [Terminal Cheat Sheet](https://gist.github.com/poopsplat/7195274) - Quick reference

### Community

**Need Help?**
- [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions) - Ask questions
- [GitHub Issues](https://github.com/joevanhorn/okta-terraform-demo-template/issues) - Report bugs
- [Stack Overflow](https://stackoverflow.com/questions/tagged/terraform+okta) - Technical questions

**Want to Contribute?**
- Share your demo scenarios
- Improve documentation
- Report issues
- Submit prompt templates

---

## Summary

### Three Ways to Build Demos

**1. AI-Assisted (Fastest) - RECOMMENDED:**
- **Time:** 30-45 min first time, 10-15 min after
- **Best for:** Common scenarios, quick demos, minimal Terraform knowledge
- **How:** Describe what you want in plain English, AI generates code
- **Tradeoff:** Less control, might need tweaking

**2. Manual (Educational):**
- **Time:** 60-90 min first time, 30 min after
- **Best for:** Learning, custom scenarios, understanding how it works
- **How:** Write Terraform code yourself
- **Tradeoff:** Takes longer, but you learn deeply

**3. Hybrid (Balanced):**
- **Time:** 20-30 min
- **Best for:** Experienced users, custom demos with speed
- **How:** AI generates base, you customize
- **Tradeoff:** Requires some Terraform knowledge

### Choose Based On

| Factor | AI-Assisted | Manual | Hybrid |
|--------|-------------|--------|--------|
| **Speed** | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| **Learning** | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Customization** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Repeatability** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

### Quick Wins for First-Time Users

**Week 1:** Use AI-Assisted to build first demo (Scenario 1)
**Week 2:** Try Manual method to understand how it works
**Week 3:** Use Hybrid for customer-specific demo
**Ongoing:** AI-Assisted for speed, Manual for learning

### Remember

- ✅ Always run `terraform plan` before `apply`
- ✅ Use dedicated demo Okta org (never production!)
- ✅ Entitlement assignment is manual (not a bug!)
- ✅ Clean up after demos (`terraform destroy`)
- ✅ Have backup screenshots for live demos
- ✅ Focus on outcomes, not syntax
- ✅ Start simple, add complexity as you learn

### Ready to Start?

**First time?** → Start with [Quick Demo Builder (AI-Assisted)](#quick-demo-builder-ai-assisted)

**Want to learn?** → Start with [Manual Demo Building](#manual-demo-building)

**Need help?** → Check [Troubleshooting](#troubleshooting-demos) and [Common Mistakes](#common-first-time-mistakes)

**Questions?** → [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions)

---

**Good luck with your demos! 🚀**
