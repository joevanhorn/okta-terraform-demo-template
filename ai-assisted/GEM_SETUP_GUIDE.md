# Gemini Gem Setup Guide: Okta Terraform Code Generator

This guide walks you through creating your own personalized Gemini Gem for generating Okta Terraform code. Once set up, you'll have a custom AI assistant that knows all the patterns and rules for this repository.

---

## Table of Contents

1. [What is a Gemini Gem?](#what-is-a-gemini-gem)
2. [Why Use a Gem vs Other Methods?](#why-use-a-gem-vs-other-methods)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Using Your Gem](#using-your-gem)
6. [Example Prompts](#example-prompts)
7. [Troubleshooting](#troubleshooting)
8. [Updating Your Gem](#updating-your-gem)

---

## What is a Gemini Gem?

**Google Gems** are customized versions of Gemini that you create for specific tasks. Think of them as your personal AI experts that:

- Remember specialized instructions permanently
- Have context about your specific use case
- Can be accessed from any device via gemini.google.com
- Can be shared with your team
- Don't require any local software installation

**For this repository:** Your Gem will be an expert Terraform code generator that knows all the Okta patterns, naming conventions, and gotchas.

---

## Why Use a Gem vs Other Methods?

### Comparison of Three Tiers

| Feature | Tier 1: Manual | Tier 2: CLI Tool | Tier 3: Gemini Gem |
|---------|----------------|------------------|--------------------|
| **Setup Time** | 0 min (just copy/paste) | 20 min (Python install) | 15 min (one-time Gem setup) |
| **Per-Task Time** | 10-15 min | 2 min | 1 min |
| **Local Software** | None | Python, pip packages | None |
| **API Key Needed** | No (use free AI) | Yes | Yes |
| **Context Memory** | Manual paste each time | Automatic | Automatic (Gem remembers) |
| **Team Sharing** | Copy docs | Share scripts | Share Gem link |
| **Best For** | Learning, one-offs | Automation, bulk tasks | Quick demos, non-technical users |

**Gem is ideal if you:**
- Generate code frequently (multiple times per week)
- Don't want to install Python locally
- Want to share with Solutions Engineers who aren't developers
- Need access from any device (laptop, tablet, phone)

---

## Prerequisites

1. **Google Account** - Free or paid (Gemini Advanced recommended but not required)
2. **Gemini API Key** - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Free tier: 60 requests/minute
   - Cost: ~$3-10/month for typical SE usage
3. **Basic Okta knowledge** - Understand users, groups, apps
4. **5-10 minutes** for setup

---

## Step-by-Step Setup

### Step 1: Create the Gem

1. **Go to Gemini:**
   - Navigate to [gemini.google.com](https://gemini.google.com)
   - Sign in with your Google account

2. **Open Gem Manager:**
   - Look for "Gem manager" in the top right (may be under profile menu)
   - Or visit: [gemini.google.com/gems](https://gemini.google.com/gems)

3. **Create New Gem:**
   - Click "Create new Gem" or "+ New Gem"
   - You'll see a configuration screen

### Step 2: Configure Basic Settings

1. **Name Your Gem:**
   ```
   Okta Terraform Generator
   ```

2. **Description (optional):**
   ```
   Expert Terraform code generator for Okta Identity and Governance resources.
   Generates production-ready HCL code following GitOps best practices.
   ```

3. **Choose Icon:**
   - Select an icon (e.g., gear, code, or settings icon)

### Step 3: Add Instructions

1. **Copy the instruction file:**
   - Open: `ai-assisted/GEM_INSTRUCTIONS.md`
   - Copy the ENTIRE file contents

2. **Paste into "Instructions" field:**
   - In the Gem configuration, find the "Instructions" text box
   - Paste all content from `GEM_INSTRUCTIONS.md`
   - This tells the Gem how to generate Terraform code

**Note:** The instructions field may have a character limit. If it's too long, use a condensed version (see Troubleshooting section).

### Step 4: Add Knowledge Files (Optional but Recommended)

Google Gems can accept knowledge files to provide additional context.

**Option A: Upload Quick Reference (Recommended)**
1. Find "Add knowledge" or "Upload files" section
2. Upload: `ai-assisted/GEM_QUICK_REFERENCE.md`
3. This gives the Gem condensed examples and patterns

**Option B: Upload Full Context (If space allows)**
If the Gem allows multiple files or larger uploads:
1. Upload: `ai-assisted/context/repository_structure.md`
2. Upload: `ai-assisted/context/terraform_examples.md`
3. Upload: `ai-assisted/context/okta_resource_guide.md`

**Option C: No uploads (Instructions only)**
If you can't upload files, just the instructions are sufficient for most use cases.

### Step 5: Configure Settings

1. **Temperature/Creativity (if available):**
   - Set to **Low** or **Deterministic**
   - We want consistent, predictable code output

2. **Response Length (if available):**
   - Set to **Medium** or **Long**
   - Terraform code can be verbose

3. **Model (if available):**
   - Use **Gemini 1.5 Pro** or **Gemini 2.0** (latest available)

### Step 6: Test Your Gem

1. **Save the Gem**
   - Click "Save" or "Create Gem"

2. **Send a test prompt:**
   ```
   Create 3 engineering users and an Engineering Team group
   ```

3. **Verify output:**
   - Should generate valid Terraform code
   - Should use `status = "ACTIVE"`
   - Should use `$$` for template strings
   - Should include comments

**Expected output:**
```hcl
# Engineering team members
resource "okta_user" "engineer1" {
  email      = "engineer1@example.com"
  first_name = "Alice"
  last_name  = "Engineer"
  login      = "engineer1@example.com"
  department = "Engineering"
  title      = "Software Engineer"
  status     = "ACTIVE"
}
# ... more users and group ...
```

### Step 7: Bookmark Your Gem

1. **Find your Gem in Gem Manager**
2. **Bookmark or pin** for quick access
3. **Share link** with team members (if sharing is enabled)

---

## Using Your Gem

### Basic Usage

1. **Access your Gem:**
   - Go to [gemini.google.com/gems](https://gemini.google.com/gems)
   - Click on "Okta Terraform Generator"

2. **Enter a natural language prompt:**
   ```
   Create 5 marketing users, a Marketing Team group, and a Salesforce OAuth app
   ```

3. **Copy the generated code:**
   - Gem outputs Terraform HCL code
   - Copy and paste into appropriate `.tf` files

4. **Apply the code:**
   ```bash
   cd environments/mycompany/terraform
   # Paste code into users.tf, groups.tf, apps.tf
   terraform fmt
   terraform validate
   terraform plan
   terraform apply
   ```

### Advanced Usage

**Specify environment and file:**
```
Create 3 users for the production environment.
Save to: environments/production/terraform/users.tf
```

**Request specific patterns:**
```
Create a SPA OAuth app for a React dashboard with PKCE enabled
```

**Ask for explanations:**
```
Create a GitHub OAuth app and explain the security settings
```

**Multi-resource requests:**
```
Create a complete demo with:
- 5 users (3 engineering, 2 marketing)
- 2 groups (Engineering, Marketing)
- 1 GitHub app for engineering
- 1 Salesforce app for marketing
```

---

## Example Prompts

### Users

```
Create 3 users in the sales department
```

```
Add a new user: John Doe, john.doe@example.com, Engineering, Senior Engineer
```

### Groups

```
Create an Administrators group and add 2 admin users
```

```
Create a Contractors group for temporary employees
```

### OAuth Applications

```
Create a Single Page Application for our React admin dashboard
```

```
Create a Salesforce OAuth integration for the marketing team
```

```
Create a backend service app for our payment processing API
```

### OIG Features

```
Create an entitlement bundle called "Engineering Tools Access"
```

```
Create a quarterly access review campaign for Q1 2025
```

```
Create 3 department bundles: Marketing, Sales, Engineering
```

### Complete Demos

```
Create a complete demo environment with:
- 10 users across 3 departments
- Department groups
- A GitHub OAuth app
- Access review campaigns
```

---

## Troubleshooting

### Problem: Instructions Too Long for Gem

**Solution:** Use condensed version
1. Create a new file: `GEM_INSTRUCTIONS_CONDENSED.md`
2. Copy only the "Critical Rules" and "Core Directive" sections from `GEM_INSTRUCTIONS.md`
3. Add: "Refer to uploaded knowledge file for detailed patterns"
4. Upload `GEM_QUICK_REFERENCE.md` as knowledge file

### Problem: Gem Generates Invalid Code

**Common issues:**

1. **Template strings using single `$`:**
   - Remind Gem: "Always use double dollar signs: `$$`"
   - Regenerate: "Fix the template strings to use $$"

2. **Missing `status = "ACTIVE"`:**
   - Regenerate: "Add status = ACTIVE to all resources"

3. **Wrong OAuth visibility settings:**
   - Regenerate: "Fix OAuth app to use hide_ios=true and login_mode=DISABLED"

### Problem: Gem Output Includes Explanations

**Solution:** Modify prompt
```
Create 3 users. Output only code, no explanations.
```

Or update Gem instructions to emphasize:
```
Output ONLY Terraform code unless explicitly asked for explanations.
```

### Problem: Can't Upload Knowledge Files

**Solution:** Paste key patterns into instructions
1. Copy critical patterns from `GEM_QUICK_REFERENCE.md`
2. Add to bottom of instructions field
3. Focus on most common patterns (users, groups, apps)

### Problem: Gem Generates Placeholder Values

**Example:** `redirect_uris = ["https://YOUR-DOMAIN.com/callback"]`

**Solution:** Be specific in prompts
```
Create Salesforce app with redirect URI: https://login.salesforce.com/services/oauth2/callback
```

Or regenerate:
```
Replace placeholder values with realistic example.com URLs
```

### Problem: Gem Doesn't Remember Context Across Sessions

**This is expected:** Gems remember instructions, not conversation history.

**Workaround:** Include context in each prompt:
```
For environment: production
Create 3 users in Engineering department
```

---

## Updating Your Gem

As this repository evolves, you may need to update your Gem.

### When to Update

- New Terraform patterns added
- New resource types supported
- Critical rule changes
- Bug fixes in instructions

### How to Update

1. **Go to Gem Manager:**
   - [gemini.google.com/gems](https://gemini.google.com/gems)

2. **Edit your Gem:**
   - Find "Okta Terraform Generator"
   - Click "Edit" or settings icon

3. **Update instructions:**
   - Replace with new `GEM_INSTRUCTIONS.md` content
   - Or add incremental changes

4. **Update knowledge files:**
   - Remove old files
   - Upload new versions

5. **Test changes:**
   - Send test prompts
   - Verify output still valid

---

## Sharing Your Gem with Team

### Option 1: Direct Sharing (Google Workspace)

If using Google Workspace:
1. Open Gem settings
2. Click "Share"
3. Add team members by email
4. They get instant access

### Option 2: Export Instructions

For non-Google Workspace users:
1. Share the `GEM_INSTRUCTIONS.md` file
2. Share the `GEM_QUICK_REFERENCE.md` file
3. Team members create their own Gems using these files

### Option 3: Team Gem Template

Create a shared document with:
- Link to this setup guide
- Your customizations or tips
- Team-specific examples
- Common prompts for your org

---

## GitHub Integration (No Git Required)

This section is for users who want to commit Gem-generated code to GitHub but **don't have git installed locally** and prefer using only a web browser.

### Prerequisites

- GitHub account (free)
- Access to your forked repository on github.com
- Your Gemini Gem already set up

### Workflow Overview

```
Gem generates code → Copy to clipboard →
GitHub web UI → Create/edit file → Commit → Create PR (optional)
```

**Time:** 3-5 minutes per commit (after first time)

---

### Method 1: Direct File Creation (Fastest)

**Best for:** Quick updates, simple changes, learning

#### Step-by-Step

**1. Generate code with your Gem:**

Go to your Gem and enter prompt:
```
Create 3 marketing users for environments/demo/terraform/users.tf
```

Copy the generated Terraform code to clipboard.

**2. Go to your GitHub repository:**
- Open browser to: `https://github.com/YOUR-USERNAME/okta-terraform-demo-template`
- Replace `YOUR-USERNAME` with your GitHub username

**3. Navigate to the file location:**
- Click on `environments/` folder
- Click on your environment folder (e.g., `demo/`)
- Click on `terraform/` folder

**4a. If file exists (editing):**
- Click on the file (e.g., `users.tf`)
- Click the pencil icon (✏️) in top right: "Edit this file"
- Paste your generated code (append or replace as needed)

**4b. If file doesn't exist (creating new):**
- Click "Add file" button (top right)
- Select "Create new file"
- Enter filename: `users.tf`
- Paste your generated code

**5. Commit the file:**

Scroll down to "Commit changes" section:

- **Commit message:**
  ```
  feat: Add marketing users for demo
  ```

- **Extended description (optional):**
  ```
  Generated with Gemini Gem
  - 3 marketing team users
  - Realistic test data
  ```

- **Choose commit option:**
  - ✅ "Commit directly to the `main` branch" (for quick updates)
  - OR "Create a new branch for this commit and start a pull request" (for review)

- Click "Commit changes" button

**6. Verify:**
- GitHub automatically triggers workflows
- Go to "Actions" tab to see terraform-plan running
- Review plan output in workflow logs

---

### Method 2: Create Pull Request (Recommended for Production)

**Best for:** Changes that need review, production environments, team collaboration

#### Step-by-Step

**1-4. Same as Method 1** (generate code, navigate to file, paste)

**5. Create branch and PR:**

When committing:
- Select: ○ "Create a **new branch** for this commit and start a pull request"
- Branch name: Auto-generated (e.g., `joevanhorn-patch-1`) or custom (e.g., `add-marketing-users`)
- Click "Propose changes"

**6. Fill out Pull Request:**

GitHub opens PR creation page:

- **Title:**
  ```
  Add marketing team users to demo environment
  ```

- **Description:**
  ```
  ## Summary
  - Added 3 marketing users for demo purposes
  - Users: sarah.johnson, mike.davis, emily.chen

  ## Generated with
  Gemini Gem using prompt: "Create 3 marketing users"

  ## Testing
  - [ ] Reviewed terraform plan in Actions
  - [ ] Validated user details
  - [ ] Ready to apply
  ```

- Click "Create pull request"

**7. Review automated checks:**
- GitHub Actions runs `terraform-plan.yml`
- Review plan output in PR comments
- Check for validation errors

**8. Merge when ready:**
- Click "Merge pull request"
- Click "Confirm merge"
- Delete branch (optional)

**9. Apply changes (manual):**
- Go to Actions tab
- Click "Run workflow" on `terraform-apply-with-approval.yml`
- Select your environment
- Run workflow
- Approve when prompted

---

### Method 3: GitHub Codespaces (Advanced, Cloud-Based)

**Best for:** Users who want terminal access without local installation

**Note:** Requires GitHub Pro, Team, or Enterprise (free for personal use with limits)

#### Quick Setup

**1. Open Codespace:**
- Go to your repository on github.com
- Click green "Code" button
- Select "Codespaces" tab
- Click "Create codespace on main"

**2. Wait for environment:**
- GitHub launches cloud-based VS Code
- Takes 1-2 minutes first time
- Has terminal, git, and all tools pre-installed

**3. Use Gem and commit:**

In Codespace terminal:
```bash
# Navigate to terraform directory
cd environments/demo/terraform

# Create file (paste Gem-generated code)
cat > users.tf << 'EOF'
[Paste your Gem-generated code here]
EOF

# Commit
git add users.tf
git commit -m "feat: Add marketing users"
git push origin main
```

**Benefits:**
- Full development environment
- Terminal access without local installation
- Git pre-configured
- Can run terraform commands

**Drawbacks:**
- Requires GitHub paid plan (or limited free tier)
- More complex than web UI
- Overkill for simple file creation

---

### Workflow Decision Tree

**Choose the right method:**

```
Do you need review/approval?
├─ Yes → Method 2 (Pull Request)
└─ No
   ├─ Just need to commit one file?
   │  └─ Yes → Method 1 (Direct Commit)
   └─ Need terminal/complex operations?
      └─ Yes → Method 3 (Codespaces)
```

---

### Example: Complete Workflow for Marketing Demo

**Scenario:** Create marketing users and Salesforce app

**Step 1: Generate Users**

Gem prompt:
```
Create 5 marketing users for environments/demo/terraform/users.tf
```

**Step 2: Commit Users**
- GitHub → `environments/demo/terraform/`
- Create new file: `users.tf`
- Paste generated code
- Commit message: `feat: Add marketing users`
- Create branch: `add-marketing-demo`
- Create PR

**Step 3: Generate Salesforce App**

Gem prompt:
```
Create Salesforce OAuth app for Marketing Team in environments/demo/terraform/apps.tf
```

**Step 4: Commit App**
- In same PR branch: `add-marketing-demo`
- GitHub → Navigate to `environments/demo/terraform/`
- Create new file: `apps.tf`
- Paste generated code
- Commit to same branch: `add-marketing-demo`

**Step 5: Generate Group**

Gem prompt:
```
Create Marketing Team group with the 5 marketing users in environments/demo/terraform/groups.tf
```

**Step 6: Commit Group**
- In same PR branch: `add-marketing-demo`
- Create file: `groups.tf`
- Paste generated code
- Commit to branch

**Step 7: Review and Merge**
- Check terraform plan in PR
- Merge PR when ready
- Trigger apply workflow manually

**Result:** Complete marketing demo in one PR, all done through web browser!

---

### Tips for GitHub Web Workflow

**1. Use descriptive commit messages:**
```
# ✅ Good
feat: Add 5 marketing users and Salesforce integration

# ❌ Bad
update files
```

**2. Create PRs for important changes:**
- Production environments
- Complex configurations
- Multi-file changes

**3. Review Actions output:**
- Always check workflow runs
- Read terraform plan carefully
- Look for validation errors

**4. Work in feature branches:**
- Branch name format: `feature/marketing-demo`
- Keeps main branch clean
- Easier to review changes

**5. Leverage PR descriptions:**
- Explain what you generated
- Include Gem prompts used
- Add testing checklist

**6. Commit related changes together:**
- All files for one feature in one branch
- Example: users + groups + apps for marketing team

**7. Use GitHub's file editor features:**
- Syntax highlighting works for .tf files
- Preview tab shows rendered markdown
- Can edit multiple files before committing

---

### Troubleshooting GitHub Web UI

**Problem: Can't find "Add file" button**

Solution: Make sure you're in a folder, not viewing a file. Navigate to the folder level where you want to add the file.

**Problem: Commit button is grayed out**

Solution:
- Make sure you've made changes to the file
- Check that filename is filled in (for new files)
- Ensure commit message is not empty

**Problem: Don't see terraform-plan workflow run**

Solution:
- Go to Actions tab
- Check if workflows are enabled (Settings → Actions)
- Verify `.github/workflows/` folder exists

**Problem: Merge conflicts**

Solution:
- This means someone else changed the same file
- Click "Resolve conflicts" button in PR
- Manually merge the changes in GitHub's editor
- Mark as resolved

**Problem: Want to edit multiple files before committing**

Solution: Use Method 2 (PR with branch):
1. Create branch for first file
2. After first commit, stay in that branch
3. Navigate to other files and edit
4. Commit to same branch
5. All changes appear in same PR

**Problem: Accidentally committed to main instead of branch**

Solution:
- No problem for non-critical changes
- For critical changes, revert: Settings → Branches → View history → Revert
- Best practice: Use PRs for important changes

---

### Security Best Practices

**When using GitHub web UI:**

1. ✅ **Review generated code before committing**
   - Check for placeholder values
   - Verify no hardcoded secrets
   - Ensure realistic test data

2. ✅ **Use example.com for email addresses**
   ```hcl
   # ✅ Good
   email = "user@example.com"

   # ❌ Bad - real email
   email = "john@realcompany.com"
   ```

3. ✅ **Never commit real API tokens**
   - Tokens go in GitHub Secrets, not code
   - Use environment variables in workflows

4. ✅ **Review terraform plan before applying**
   - Always check what will be created
   - Look for unexpected changes
   - Verify resource counts

5. ✅ **Use branch protection for production**
   - Settings → Branches
   - Add rule for `main` branch
   - Require PR reviews

---

## Cost Considerations

### Gemini API Pricing (as of 2025)

**Free Tier:**
- 60 requests per minute
- Sufficient for most individual SE usage

**Paid Tier (Gemini Advanced):**
- Higher rate limits
- Priority access to latest models
- ~$20/month for Google One AI Premium

**Typical Usage Costs:**
- Casual use (5-10 generations/week): **Free tier sufficient**
- Heavy use (50+ generations/week): **~$3-10/month in API costs**
- Team use (5 people): **~$15-50/month total**

**Compare to:**
- Manual time saved: 2-3 hours/week = **$200-400/week** in SE time
- Python automation: Free but requires setup/maintenance

**ROI:** Even with paid tier, Gem pays for itself in first hour of use.

---

## Tips for Best Results

### 1. Be Specific in Prompts

```
# ❌ Vague
Create some users

# ✅ Specific
Create 5 users in the Marketing department with realistic names and titles
```

### 2. Specify File Targets

```
Create 3 users for environments/demo/terraform/users.tf
```

### 3. Request Validation

```
Create a GitHub app and validate OAuth settings
```

### 4. Iterate on Output

```
[After getting code]
Add 2 more users to the Engineering group
```

### 5. Use Context from Previous Output

```
[After creating users]
Now create group memberships for those users in an Engineering Team group
```

---

## Next Steps

1. ✅ **Set up your Gem** (15 minutes)
2. ✅ **Test with simple prompts** (5 minutes)
3. ✅ **Generate your first demo** (10 minutes)
4. ✅ **Share with team** (optional)
5. ✅ **Provide feedback** (file issues in repo)

**Ready to create your Gem?** Follow [Step-by-Step Setup](#step-by-step-setup) above!

---

## Additional Resources

- **Google Gems Documentation:** [blog.google/products/gemini/google-gems-tips/](https://blog.google/products/gemini/google-gems-tips/)
- **Gemini API Pricing:** [ai.google.dev/pricing](https://ai.google.dev/pricing)
- **Repository Documentation:** `../docs/` folder
- **Prompt Templates:** `../prompts/` folder (for manual reference)

---

## Support

**Questions or issues?**
1. Check [Troubleshooting](#troubleshooting) section above
2. Review `ai-assisted/README.md` for Tier 1 and Tier 2 alternatives
3. File an issue in the repository
4. Share learnings with team

**Happy Terraform generating!** 🎉
