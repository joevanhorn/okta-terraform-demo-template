# Lessons Learned: Terraformer + Okta Terraform Provider

This document captures the issues encountered while validating the Terraformer import workflow with the Okta Terraform Provider, and how they were resolved.

## Executive Summary

**Goal:** Prove we can import existing Okta resources with Terraformer, manage them with Terraform, and make changes.

**Result:** ✅ SUCCESS - Full workflow validated end-to-end

**Key Achievement:** Successfully imported existing infrastructure, added 3 new users + 1 new app, and applied changes with zero drift.

---

## Issues Encountered & Solutions

### 1. Template String Interpolation Conflict

**Issue:** Okta uses `${source.login}` as a template variable in the `user_name_template` field. Terraform also uses `${}` for variable interpolation, causing a conflict.

**Error:**
```
Error: Reference to undeclared resource

A managed resource "source" "login" has not been declared in the root module.
```

**Root Cause:**
Terraform was trying to interpolate `${source.login}` as a Terraform variable reference instead of passing it as a literal string to Okta.

**Solution:**
Escape the dollar sign with double `$$`:

```hcl
# WRONG
user_name_template = "${source.login}"

# CORRECT
user_name_template = "$${source.login}"
```

**Fix Applied:**
```bash
sed -i '' 's/user_name_template *= *"\${source\.login}"/user_name_template = "${source.login}"/g' app_oauth.tf
```

**Files Affected:**
- `app_oauth.tf:30,61,94,etc.` - All OAuth apps with user_name_template

---

### 2. Missing Required `type` Attribute on Okta System Apps

**Issue:** Terraformer imported 5 Okta-managed internal apps (Workflows, Access Requests, IGA, etc.) without the required `type` attribute.

**Error:**
```
Error: Missing required argument

The argument "type" is required, but no definition was found.
```

**Affected Apps:**
1. `okta_app_oauth.tfer--oarf1km0tncsdlwh1d7-okta-iga-reviewer` (Okta Access Certification Reviews)
2. `okta_app_oauth.tfer--oarf1kr5tks4wmlh1d7-okta-flow-sso` (Okta Workflows)
3. `okta_app_oauth.tfer--oarf1kr9kflpyfzg1d7-okta-access-requests-resource-catalog` (Okta Identity Governance)
4. `okta_app_oauth.tfer--oarf1krcc6rgayyr1d7-flow` (Okta Workflows OAuth)
5. `okta_app_oauth.tfer--oarf1tnyf8rtprw91d7-okta-atspoke-sso` (Okta Access Requests)

**Root Cause:**
These are special Okta-managed internal applications that don't follow standard OAuth app patterns. The `okta_app_oauth` resource requires a `type` field, but these apps don't have a compatible type in the Okta API.

**Attempted Solutions:**
- ❌ Adding `type = "browser"` → Caused Terraform to want to destroy and recreate the apps
- ❌ Adding `type = "web"` → Same issue
- ❌ Using `lifecycle { ignore_changes = [type] }` → Still required the attribute

**Final Solution:**
**Exclude these apps from Terraform management entirely.**

1. Removed them from `app_oauth.tf`
2. Removed them from Terraform state:
   ```bash
   terraform state rm 'okta_app_oauth.tfer--oarf1km0tncsdlwh1d7-okta-iga-reviewer'
   terraform state rm 'okta_app_oauth.tfer--oarf1kr5tks4wmlh1d7-okta-flow-sso'
   terraform state rm 'okta_app_oauth.tfer--oarf1kr9kflpyfzg1d7-okta-access-requests-resource-catalog'
   terraform state rm 'okta_app_oauth.tfer--oarf1krcc6rgayyr1d7-flow'
   terraform state rm 'okta_app_oauth.tfer--oarf1tnyf8rtprw91d7-okta-atspoke-sso'
   ```
3. Documented in `okta_system_apps.tf.excluded` for reference

**Recommendation:**
When using Terraformer with Okta, filter out Okta system apps during import or immediately after.

**Files Affected:**
- `okta_system_apps.tf.excluded` - Reference copy of excluded apps
- `app_oauth.tf` - Removed 5 system apps

---

### 3. Terraform State Organization

