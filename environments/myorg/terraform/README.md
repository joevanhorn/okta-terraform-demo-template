# Terraform Configuration Directory

This directory contains Terraform configurations for managing your Okta organization.

## 📁 Files in This Directory

### Core Configuration Files

- **`provider.tf`** - Terraform and Okta provider configuration with S3 backend
- **`variables.tf`** - Variable definitions for Okta credentials
- **`.terraform.lock.hcl`** - Provider version lock file (auto-generated)

### Template Files for New Organizations

These template files help you quickly set up a new Okta environment from scratch:

#### 🚀 **QUICKSTART_DEMO.tf.example** - Ready-to-Use Demo Environment

**Best for:** Quick testing, learning, and simple demos

**Contains:**
- 5 demo users (employees, manager, contractor)
- 3 groups (Engineering, Marketing, Admins)
- 1 OAuth application with group assignments
- Helpful outputs for credentials

**Time to deploy:** ~2 minutes

**Usage:**
```bash
# 1. Copy the template
cp QUICKSTART_DEMO.tf.example demo.tf

# 2. Edit demo.tf and uncomment ALL code
# 3. Search and replace @example.com with your email domain
# 4. Deploy
terraform init
terraform apply
```

---

#### 📚 **RESOURCE_EXAMPLES.tf** - Complete Resource Reference

**Best for:** Finding examples of specific resource types, learning all available options

**Contains:**
- ALL Okta Terraform resources with examples
- Organized by category (Users, Groups, Apps, Policies, OIG, etc.)
- Real-world configuration patterns
- Detailed comments explaining each attribute

**Coverage:**
- Identity & Access Management (Users, Groups, Schemas)
- Applications (OAuth, SAML, SWA, Basic Auth)
- Security (Policies, Rules, Networks, Behaviors)
- Okta Identity Governance (OIG) resources
- Authorization Servers & Scopes
- Inline Hooks & Event Hooks

**Usage:**
```bash
# Browse the file to find examples
less RESOURCE_EXAMPLES.tf

# Copy specific examples to your own .tf files
# All examples are commented out - uncomment what you need
```

---

### Generated Files (from Import Workflow)

These files are auto-generated when you run the import workflow:

- **`oig_entitlements.tf`** - Entitlement bundles imported from your Okta org
- **`oig_reviews.tf`** - Access review campaigns imported from your Okta org
- **`oig_approval_sequences.tf`** - Approval workflows imported from your Okta org

⚠️ **Do not manually edit generated files** - they will be overwritten on next import.

---

## 🎯 Quick Start Workflows

### Starting with a Brand New Okta Org

**Scenario:** You have an empty Okta developer org and want to create a demo environment.

**Steps:**
1. Use **QUICKSTART_DEMO.tf.example** to create initial resources
2. Explore **RESOURCE_EXAMPLES.tf** to add more resource types
3. Once satisfied, commit your .tf files and use GitOps workflow

**Commands:**
```bash
# Copy and customize quickstart demo
cp QUICKSTART_DEMO.tf.example demo.tf
vim demo.tf  # Uncomment all code, change @example.com

# Deploy
terraform init
terraform apply

# View outputs
terraform output demo_users
terraform output demo_app
```

---

### Importing an Existing Okta Org

**Scenario:** You have an existing Okta org with resources you want to manage with Terraform.

**Steps:**
1. Run the **Import All Resources** workflow from GitHub Actions
2. Review generated .tf files (oig_entitlements.tf, etc.)
3. Optionally, copy examples from RESOURCE_EXAMPLES.tf to create new resources
4. Use GitOps workflow for all changes

**Commands:**
```bash
# Via GitHub Actions UI
# Actions → Import All Resources from Okta → Run workflow

# Or via GitHub CLI
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyOrg \
  -f update_terraform=true \
  -f commit_changes=true
```

---

### Learning Terraform with Okta

**Scenario:** You want to learn how to use Terraform with Okta.

**Steps:**
1. Browse **RESOURCE_EXAMPLES.tf** to see all available resources
2. Copy examples for resources you want to create
3. Start with simple resources (users, groups) before complex ones (policies, OIG)
4. Use **QUICKSTART_DEMO.tf.example** as a working reference

**Recommended Learning Path:**
1. Users & Groups (QUICKSTART_DEMO.tf.example)
2. Applications (RESOURCE_EXAMPLES.tf → Applications section)
3. Policies & Rules (RESOURCE_EXAMPLES.tf → Security section)
4. OIG Features (RESOURCE_EXAMPLES.tf → OIG section)

---

## 📝 Best Practices

### File Organization

**Recommended structure:**
```
terraform/
├── provider.tf                    # Provider config (required)
├── variables.tf                   # Variables (required)
├── users.tf                       # User definitions
├── groups.tf                      # Group definitions
├── apps_oauth.tf                  # OAuth applications
├── apps_saml.tf                   # SAML applications
├── policies.tf                    # Security policies
├── oig_entitlements.tf           # OIG entitlement bundles
├── oig_reviews.tf                 # OIG access reviews
└── outputs.tf                     # Output values
```

