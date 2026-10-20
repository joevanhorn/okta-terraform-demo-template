# Okta Terraformer Integration Guide

Complete guide for importing existing Okta configurations using Terraformer (reverse Terraform).

## 🚨 Important Limitations

### OIG Resources Not Supported

**Terraformer does NOT support the OIG resources** introduced in Terraform Provider v6.x. These must be managed separately:

❌ **Not Imported by Terraformer:**
- `okta_campaign` - Access certification campaigns
- `okta_entitlement` / `okta_entitlement_bundle` - Entitlements and bundles
- `okta_request_condition` - Request conditions
- `okta_request_sequence` - Approval sequence bindings
- `okta_request_setting_organization` / `okta_request_setting_resource` - Request settings
- `okta_request_v2` - Access requests
- `okta_resource_owner` - Resource owners (provider v6.13.0+)
- `okta_label` - Label definitions (provider v6.13.0+)
- Data sources such as `okta_catalog_entry_default`, `okta_catalog_entry_user_access_request_fields`, `okta_principal_entitlements` are read-only and never imported
- Label-to-resource assignment and risk rules (API only, no Terraform resource)

✅ **Fully Supported by Terraformer:**
- All standard Okta resources (users, groups, apps, policies, etc.)

**Recommendation:** Use Terraformer for base resources, create OIG configurations using the provided Terraform files. See [OIG Manual Import Guide](./OIG_MANUAL_IMPORT.md) if you have existing OIG configurations that must be imported.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Workflow](#detailed-workflow)
- [Resource Types](#resource-types)
- [Cleanup & Refactoring](#cleanup--refactoring)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Integration with OIG Demo](#integration-with-oig-demo)

## 🎯 Overview

**Terraformer** is a CLI tool that generates Terraform files from existing infrastructure (reverse Terraform). This is incredibly useful for:

- **Migrating to Terraform** - Import existing Okta configurations
- **Disaster Recovery** - Create backups of your Okta config as code
- **Documentation** - Generate infrastructure documentation
- **Compliance** - Track infrastructure changes over time
- **Learning** - See how Okta resources translate to Terraform

### Terraformer vs Manual Import

| Feature | Terraformer | Manual `terraform import` |
|---------|-------------|---------------------------|
| Speed | Very fast (bulk import) | Slow (one resource at a time) |
| Accuracy | Generates complete config | Requires manual config writing |
| State | Automatically creates | Manual state management |
| Discovery | Finds all resources | Need to know resource IDs |
| Use Case | Initial migration | Single resource import |

## 📦 Prerequisites

### Required Tools

1. **Terraform** (>= 1.9.0)
   ```bash
   # Using tfenv (recommended)
   tfenv install 1.9.0
   tfenv use 1.9.0
   
   # Or direct install
   # https://www.terraform.io/downloads
   ```

2. **Terraformer** (>= 0.8.24)
   ```bash
   # macOS
   brew install terraformer
   
   # Linux
   curl -LO https://github.com/GoogleCloudPlatform/terraformer/releases/download/$(curl -s https://api.github.com/repos/GoogleCloudPlatform/terraformer/releases/latest | grep tag_name | cut -d '"' -f 4)/terraformer-all-linux-amd64
   chmod +x terraformer-all-linux-amd64
   sudo mv terraformer-all-linux-amd64 /usr/local/bin/terraformer
   
   # Windows
   # Download from: https://github.com/GoogleCloudPlatform/terraformer/releases
   ```

3. **Python 3.8+** (for cleanup scripts)
   ```bash
   python3 --version
   ```

### Optional but Recommended

- **tfenv** - Terraform version manager
- **direnv** - Environment variable management
- **jq** - JSON processing (for scripts)

### Okta Setup

1. **Okta Development Org** (free at https://developer.okta.com)
2. **API Token** with admin privileges
   - Navigate to: Security → API → Tokens
   - Create Token with full admin access

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd okta-terraform-oig-demo
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x scripts/import_okta_resources.sh
chmod +x scripts/cleanup_terraform.py
```

### 3. Setup Environment Variables

```bash
# Create .envrc file (for direnv)
cat > .envrc <<EOF
export OKTA_API_TOKEN="00abc...xyz"
export OKTA_ORG_NAME="dev-12345678"
export OKTA_BASE_URL="okta.com"
EOF

# Allow direnv
direnv allow .

# Or source manually
source .envrc
```

Alternatively, export directly:

```bash
export OKTA_API_TOKEN="your-token"
export OKTA_ORG_NAME="your-org-name"
export OKTA_BASE_URL="okta.com"
```

## 🎬 Quick Start

### Option 1: Automated Import (Recommended)

Use our automated script to import all resources:

```bash
# Run the automated import script
./scripts/import_okta_resources.sh

# Script will:
# 1. Check prerequisites
# 2. Backup existing generated/ directory
# 3. Import all supported resource types
# 4. Organize imported resources
# 5. Generate summary report
```

### Option 2: Manual Import

Import specific resource types manually:

```bash
# Initialize Terraform
terraform init

# Import users only
terraformer import okta --resources=okta_user

# Import multiple resource types
terraformer import okta --resources=okta_user,okta_group,okta_app_oauth

# Import everything (use with caution on large orgs)
terraformer import okta --resources=okta_user,okta_group,okta_group_rule,okta_app_oauth,okta_app_saml,okta_auth_server,okta_policy_mfa
```

### Option 3: Selective Import with Filters

Import specific resources by ID:

```bash
# Import specific users by ID
terraformer import okta --resources=okta_user --filter="okta_user=id1:id2:id3"

# Import specific groups
terraformer import okta --resources=okta_group --filter="okta_group=00g123:00g456"
```

## 📖 Detailed Workflow

### Step 1: Import Resources

```bash
# Create basic okta.tf provider config
cat > okta.tf <<EOF
terraform {
  required_providers {
    okta = {
      source  = "okta/okta"
      version = "~> 6.1.0"
    }
  }
}

provider "okta" {
  org_name  = "${OKTA_ORG_NAME}"
  base_url  = "${OKTA_BASE_URL}"
  api_token = "${OKTA_API_TOKEN}"
}
EOF

# Initialize provider
terraform init

# Import resources
terraformer import okta --resources=okta_user,okta_group,okta_app_oauth
```

### Step 2: Review Generated Files

```bash
# View structure
tree generated/

# Output example:
# generated/
# └── okta/
#     ├── okta_user/
#     │   ├── provider.tf
#     │   ├── user.tf
#     │   ├── outputs.tf
#     │   └── terraform.tfstate
#     ├── okta_group/
#     │   ├── provider.tf
#     │   ├── group.tf
#     │   └── terraform.tfstate
#     └── okta_app_oauth/
#         ├── provider.tf
#         ├── app_oauth.tf
#         └── terraform.tfstate
```

### Step 3: Clean Up Generated Files

Run the cleanup script:

```bash
python3 scripts/cleanup_terraform.py \
  --input generated/okta \
  --output cleaned
```

The cleanup script will:
- Remove `tfer--` prefixes from resource names
- Remove null values and empty blocks
- Extract variables from hardcoded values
- Update all resource references
- Organize files by resource type
- Generate import commands

### Step 4: Review Cleaned Files

```bash
cd cleaned

# View organized structure
tree .

# Output example:
# cleaned/
# ├── identity/
# │   └── identity.tf
# ├── applications/
# │   └── applications.tf
# ├── policies/
# │   └── policies.tf
# ├── main.tf
# ├── variables.tf
# ├── resource_mapping.json
# ├── import_commands.sh
# └── CLEANUP_SUMMARY.md
```

### Step 5: Test Configuration

```bash
cd cleaned

# Initialize
terraform init

# Validate
terraform validate

# Plan (should show no changes if state was preserved)
terraform plan

# If importing fresh (without state), run imports
./import_commands.sh
```

### Step 6: Integrate with Existing Code

```bash
# Copy cleaned files to your terraform directory
cp -r cleaned/* ../terraform/imported/

# Review and merge with existing configuration
cd ../terraform
```

## 📚 Resource Types

### Supported Okta Resources

Terraformer supports these Okta resource types:

#### Identity & Access
- ✅ `okta_user` - User accounts
- ✅ `okta_group` - Groups
- ✅ `okta_group_rule` - Dynamic group rules
- ✅ `okta_group_membership` - Group memberships (deprecated, use okta_group_memberships)

#### Applications
- ✅ `okta_app_oauth` - OAuth/OIDC applications
- ✅ `okta_app_saml` - SAML applications
- ✅ `okta_app_basic_auth` - Basic auth applications
- ✅ `okta_app_bookmark` - Bookmark applications
- ✅ `okta_app_secure_password_store` - SWA applications

#### Authorization
- ✅ `okta_auth_server` - Custom authorization servers
- ✅ `okta_auth_server_policy` - Auth server policies
- ✅ `okta_auth_server_policy_rule` - Auth server policy rules
- ✅ `okta_auth_server_claim` - Custom claims
- ✅ `okta_auth_server_scope` - Custom scopes

#### Policies
- ✅ `okta_policy_mfa` - MFA policies
- ✅ `okta_policy_password` - Password policies
- ✅ `okta_policy_signon` - Sign-on policies
- ✅ `okta_policy_rule_signon` - Sign-on policy rules
- ✅ `okta_policy_rule_password` - Password policy rules
- ✅ `okta_policy_rule_mfa` - MFA policy rules

#### Security
- ✅ `okta_network_zone` - Network zones
- ✅ `okta_trusted_origin` - Trusted origins

#### Identity Providers
- ✅ `okta_idp_saml` - SAML identity providers
- ✅ `okta_idp_oidc` - OIDC identity providers
- ✅ `okta_idp_social` - Social identity providers

#### Schemas
- ✅ `okta_user_schema` - User schema attributes
- ✅ `okta_group_schema` - Group schema attributes

#### Other
- ✅ `okta_inline_hook` - Inline hooks
- ✅ `okta_event_hook` - Event hooks

### Not Yet Supported by Terraformer

These resources exist in the Terraform provider (v6.x/v7.x) but aren't in Terraformer yet:

- ❌ `okta_campaign` - Access certification campaigns
- ❌ `okta_entitlement` / `okta_entitlement_bundle` - Entitlements and bundles
- ❌ `okta_request_condition` - Request conditions
- ❌ `okta_request_sequence` - Approval sequence bindings
- ❌ `okta_request_setting_organization` / `okta_request_setting_resource` - Request settings
- ❌ `okta_request_v2` - Access requests
- ❌ `okta_resource_owner` - Resource owners
- ❌ `okta_label` - Label definitions
- ❌ `okta_realm` / `okta_realm_assignment`, `okta_app_connection`, `okta_app_features`, `okta_group_owners` - newer resources
- ❌ Label-to-resource assignment and risk rules (API only)

> **Note**: For OIG resources, you'll need to create these manually or use our Python API management scripts.

## 🧹 Cleanup & Refactoring

### Common Issues in Generated Code

1. **Resource Names with `tfer--` Prefix**
   ```hcl
   # Before
   resource "okta_user" "tfer--00u1234567890abcdef" {
   
   # After cleanup
   resource "okta_user" "john_doe" {
   ```

2. **Null Values**
   ```hcl
   # Before
   custom_profile_attributes = null
   
   # After cleanup (removed)
   ```

3. **Computed Attributes**
   ```hcl
   # Before
   id = "00u1234567890abcdef"
   status = "ACTIVE"
   
   # After cleanup (removed computed values)
   ```

4. **Hardcoded Values**
   ```hcl
   # Before
   email = "user@example.com"
   
   # After cleanup
   email = "${var.user_name}@${var.email_domain}"
   ```

### Manual Cleanup Tips

After running the automated cleanup:

1. **Rename Resources Meaningfully**
   ```hcl
   # Instead of generic names
   resource "okta_group" "group_001" {
   
   # Use descriptive names
   resource "okta_group" "engineering_team" {
   ```

2. **Extract Common Patterns to Locals**
   ```hcl
   locals {
     common_user_attributes = {
       department = "Engineering"
       division   = "Technology"
     }
   }
   ```

3. **Use Data Sources for Dynamic Lookups**
   ```hcl
   # Instead of hardcoding IDs
   group_id = "00g123456"
   
   # Use data source
   data "okta_group" "engineering" {
     name = "Engineering"
   }
   
   group_id = data.okta_group.engineering.id
   ```

4. **Add Lifecycle Rules**
   ```hcl
   resource "okta_user" "imported_user" {
     # ...
     
     lifecycle {
       ignore_changes = [
         password,  # Don't manage passwords
         status,    # Don't manage user status
       ]
     }
   }
   ```

5. **Organize into Modules**
   ```
   modules/
   ├── users/
   ├── groups/
   ├── applications/
   └── policies/
   ```

## 💡 Best Practices

### 1. Start Small

Don't import everything at once:

```bash
# Phase 1: Import core identity
terraformer import okta --resources=okta_user,okta_group

# Phase 2: Import applications
terraformer import okta --resources=okta_app_oauth,okta_app_saml

# Phase 3: Import policies
terraformer import okta --resources=okta_policy_mfa,okta_policy_signon
```

### 2. Use Filters for Large Orgs

```bash
# Import only active users
terraformer import okta --resources=okta_user \
  --filter="okta_user=status=ACTIVE"

# Import specific app types
terraformer import okta --resources=okta_app_oauth \
  --filter="Name=Production*"
```

### 3. Version Control Strategy

```bash
# Create a branch for imports
git checkout -b import/okta-resources

# Import and commit each resource type separately
terraformer import okta --resources=okta_user
git add generated/okta/okta_user
git commit -m "Import Okta users"

terraformer import okta --resources=okta_group
git add generated/okta/okta_group
git commit -m "Import Okta groups"
```

### 4. Test in Non-Production First

```bash
# Import from dev org first
export OKTA_ORG_NAME="dev-12345678"
terraformer import okta --resources=okta_user

# Validate and refine process

# Then import from production
export OKTA_ORG_NAME="prod-87654321"
terraformer import okta --resources=okta_user
```

### 5. Document Custom Changes

```hcl
# Mark resources that were manually modified
resource "okta_app_oauth" "custom_app" {
  # CUSTOM: Modified from imported config
  # Original: label = "My App"
  # Changed to use variable
  label = var.app_name
  
  # ...
}
```

## 🔄 Integration with OIG Demo

### Combining Imported Resources with OIG

1. **Import Base Resources**
   ```bash
   # Import existing users, groups, apps
   ./scripts/import_okta_resources.sh
   ```

2. **Clean Up Imports**
   ```bash
   python3 scripts/cleanup_terraform.py \
     --input generated/okta \
     --output terraform/imported
   ```

3. **Add OIG Configuration**
   ```bash
   cd terraform
   
   # Use imported resources in OIG config
   # Make an imported app requestable (catalog entries are read-only data sources)
   resource "okta_request_condition" "imported_app" {
     name                 = "Request ${okta_app_oauth.existing_app.label}"
     resource_id          = okta_app_oauth.existing_app.id  # From import
     approval_sequence_id = "<approval-sequence-id>"
     requester_settings {
       type = "EVERYONE"
     }
     access_scope_settings {
       type = "RESOURCE_DEFAULT"
     }
   }
   ```

4. **Configure Resource Owners for Imported Apps**
   ```hcl
   locals {
     imported_app_owners = [
       for app in [okta_app_oauth.app1, okta_app_oauth.app2] : {
         app_name       = app.label
         app_id         = app.id
         app_type       = "oauth2"
         owner_user_ids = [var.admin_user_id]
       }
     ]
   }
   
   module "api_management" {
     source = "./modules/api-management"
     
     app_owner_configs = local.imported_app_owners
   }
   ```

### Example: Complete Migration Workflow

```bash
#!/bin/bash
# complete_migration.sh

# 1. Import existing Okta config
echo "Step 1: Importing existing Okta resources..."
./scripts/import_okta_resources.sh

# 2. Clean up imported files
echo "Step 2: Cleaning up generated files..."
python3 scripts/cleanup_terraform.py \
  --input generated/okta \
  --output terraform/imported

# 3. Move to terraform directory
cd terraform/imported

# 4. Test import
echo "Step 3: Testing imported configuration..."
terraform init
terraform plan

# 5. Add OIG configuration
echo "Step 4: Adding OIG configuration..."
cp ../main.tf ./main-oig.tf
cp ../variables.tf ./variables-oig.tf

# 6. Configure API management
echo "Step 5: Configuring API management..."
cat > api_config_imported.json <<EOF
{
  "okta_org_name": "${OKTA_ORG_NAME}",
  "okta_api_token": "${OKTA_API_TOKEN}",
  "resource_owners": [],
  "labels": []
}
EOF

# 7. Generate resource owners for all imported apps
echo "Step 6: Generating resource owners..."
python3 ../../scripts/generate_owners_from_import.py \
  --state terraform.tfstate \
  --output api_config_imported.json

# 8. Apply API management
echo "Step 7: Applying API management..."
python3 ../../scripts/okta_api_manager.py \
  --action apply \
  --config api_config_imported.json

echo "Migration complete!"
```

## 🐛 Troubleshooting

### Issue: "Provider not found"

**Error:**
```
Error: provider not found
```

**Solution:**
```bash
# Initialize Terraform first
terraform init

# Then run terraformer
terraformer import okta --resources=okta_user
```

### Issue: "Rate limit exceeded"

**Error:**
```
Error: API rate limit exceeded
```

**Solution:**
```bash
# Import in smaller batches
terraformer import okta --resources=okta_user --filter="okta_user=id1:id2:id3"

# Add delays between imports
terraformer import okta --resources=okta_user
sleep 60
terraformer import okta --resources=okta_group
```

### Issue: "Resource not supported"

**Error:**
```
Resource type 'okta_campaign' is not supported
```

**Solution:**
- Check Terraformer documentation for supported resources
- For unsupported resources, create manually or use API scripts

### Issue: "Invalid credentials"

**Error:**
```
Error: invalid credentials
```

**Solution:**
```bash
# Verify environment variables
echo $OKTA_API_TOKEN
echo $OKTA_ORG_NAME
echo $OKTA_BASE_URL

# Re-export if needed
export OKTA_API_TOKEN="your-token"
```

### Issue: "Too many resources"

**Error:**
Memory or timeout issues with large imports

**Solution:**
```bash
# Use filters to import in chunks
terraformer import okta --resources=okta_user \
  --filter="okta_user=00u001:00u002:00u003"

# Or import by resource type separately
for resource in okta_user okta_group okta_app_oauth; do
  terraformer import okta --resources=$resource
  sleep 30
done
```

## 📚 Additional Resources

- [Terraformer Documentation](https://github.com/GoogleCloudPlatform/terraformer)
- [Terraformer Okta Provider Docs](https://github.com/GoogleCloudPlatform/terraformer/blob/master/docs/okta.md)
- [Okta Terraform Provider](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Terraform Import Command](https://www.terraform.io/docs/cli/import/index.html)

## 🎓 Next Steps

After importing and cleaning up:

1. **Review and test** all imported resources
2. **Add OIG configuration** for governance
3. **Configure resource owners and labels** via API
4. **Set up CI/CD** for automated deployments
5. **Document** your Terraform modules and workflows

---

**Happy Importing! 🚀**