**Issue:** Terraformer creates separate subdirectories with individual state files for each resource type, making it difficult to manage resources as a unified configuration.

**Directory Structure from Terraformer:**
```
production-ready/
├── users/
│   ├── user.tf
│   ├── provider.tf
│   └── terraform.tfstate
├── apps/
│   ├── app_oauth.tf
│   ├── provider.tf
│   └── terraform.tfstate
├── groups/
│   ├── group.tf
│   ├── provider.tf
│   └── terraform.tfstate
... etc
```

**Problem:**
- Each subdirectory is a separate Terraform project
- Can't manage resources together
- Duplicate provider configurations
- Hard to add cross-resource dependencies

**Solution:**
**Consolidate into a single root-level state:**

1. Copy all `.tf` resource files to root directory
2. Remove duplicate `provider.tf` files from subdirectories
3. Import all resources into root state:
   ```bash
   # Example for users
   terraform import 'okta_user.tfer--user_00urfd91ncmFPEKoH1d7' 00urfd91ncmFPEKoH1d7
   terraform import 'okta_user.tfer--user_00urfdcayfab8qED11d7' 00urfdcayfab8qED11d7
   terraform import 'okta_user.tfer--user_00urfddqbf5k0uQJG1d7' 00urfddqbf5k0uQJG1d7

   # Repeat for groups, apps, policies, auth servers
   ```
4. Keep subdirectories for reference but work from root

**Automation:**
Created import script (`/tmp/import_resources.sh`) to batch import all resources.

**Files Affected:**
- All resource files moved to root
- Root `terraform.tfstate` now tracks all resources
- Subdirectory state files kept for historical reference

---

### 4. OAuth App Visibility and Login Mode Constraints

**Issue:** Okta enforces validation rules between app visibility and login mode that caused creation failures.

**Error 1:**
```
Error: failed to create OAuth application: you have to set up 'login_uri'
to configure any 'login_mode' besides 'DISABLED'
```

**Error 2:**
```
Error: failed to create OAuth application: the API returned an error:
mode: 'idp_initiated_login.mode' cannot be DISABLED when 'visibility.hide.iOS'
or 'visibility.hide.web' is false.
```

**Root Cause:**
Okta enforces these rules:
- If `login_mode = "SPEC"`, then `login_uri` is required
- If `hide_ios = false` OR `hide_web = false`, then `login_mode` cannot be "DISABLED"

**Solution:**
For the new Team Collaboration Tool app:

```hcl
# Changed from:
hide_ios   = false
hide_web   = false
login_mode = "SPEC"

# To:
hide_ios   = true
hide_web   = true
login_mode = "DISABLED"
```

**Lesson Learned:**
For automated/API-based apps that don't need to appear in end-user dashboards, use:
- `hide_ios = true`
- `hide_web = true`
- `login_mode = "DISABLED"`

**Files Affected:**
- `app_oauth.tf:105-110` - Team Collaboration Tool app

---

### 5. Refresh Token Rotation Configuration

**Issue:** Invalid value for `refresh_token_rotation` field.

**Error:**
```
Error: failed to create OAuth application: the API returned an error:
Api validation failed: rotationType.
Causes: errorSummary: rotationType: The field has an invalid value
```

**Root Cause:**
Used `refresh_token_rotation = "ROTATE_ON_USE"` which appears to not be supported or requires additional configuration.

**Solution:**
Changed to `refresh_token_rotation = "STATIC"` to match the existing imported apps.

**Valid Values (based on testing):**
- ✅ `"STATIC"` - Works
- ❌ `"ROTATE_ON_USE"` - Failed

**Files Affected:**
- `app_oauth.tf:114` - Team Collaboration Tool app

---

### 6. Duplicate Provider Configurations

**Issue:** Each Terraformer-imported subdirectory contained its own `provider.tf` file, causing conflicts when consolidating.

**Error:**
```
Error: Duplicate provider configuration
```

**Root Cause:**
Terraformer generates a complete Terraform project for each resource type, including provider configuration.

**Solution:**
1. Keep only the root-level `provider.tf`
2. Delete provider files from subdirectories:
   ```bash
   rm users/provider.tf
   rm groups/provider.tf
   rm apps/provider.tf
   rm policies/provider.tf
   rm auth_servers/provider.tf
   ```

