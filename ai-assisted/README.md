# AI-Assisted Terraform Generation

This directory contains tools and templates for using AI assistants (Gemini, ChatGPT, Claude) to generate Terraform code for Okta infrastructure.

**Three approaches available:**
1. **Tier 1: Prompt Engineering** (Manual copy/paste with any AI)
2. **Tier 2: CLI Tool** (Automated with API integration)
3. **Tier 3: Gemini Gem** (Custom AI assistant, easiest for non-technical users)

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Tier 1: Prompt Engineering (Recommended for Beginners)](#tier-1-prompt-engineering)
3. [Tier 2: CLI Tool (Advanced)](#tier-2-cli-tool)
4. [Tier 3: Gemini Gem (Easiest)](#tier-3-gemini-gem)
5. [Directory Structure](#directory-structure)
6. [Available Prompts](#available-prompts)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### For Beginners (Tier 1)

1. **Open your AI assistant** (Gemini, ChatGPT, Claude, etc.)
2. **Copy context files:**
   - `context/repository_structure.md`
   - `context/terraform_examples.md`
   - `context/okta_resource_guide.md`
3. **Choose a prompt template:**
   - `prompts/create_demo_environment.md` (complete demo)
   - `prompts/deploy_infrastructure.md` (AWS Active Directory infrastructure)
   - `prompts/add_users.md` (add users only)
   - `prompts/create_app.md` (create applications)
   - `prompts/oig_setup.md` (OIG features)
4. **Follow the template** and paste into your AI
5. **Copy generated code** to your Terraform files
6. **Validate and apply:**
   ```bash
   terraform fmt
   terraform validate
   terraform plan
   terraform apply
   ```

**Time: ~5-10 minutes**
**Cost: Uses your existing AI subscription**

### For Advanced Users (Tier 2)

1. **Install dependencies:**
   ```bash
   cd ai-assisted
   pip install google-generativeai  # For Gemini
   # Or: pip install openai          # For OpenAI
   # Or: pip install anthropic        # For Claude
   ```

2. **Set API key:**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   # Or: export OPENAI_API_KEY="..."
   # Or: export ANTHROPIC_API_KEY="..."
   ```

3. **Run in interactive mode:**
   ```bash
   python generate.py --interactive --provider gemini
   ```

4. **Or generate from command line:**
   ```bash
   python generate.py \
     --prompt "Create 5 marketing users and a Salesforce app" \
     --provider gemini \
     --output environments/myorg/terraform/demo.tf
   ```

**Time: ~2-3 minutes**
**Cost: Direct API costs (pay-per-use)**

### For Non-Technical Users (Tier 3)

1. **Create your Gemini Gem:**
   - Follow: `GEM_SETUP_GUIDE.md` (15 minute one-time setup)
   - Paste instructions from: `GEM_INSTRUCTIONS.md`
   - Upload context from: `GEM_QUICK_REFERENCE.md`

2. **Use your Gem:**
   - Go to [gemini.google.com/gems](https://gemini.google.com/gems)
   - Open your "Okta Terraform Generator" Gem
   - Type: "Create 5 marketing users and a Salesforce app"
   - Copy generated code to your `.tf` files

3. **Apply:**
   ```bash
   terraform fmt
   terraform validate
   terraform plan
   terraform apply
   ```

**Time: ~1 minute per generation (after setup)**
**Cost: Gemini API costs (~$3-10/month for typical use)**
**Best for:** Solutions Engineers, non-developers, frequent demo creation

---

## Tier 1: Prompt Engineering

### Overview

Use pre-written prompts and context files with any AI assistant. No installation, no API keys, works with the AI service you already use.

### Step-by-Step Guide

#### 1. Choose Your Scenario

| Scenario | Prompt Template | Use Case |
|----------|----------------|----------|
| **Complete Demo Environment** | `prompts/create_demo_environment.md` | Building a full demo from scratch |
| **Deploy Infrastructure** | `prompts/deploy_infrastructure.md` | AWS Active Directory infrastructure |
| **Add Users** | `prompts/add_users.md` | Adding users to existing setup |
| **Create Application** | `prompts/create_app.md` | OAuth/OIDC app configuration |
| **OIG Setup** | `prompts/oig_setup.md` | Identity Governance features |

#### 2. Prepare Context

Open your AI assistant and paste these files:

```
[Paste entire contents of: context/repository_structure.md]

[Paste entire contents of: context/terraform_examples.md]

[Paste entire contents of: context/okta_resource_guide.md]
```

#### 3. Use the Prompt Template

Open your chosen prompt template (e.g., `prompts/create_demo_environment.md`) and fill in your specific requirements.

**Example:**
```
I need to create a complete Okta demo environment using Terraform.

DEMO SCENARIO:
SaaS company with engineering and marketing departments

USERS TO CREATE:
- Jane Smith (jane.smith@example.com, Engineering Manager)
- 3 engineers
- Bob Jones (bob.jones@example.com, Marketing Manager)
- 2 marketing team members

GROUPS TO CREATE:
- Engineering Team
- Marketing Team

APPLICATIONS TO CREATE:
- Salesforce (OAuth web app, Marketing Team access)
- GitHub (OAuth web app, Engineering Team access)

[Follow the rest of the template...]
```

#### 4. Review and Use Generated Code

The AI will generate complete Terraform files. Copy them to your environment:

```bash
# Copy to your terraform directory
cd environments/myorg/terraform

# Paste generated code into files:
# - users.tf
# - groups.tf
# - apps.tf
# etc.

# Validate
terraform fmt
terraform validate
terraform plan
```

### Tier 1 Advantages

✅ **No installation required**
✅ **Works with any AI (Gemini, ChatGPT, Claude, etc.)**
✅ **Use your existing AI subscription**
✅ **No API key management**
✅ **Easy to understand and modify**
✅ **Great for learning**

### Example Sessions

See real examples:
- **Gemini:** `examples/example_session_gemini.md`
- Shows complete workflow from prompt to working code
- Includes follow-up prompts and iterations

---

## Tier 2: CLI Tool

### Overview

Python CLI tool with direct API integration for automated Terraform generation.

### Installation

#### Option 1: Install for Gemini only
```bash
pip install google-generativeai
```

#### Option 2: Install for OpenAI only
```bash
pip install openai
```

#### Option 3: Install for Anthropic/Claude only
```bash
pip install anthropic
```

#### Option 4: Install all providers
```bash
cd ai-assisted
pip install -r requirements.txt
```

### Configuration

Set your API key as an environment variable:

```bash
# For Gemini
export GEMINI_API_KEY="your-gemini-api-key"
# Or
export GOOGLE_API_KEY="your-google-api-key"

# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic/Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"
# Or
export CLAUDE_API_KEY="your-claude-api-key"
```

**Get API Keys:**
- **Gemini:** https://aistudio.google.com/app/apikey
- **OpenAI:** https://platform.openai.com/api-keys
- **Anthropic:** https://console.anthropic.com/

### Usage

#### Interactive Mode (Recommended)

```bash
python generate.py --interactive --provider gemini
```

This starts an interactive session:
```
🤖 AI-Assisted Terraform Generator (Provider: gemini)
============================================================

Loading context files...
✅ Loaded 3 context files

Initializing AI provider...
✅ Using model: gemini-1.5-pro

============================================================
Enter your prompt (or 'quit' to exit):
Example: Create 3 engineering users and an Engineering Team group
============================================================

> Create 5 marketing users with a Salesforce app

🔄 Generating Terraform code...

============================================================
GENERATED TERRAFORM CODE:
============================================================

[Generated code appears here]

============================================================

📊 Token Usage: 1234 input, 567 output, 1801 total

Save to file? (y/N): y
Filename (e.g., users.tf): marketing_demo.tf
✅ Saved to marketing_demo.tf

Run terraform fmt? (y/N): y
✅ Terraform formatting validated

>
```

#### Command Line Mode

```bash
# Basic generation
python generate.py \
  --prompt "Create 3 engineering users" \
  --provider gemini

# Save to file
python generate.py \
  --prompt "Create a Salesforce OAuth app" \
  --provider gemini \
  --output environments/myorg/terraform/salesforce.tf

# Use specific model
python generate.py \
  --prompt "Create OIG entitlement bundles" \
  --provider openai \
  --model gpt-4-turbo-preview \
  --output oig_bundles.tf

# With validation
python generate.py \
  --prompt "Create demo environment" \
  --provider anthropic \
  --validate \
  --output demo.tf
```

### Tier 2 Advantages

✅ **Automated context loading**
✅ **Built-in validation**
✅ **Token usage tracking**
✅ **Interactive mode for iteration**
✅ **Direct file output**
✅ **Multiple provider support**
✅ **Faster iteration**

### CLI Options

```
usage: generate.py [-h] [--provider {gemini,openai,anthropic,claude}]
                   [--model MODEL] [--prompt PROMPT] [--output OUTPUT]
                   [--interactive] [--validate]

AI-Assisted Terraform Generator for Okta

options:
  -h, --help            show this help message and exit
  --provider {gemini,openai,anthropic,claude}
                        AI provider to use (default: gemini)
  --model MODEL         Specific model to use (provider-specific)
  --prompt PROMPT       Prompt describing what to generate
  --output OUTPUT       Output file path (if not specified, prints to stdout)
  --interactive, -i     Run in interactive mode
  --validate            Run terraform fmt validation on generated code
```

---

## Tier 3: Gemini Gem

### Overview

Create a custom Gemini Gem (personalized AI assistant) that permanently remembers all Okta Terraform patterns and rules. This is the **easiest and fastest** method for non-technical users who generate demos frequently.

### What is a Gemini Gem?

**Google Gems** are customized versions of Gemini that you configure once and reuse forever:
- Remember specialized instructions permanently
- Accessible from any device via browser
- Can be shared with team members
- No local software installation required
- No need to paste context files every time

**Think of it as:** Your personal Okta Terraform expert that's always available.

### Why Use a Gem?

**Advantages over Tier 1:**
- ✅ No need to paste context files every time
- ✅ Faster (1 min vs 10 min per generation)
- ✅ More consistent output
- ✅ Shareable with team

**Advantages over Tier 2:**
- ✅ No Python installation required
- ✅ No local setup or dependencies
- ✅ Access from any device (laptop, tablet, phone)
- ✅ Perfect for non-developers

**When to use Gem:**
- You generate Terraform code frequently (weekly or more)
- You want the fastest possible workflow
- You don't want to install Python
- You're a Solutions Engineer focused on demos
- You want to share with non-technical team members

### Setup Guide

**Complete step-by-step guide:** See `GEM_SETUP_GUIDE.md`

**Quick setup (15 minutes one-time):**

1. **Create Gem at [gemini.google.com/gems](https://gemini.google.com/gems)**

2. **Name it:** "Okta Terraform Generator"

3. **Paste instructions:**
   - Copy all content from: `GEM_INSTRUCTIONS.md`
   - Paste into Gem's "Instructions" field

4. **Upload knowledge (optional but recommended):**
   - Upload: `GEM_QUICK_REFERENCE.md`
   - Or upload all context files from `context/` folder

5. **Configure settings:**
   - Temperature: Low (deterministic output)
   - Model: Gemini 1.5 Pro or latest

6. **Test:**
   ```
   Create 3 engineering users and an Engineering Team group
   ```

7. **Done!** Bookmark your Gem for quick access

### Using Your Gem

#### Basic Workflow

1. **Open your Gem:**
   - Go to [gemini.google.com/gems](https://gemini.google.com/gems)
   - Click "Okta Terraform Generator"

2. **Send prompt:**
   ```
   Create 5 marketing users, a Marketing Team group, and a Salesforce OAuth app
   ```

3. **Copy generated code:**
   - Gem outputs complete Terraform HCL
   - Copy to appropriate `.tf` files

4. **Apply:**
   ```bash
   cd environments/mycompany/terraform
   terraform fmt
   terraform validate
   terraform plan
   terraform apply
   ```

#### Example Prompts

**Users:**
```
Create 3 users in the sales department
```

**Groups:**
```
Create an Administrators group with 2 admin users
```

**Applications:**
```
Create a Single Page Application for our React admin dashboard
```

**Complete demos:**
```
Create a complete demo with:
- 10 users across 3 departments
- Department groups
- GitHub app for engineering
- Salesforce for marketing
```

**OIG features:**
```
Create quarterly access review campaigns for 2025
```

### Tier 3 Advantages

✅ **Fastest workflow** - 1 minute per generation
✅ **No installation** - Browser-based, works anywhere
✅ **No context pasting** - Gem remembers everything
✅ **Team sharing** - Share Gem link with colleagues
✅ **Consistent output** - Same quality every time
✅ **Beginner friendly** - No coding or terminal skills needed
✅ **Mobile accessible** - Use from phone/tablet
✅ **Always up-to-date** - Update instructions once, affects all uses

### Cost

**Gemini API Pricing (2025):**
- **Free tier:** 60 requests/minute (sufficient for most SEs)
- **Paid tier:** ~$20/month for Gemini Advanced (optional)

**Typical usage costs:**
- Light use (5 generations/week): **Free tier sufficient**
- Heavy use (50 generations/week): **~$3-10/month**
- Team (5 people): **~$15-50/month total**

**ROI:** Saves 2-3 hours/week compared to manual demo building = **$200-400/week in SE time**

### Sharing with Team

**Option 1: Direct sharing (Google Workspace)**
1. Open Gem settings
2. Click "Share"
3. Add team members by email

**Option 2: Share setup files**
1. Share `GEM_SETUP_GUIDE.md`
2. Share `GEM_INSTRUCTIONS.md`
3. Team members create their own Gems

**Option 3: Team template**
- Create shared doc with team-specific examples
- Link to Gem setup guide
- Include common prompts for your org

### Troubleshooting

**Problem: Gem generates code with wrong template syntax**

Solution: Remind Gem in prompt:
```
Create 3 users. Remember to use $$ for template strings.
```

**Problem: Can't upload knowledge files**

Solution: Paste critical patterns from `GEM_QUICK_REFERENCE.md` into instructions field

**Problem: Gem outputs explanations instead of code**

Solution: Add to prompt:
```
Create 3 users. Output only code, no explanations.
```

**More troubleshooting:** See `GEM_SETUP_GUIDE.md`

### Files for Gem Setup

| File | Purpose | Size |
|------|---------|------|
| `GEM_SETUP_GUIDE.md` | Step-by-step setup instructions | Complete guide |
| `GEM_INSTRUCTIONS.md` | Paste into Gem instructions field | ~400 lines |
| `GEM_QUICK_REFERENCE.md` | Upload as knowledge file | ~250 lines |

### Comparison: Tier 1 vs Tier 2 vs Tier 3

| Feature | Tier 1 | Tier 2 | Tier 3 (Gem) |
|---------|--------|--------|--------------|
| **Setup time** | 0 min | 20 min | 15 min |
| **Per-task time** | 10-15 min | 2 min | **1 min** |
| **Installation** | None | Python + packages | None |
| **API key** | No | Yes | Yes |
| **Context memory** | Manual paste | Automatic | **Permanent** |
| **Best for** | Learning | Automation | **Frequent demos** |
| **Team sharing** | Docs | Scripts | **Gem link** |
| **Mobile access** | ❌ | ❌ | **✅** |
| **Non-technical** | ✅ | ❌ | **✅** |

---

## Directory Structure

```
ai-assisted/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── generate.py                        # CLI tool (Tier 2)
│
├── GEM_SETUP_GUIDE.md                 # Tier 3: Step-by-step Gem setup guide
├── GEM_INSTRUCTIONS.md                # Tier 3: Instructions to paste into Gem
├── GEM_QUICK_REFERENCE.md             # Tier 3: Condensed context for Gem
│
├── prompts/                           # Prompt templates (Tier 1)
│   ├── create_demo_environment.md     # Full demo environment
│   ├── deploy_infrastructure.md       # AWS infrastructure for Active Directory
│   ├── add_users.md                   # Add users to existing setup
│   ├── create_app.md                  # Create OAuth applications
│   └── oig_setup.md                   # OIG features (entitlements, reviews)
│
├── context/                           # Context files for AI
│   ├── repository_structure.md        # How the repo is organized
│   ├── terraform_examples.md          # Example Terraform patterns
│   └── okta_resource_guide.md         # Quick reference for resources
│
├── examples/                          # Real session examples
│   └── example_session_gemini.md      # Complete Gemini session
│
└── providers/                         # AI provider implementations (Tier 2)
    ├── __init__.py                    # Provider registry
    ├── base.py                        # Base provider class
    ├── gemini.py                      # Google Gemini provider
    ├── openai.py                      # OpenAI provider
    └── anthropic.py                   # Anthropic/Claude provider
```

---

## Available Prompts

### 1. Create Demo Environment
**File:** `prompts/create_demo_environment.md`

**Use for:**
- Building complete demo from scratch
- Multi-department setups
- Full RBAC demonstrations
- App integrations

**Generates:**
- users.tf
- groups.tf
- group_memberships.tf
- apps.tf
- app_assignments.tf
- (optional) oig_entitlements.tf

**Time to generate:** 5-10 minutes (Tier 1) or 2-3 minutes (Tier 2)

### 2. Add Users
**File:** `prompts/add_users.md`

**Use for:**
- Adding users to existing environment
- Expanding demos
- Testing scenarios

**Generates:**
- okta_user resources
- Updated group memberships

**Time to generate:** 2-3 minutes (Tier 1) or 1 minute (Tier 2)

### 3. Create Application
**File:** `prompts/create_app.md`

**Use for:**
- OAuth/OIDC applications
- SAML integrations
- Service apps (M2M)
- SPAs, web apps, native apps

**Generates:**
- okta_app_oauth resources
- okta_app_group_assignment resources

**Time to generate:** 2-3 minutes (Tier 1) or 1 minute (Tier 2)

### 4. OIG Setup
**File:** `prompts/oig_setup.md`

**Use for:**
- Entitlement bundles
- Access review campaigns
- Governance demonstrations

**Generates:**
- okta_entitlement_bundle resources
- okta_reviews resources

**Time to generate:** 3-5 minutes (Tier 1) or 1-2 minutes (Tier 2)

**Requirements:** Okta Identity Governance license

### 6. Manage Risk Rules (SOD Policies)
**File:** `prompts/manage_risk_rules.md`

**Use for:**
- Separation of Duties (SOD) policies
- Risk rule configuration
- Conflict detection setup
- Compliance controls

**Generates:**
- risk_rules.json configuration file

**Time to generate:** 3-5 minutes (Tier 1) or 1-2 minutes (Tier 2)

**Requirements:** Okta Identity Governance license

**Note:** Risk rules are managed via Python scripts, not Terraform

### 5. Deploy Infrastructure
**File:** `prompts/deploy_infrastructure.md`

**Use for:**
- AWS infrastructure for Active Directory integration
- Windows Server Domain Controller setup
- Okta AD Agent infrastructure preparation
- VPC and networking for AD

**Generates:**
- provider.tf (AWS provider with S3 backend)
- variables.tf (infrastructure variables)
- vpc.tf (VPC, subnets, routing)
- security-groups.tf (AD ports: DNS, LDAP, Kerberos, RDP, SMB)
- ad-domain-controller.tf (EC2 instance with PowerShell automation)
- outputs.tf (connection info, next steps)
- scripts/userdata.ps1 (automated DC promotion and setup)
- terraform.tfvars.example (configuration template)
- README.md (deployment guide)

**Infrastructure Features:**
- Fully automated Domain Controller promotion
- Automated OU structure creation (IT, HR, Finance, Sales, Marketing, Engineering)
- Automated security group creation (department groups)
- Sample user creation with default passwords
- Okta AD Agent installer pre-downloaded
- Comprehensive logging and troubleshooting

**Deployment Time:**
- Terraform apply: ~3-5 minutes
- Automated setup: ~15-20 minutes
- **Total:** ~20-25 minutes to ready-to-use Domain Controller

**Cost:** ~$35-40/month (t3.medium EC2 + EBS + Elastic IP)

**Time to generate:** 5-10 minutes (Tier 1) or 2-3 minutes (Tier 2)

**Important:** Infrastructure goes in `environments/{env}/infrastructure/`, NOT `terraform/` directory

---

## Best Practices

### 1. Start Simple, Iterate

**Good approach:**
```
First prompt: "Create 2 users in engineering"
Review output
Second prompt: "Add 3 more users and a group"
Review output
Third prompt: "Add Salesforce app for this group"
```

**Avoid:**
```
Single massive prompt: "Create 50 users across 5 departments with
15 applications and complex OIG setup..."
```

### 2. Be Specific

**Good:**
```
"Create user Jane Smith (jane.smith@example.com) in Engineering
department with title Senior Software Engineer"
```

**Less effective:**
```
"Create some users"
```

### 3. Always Validate

After generating code:

```bash
# 1. Format
terraform fmt

# 2. Validate syntax
terraform validate

# 3. Review plan
terraform plan

# 4. Check for issues:
# - Hardcoded secrets?
# - Template strings escaped ($$)?
# - Realistic test data?
# - Status = "ACTIVE"?

# 5. Apply when ready
terraform apply
```

### 4. Use Context Files

Always provide context files to the AI. This ensures:
- Consistent naming patterns
- Proper template escaping ($$ vs $)
- Correct resource structure
- Repository conventions

### 5. Review Security

Before applying, check:
- ✅ No real email addresses (use example.com)
- ✅ No hardcoded API tokens
- ✅ Template strings escaped: `$${source.login}`
- ✅ PKCE enabled for OAuth apps
- ✅ Appropriate grant types
- ✅ Proper client authentication

### 6. Save Your Prompts

If you create a great demo, save the prompt that generated it:

```bash
# Create a prompts/custom/ directory for your team
mkdir -p prompts/custom

# Save your successful prompts
echo "Prompt that created sales demo..." > prompts/custom/sales_demo.md
```

---

## Troubleshooting

### Issue: AI generates code with $ instead of $$

**Symptom:**
```hcl
user_name_template = "${source.login}"  # WRONG
```

**Solution:**
Remind the AI:
```
"Please ensure all Okta template strings use $$ for escaping,
not single $. Example: $${source.login}"
```

### Issue: Generated code fails terraform validate

**Symptom:**
```
Error: Invalid template interpolation
```

**Solution:**
1. Check for unescaped template strings
2. Look for syntax errors
3. Ask AI to fix:
   ```
   "I got this error: [paste error]. Please fix the code."
   ```

### Issue: API key not found (Tier 2)

**Symptom:**
```
❌ Error: No API key found for gemini
```

**Solution:**
```bash
# Set the appropriate environment variable
export GEMINI_API_KEY="your-key-here"

# Verify it's set
echo $GEMINI_API_KEY
```

### Issue: Missing dependencies (Tier 2)

**Symptom:**
```
ImportError: google-generativeai package is required
```

**Solution:**
```bash
pip install google-generativeai
# Or for your specific provider:
pip install openai
pip install anthropic
```

### Issue: Generated code doesn't match repository patterns

**Solution:**
Make sure you pasted all three context files:
1. `context/repository_structure.md`
2. `context/terraform_examples.md`
3. `context/okta_resource_guide.md`

### Issue: OIG resources not working

**Checks:**
1. ✅ Do you have Okta Identity Governance license?
2. ✅ Is OIG enabled in your tenant?
3. ✅ Are you trying to manage principal assignments? (Use Okta UI instead)
4. ✅ Are you trying to set resource owners? (Use Python scripts)

---

## Cost Comparison

### Tier 1: Manual (Free/Existing Subscription)

- **Cost:** $0 (uses existing AI subscription)
- **Time:** ~5-10 minutes per generation
- **Best for:** Occasional use, learning, team sharing one account

### Tier 2: CLI Tool (API Costs)

- **Gemini:** ~$0.001-0.01 per generation (very cheap)
- **OpenAI GPT-4:** ~$0.05-0.20 per generation
- **Claude:** ~$0.03-0.15 per generation
- **Time:** ~1-3 minutes per generation
- **Best for:** Frequent use, automation, multiple users

**Example monthly costs (10 generations/day):**
- Gemini: ~$3-10/month
- OpenAI: ~$15-60/month
- Claude: ~$10-45/month

### Tier 3: Gemini Gem (API Costs)

- **Cost:** Gemini API costs (~$0.001-0.01 per generation)
- **Time:** ~1 minute per generation (fastest!)
- **Setup:** 15 minutes one-time
- **Best for:** Solutions Engineers, frequent demo creation, non-technical users

**Example monthly costs:**
- Light use (5 generations/week): **Free tier** (60 requests/min limit)
- Heavy use (50 generations/week): **~$3-10/month**
- Team (5 people): **~$15-50/month total**

**ROI calculation:**
- Time saved: 2-3 hours/week vs manual demo building
- Value: $200-400/week in SE time saved
- Gem cost: $3-10/month
- **Return:** 20-100x ROI

---

## Examples and Demos

### Example 1: Quick User Addition (Tier 1)

```
[Paste context files]

Add 3 new marketing users:
- Sarah Lee (sarah.lee@example.com, Marketing Coordinator)
- Mike Chen (mike.chen@example.com, Content Manager)
- Emma Davis (emma.davis@example.com, Social Media Specialist)

Add them to the existing Marketing Team group.
```

**Time:** ~2 minutes
**Output:** Ready-to-use Terraform code

### Example 2: Full Demo (Tier 2)

```bash
python generate.py --interactive --provider gemini

> Create a complete SaaS demo with 5 engineering users,
  3 marketing users, GitHub app for engineering,
  Salesforce for marketing, and appropriate groups

[Code generated in ~30 seconds]

Save to file? y
Filename: complete_demo.tf
✅ Saved to complete_demo.tf
```

**Time:** ~1 minute
**Output:** Complete demo ready to apply

---

## Contributing

### Adding New Prompt Templates

1. Create a new file in `prompts/`
2. Follow the structure of existing templates
3. Include:
   - Clear instructions
   - Example usage
   - Expected output
   - Post-generation steps

### Adding New Providers (Tier 2)

1. Create new provider in `providers/your_provider.py`
2. Inherit from `AIProvider` base class
3. Implement required methods
4. Add to `providers/__init__.py`
5. Test thoroughly

---

## Related Documentation

- **📖 Documentation Index:** `../docs/00-INDEX.md` - **Start here! Master index to all 52+ documentation files**
- **Demo Build Guide:** `../testing/DETAILED_DEMO_BUILD_GUIDE.md`
- **Resource Reference:** `../docs/TERRAFORM_RESOURCES.md`
- **Manual Validation:** `../testing/MANUAL_VALIDATION_PLAN.md`
- **Main README:** `../README.md`
- **API Management:** `../docs/API_MANAGEMENT.md` - Risk rules, owners, labels
- **OIG Prerequisites:** `../OIG_PREREQUISITES.md`

---

## Support

**Issues:**
- Check troubleshooting section above
- Review example sessions
- Verify context files are complete
- Test with simpler prompts first

**Questions:**
- Review prompt templates for guidance
- Check example sessions for patterns
- Consult main documentation

---

**Last Updated:** 2025-11-12

**Happy Generating! 🚀**