**Why separate files?**
- Easier to navigate and find specific resources
- Better for code reviews (smaller diffs)
- Easier to use terraform -target for specific changes

### Naming Conventions

**Resource names in Terraform:**
```hcl
# Use descriptive, lowercase with underscores
resource "okta_user" "alice_engineer" { ... }      # ✅ Good
resource "okta_user" "user1" { ... }               # ❌ Too generic
resource "okta_user" "AliceEngineer" { ... }       # ❌ Wrong case

# Use consistent prefixes for related resources
resource "okta_group" "eng_developers" { ... }     # ✅ Good
resource "okta_group" "eng_managers" { ... }       # ✅ Good (same prefix)
```

**Resource labels in Okta:**
```hcl
# Use clear, readable names
resource "okta_app_oauth" "demo_app" {
  label = "Demo Application"                       # ✅ Good - user-friendly
  label = "demo-app"                               # ❌ Too technical
}
```

### Template String Escaping

**⚠️ CRITICAL:** Okta uses `${variable}` syntax which conflicts with Terraform.

```hcl
# ❌ WRONG - Terraform will try to interpolate
user_name_template = "${source.login}"

# ✅ CORRECT - Use double $$ to escape
user_name_template = "$${source.login}"
```

**Always use `$$` for Okta template strings!**

### Comments

**Document your intentions:**
```hcl
# ✅ Good comments
# Contractor group - auto-assigned via group rule
resource "okta_group" "contractors" {
  name = "Contractors"
  description = "External contractors with limited access"
}

# ❌ No value
# Create group
resource "okta_group" "contractors" {
  name = "Contractors"
}
```

---

## 🧪 Testing Your Configuration

### Before Applying

```bash
# Format code
terraform fmt

# Validate syntax
terraform validate

# See what will change (safe, read-only)
terraform plan
```

### After Applying

**Verify in Okta Admin Console:**
1. Check created resources exist
2. Test user logins
3. Verify group memberships
4. Test application integrations

**Check Terraform state:**
```bash
# List all resources in state
terraform state list

# Show specific resource details
terraform state show okta_user.alice_engineer
```

---

## 🗑️ Cleaning Up

### Remove Specific Resources

```bash
# Remove a single resource
terraform destroy -target=okta_user.alice_engineer

# Remove multiple related resources
terraform destroy -target=okta_group.engineering \
                  -target=okta_user.alice_engineer
```

### Remove Everything

```bash
# ⚠️ This deletes ALL resources managed by Terraform!
terraform destroy

# You'll be prompted to confirm - type "yes"
```

---

## 📚 Additional Resources

### Documentation

- **Okta Terraform Provider Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs
- **Repository Root README:** ../../README.md
- **GitOps Workflow Guide:** ../../docs/GITOPS_WORKFLOW.md
- **OIG Prerequisites:** ../../OIG_PREREQUISITES.md

### Template Repository Files

- **QUICKSTART_DEMO.tf.example** - This directory (quickstart demo)
- **RESOURCE_EXAMPLES.tf** - This directory (comprehensive reference)
- **DIRECTORY_GUIDE.md** - Root directory (environment structure explained)
- **TEMPLATE_SETUP.md** - Root directory (complete setup guide)

### Getting Help

- **Troubleshooting Guide:** ../../docs/05-TROUBLESHOOTING.md
- **GitHub Discussions:** https://github.com/joevanhorn/okta-terraform-demo-template/discussions
- **Open an Issue:** https://github.com/joevanhorn/okta-terraform-demo-template/issues

---

## 🔧 Troubleshooting

### Common Issues

**Issue: `Error: Invalid provider configuration`**
- **Cause:** Missing or incorrect variables
- **Solution:** Check variables.tf and ensure secrets are set correctly
- **See:** SECRETS_SETUP.md for detailed configuration guide

**Issue: `Error: Invalid template interpolation`**
- **Cause:** Forgot to escape Okta template strings with `$$`
- **Solution:** Replace `${...}` with `$${...}` in Okta template strings
- **Example:** `user_name_template = "$${source.login}"`

**Issue: `Error: Resource already exists`**
- **Cause:** Trying to create a resource that already exists in Okta
- **Solution:** Import the existing resource or remove it from Okta first
- **Command:** `terraform import okta_user.alice_engineer <user-id>`

**Issue: Changes not appearing in Okta**
- **Cause:** Terraform applied successfully but expecting wrong behavior
- **Solution:** Check Terraform state vs Okta Admin Console
- **Remember:** Terraform manages resource DEFINITIONS, not all runtime behavior

---

**Happy Terraforming! 🚀**