**Files Affected:**
- `provider.tf` (root) - Kept this one
- Subdirectory provider files - Removed

---

### 7. Repository Secrets vs Environment Secrets Confusion

**Issue:** Workflows using repository-level Okta secrets instead of environment-specific secrets caused resources to be created in the wrong Okta org.

**Error Symptom:**
- Labels appeared to exist in one org but not when queried from another org
- Different label IDs returned from different workflows
- API operations succeeded but changes weren't visible in expected org

**Example:**
```
# Workflow A (using repository secrets)
Privileged: lbc138jztfcso9bo61d7  # Org X

# Workflow B (using environment secrets: MyOrg)
Privileged: lbc11keklyNa6KhMi1d7  # Org Y (correct)
```

**Root Cause:**
The label deployment workflow was configured to use repository secrets instead of environment-specific secrets:

```yaml
# WRONG - Uses repository secrets
jobs:
  apply-labels:
    runs-on: ubuntu-latest
    # Note: Uses repository secrets instead of environment secrets

# CORRECT - Uses environment secrets
jobs:
  apply-labels:
    runs-on: ubuntu-latest
    environment: MyOrg  # ← This was missing
```

**Problem:**
- Repository secrets (`OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`) pointed to a different Okta org
- Environment secrets (under `MyOrg`) pointed to the correct org
- Workflows without `environment:` field defaulted to repository secrets
- This caused resources to be created/modified in the wrong org

**Solution:**
1. **Removed repository-level Okta secrets** to prevent confusion:
   ```bash
   gh secret delete OKTA_API_TOKEN
   gh secret delete OKTA_BASE_URL
   gh secret delete OKTA_ORG_NAME
   ```

2. **Updated all workflows** to explicitly use environment-specific secrets:
   ```yaml
   jobs:
     apply-labels:
       environment: MyOrg  # Required
   ```

3. **Kept only environment-agnostic repository secrets:**
   - `AWS_ROLE_ARN` (for Terraform state backend)
   - `CLAUDE_CODE_OAUTH_TOKEN` (for Claude Code integration)

**Lesson Learned:**
- **Never store org-specific Okta secrets at repository level**
- **Always use GitHub Environments** for org-specific secrets
- **Each environment directory should have matching GitHub Environment:**
  ```
  environments/myorg/  ← Directory
  GitHub Environment: MyOrg  ← Secrets
  ```
- **All workflows must explicitly declare `environment:`** field to use correct secrets

**Files Affected:**
- `.github/workflows/apply-labels-from-config.yml` - Updated to require environment input parameter
- Repository secrets - Removed `OKTA_API_TOKEN`, `OKTA_BASE_URL`, `OKTA_ORG_NAME`

**Validation:**
```bash
# List repository secrets (should only see AWS_ROLE_ARN and CLAUDE_CODE_OAUTH_TOKEN)
gh secret list

# List environment secrets
gh secret list -e MyOrg
```

---

## Best Practices Discovered

### 1. Template String Handling
**Always** escape Okta template variables with `$$`:
```hcl
user_name_template = "$${source.login}"
```

### 2. OAuth App Configuration
For programmatic/API-based apps:
```hcl
resource "okta_app_oauth" "api_app" {
  type                       = "web"
  login_mode                 = "DISABLED"
  hide_ios                   = true
  hide_web                   = true
  refresh_token_rotation     = "STATIC"
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
  # ... other fields
}
```

### 3. State Management
- Consolidate into single root state
- Use remote state backend (S3, Azure Blob, GCS, Terraform Cloud)
- Enable state locking to prevent conflicts
- Keep subdirectory states as backup/reference

### 4. Resource Filtering
**Exclude from Terraform management:**
- Super admin users (prevents lockout)
- Okta system apps (Workflows, IGA, Access Requests, etc.)
- Any resource you don't want accidentally destroyed

### 5. Import Workflow
```bash
# 1. Run Terraformer import
terraformer import okta --resources=user,group,app_oauth,auth_server,policy

# 2. Consolidate to root
mv */**.tf .
rm */provider.tf

# 3. Fix template strings
sed -i 's/\${source\.login}/$${source.login}/g' *.tf

# 4. Import into root state
./import_all_resources.sh

# 5. Remove Okta system apps
terraform state rm 'okta_app_oauth.tfer--oarf1...'  # repeat for each

# 6. Validate
terraform validate
terraform plan  # Should show no changes

# 7. Test adding new resources
# Add new resource to .tf file
terraform plan
terraform apply
```

### 6. GitHub Secrets Management
**CRITICAL: Use Environment-Specific Secrets for Multi-Tenant Setups**

```bash
# ❌ WRONG - Repository-level secrets for Okta
gh secret set OKTA_API_TOKEN -b "..."
gh secret set OKTA_ORG_NAME -b "myorg"
gh secret set OKTA_BASE_URL -b "oktapreview.com"

# ✅ CORRECT - Environment-level secrets
gh secret set OKTA_API_TOKEN -b "..." -e MyOrg
gh secret set OKTA_ORG_NAME -b "demo-myorg" -e MyOrg
gh secret set OKTA_BASE_URL -b "oktapreview.com" -e MyOrg
```

**Repository secrets should only contain:**
- Infrastructure secrets (AWS_ROLE_ARN, etc.)
- Tool tokens (CLAUDE_CODE_OAUTH_TOKEN, etc.)

**Environment secrets should contain:**
- Org-specific API tokens
- Org-specific configuration

**Workflow configuration:**
```yaml
jobs:
  job-name:
    runs-on: ubuntu-latest
    environment: MyOrg  # ← Always specify for org-specific jobs
```

**Verification:**
```bash
# Repository secrets - should NOT include Okta secrets
gh secret list

# Environment secrets - should include Okta secrets
gh secret list -e MyOrg
```

---

## Validation Results

### Before Changes
- **Imported Resources:** 17 resources from Okta
- **State:** Consolidated into root `terraform.tfstate`
- **Terraform Plan:** "No changes" (all imported resources matched)

### Changes Made
- Added 3 new users (alice.williams, david.chen, emma.rodriguez)
- Added 1 new OAuth app (Team Collaboration Tool)

### After Apply
```
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.
```

### Final Validation
```
terraform plan
> No changes. Your infrastructure matches the configuration.
```

**✅ Zero drift after apply - configuration validated!**

---

## Recommended Terraformer Filters

When running Terraformer import, consider using filters to exclude problematic resources:

```bash
terraformer import okta \
  --resources=user,group,app_oauth,auth_server,policy \
  --filter="okta_app_oauth=name~'^(?!.*okta_(flow|iga|atspoke|access_requests|workflows)).*$'" \
  --organizations=<your-org> \
  --okta-base-url=<domain> \
  --okta-api-token=<token>
```

Note: The filter syntax may vary depending on Terraformer version. Check documentation.

---

## Time Investment

Total time from import to validated production-ready config: **~4 hours**

Breakdown:
- Terraformer import: 15 minutes
- Troubleshooting template strings: 30 minutes
- Troubleshooting missing type attributes: 45 minutes
- State consolidation and imports: 60 minutes
- OAuth app configuration issues: 45 minutes
- Documentation: 45 minutes

**Future runs:** With this knowledge, the process should take < 1 hour.

---

## Tools & Versions Used

- **Terraform:** v1.9.x
- **Okta Terraform Provider:** v6.1.0
- **Terraformer:** v0.8.x
- **Okta:** Preview environment (oktapreview.com)

---

## Conclusion

While there were several issues encountered during the Terraformer import process, all were solvable with proper understanding of:

1. Terraform template string escaping
2. Okta API constraints and validation rules
3. The need to exclude certain Okta system resources
4. Proper state management patterns

The end result is a **production-ready** configuration that proves you can:
- ✅ Import existing Okta infrastructure with Terraformer
- ✅ Manage it with Terraform going forward
- ✅ Make changes and apply them successfully
- ✅ Maintain zero drift between config and actual state

This workflow is suitable for production use with proper remote state backend and CI/CD integration.

---

## Additional Resources

- [Okta Terraform Provider Documentation](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Terraformer Documentation](https://github.com/GoogleCloudPlatform/terraformer)
- [Terraform String Templates](https://www.terraform.io/language/expressions/strings#string-templates)
- [Okta API Reference](https://developer.okta.com/docs/reference/)
