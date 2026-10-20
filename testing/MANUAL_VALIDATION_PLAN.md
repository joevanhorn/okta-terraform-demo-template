# Manual Validation Plan - Okta Terraform Complete Demo

This document provides a comprehensive manual validation plan for testing the Okta Terraform configuration across all environments and workflows.

**Last Updated:** 2025-11-09
**Estimated Time:** 2-3 hours for complete validation
**Required Access:** Okta Admin Console, GitHub Actions, Local Terminal, AWS Console

---

## 📋 Table of Contents

1. [Pre-Validation Checklist](#1-pre-validation-checklist)
2. [Environment Validation](#2-environment-validation)
3. [Import Workflow Validation](#3-import-workflow-validation)
4. [Resource Management Validation](#4-resource-management-validation)
5. [OIG Governance Validation](#5-oig-governance-validation)
6. [State Management Validation](#6-state-management-validation)
7. [Documentation Validation](#7-documentation-validation)
8. [Security Validation](#8-security-validation)
9. [Cleanup and Rollback](#9-cleanup-and-rollback)
10. [Validation Sign-Off](#10-validation-sign-off)

---

## 1. Pre-Validation Checklist

### 1.1 Environment Setup

**Objective:** Verify all required tools and access are configured

- [ ] **Terraform Installed**
  ```bash
  terraform version
  # Expected: Terraform v1.9.0 or higher
  ```
  - ✅ Pass: Version >= 1.9.0
  - ❌ Fail: Version < 1.9.0 or not installed

- [ ] **Okta Provider Version**
  ```bash
  cd environments/myorg/terraform
  terraform version
  # Expected: provider registry.terraform.io/okta/okta v7.0.0+
  ```
  - ✅ Pass: Provider v7.0.0 or higher (required for OIG resources)
  - ❌ Fail: Version < 7.0.0 or missing

- [ ] **Python 3.8+ Installed**
  ```bash
  python3 --version
  # Expected: Python 3.8 or higher
  ```
  - ✅ Pass: Version >= 3.8
  - ❌ Fail: Version < 3.8

- [ ] **GitHub CLI Installed**
  ```bash
  gh --version
  # Expected: gh version 2.0.0 or higher
  ```
  - ✅ Pass: gh installed and authenticated
  - ❌ Fail: Not installed or not authenticated

- [ ] **jq Installed**
  ```bash
  jq --version
  # Expected: jq-1.6 or higher
  ```
  - ✅ Pass: jq installed
  - ❌ Fail: Not installed

- [ ] **AWS CLI Installed**
  ```bash
  aws --version
  # Expected: aws-cli/2.0.0 or higher
  ```
  - ✅ Pass: AWS CLI installed and configured
  - ❌ Fail: Not installed

### 1.2 Access Verification

- [ ] **Okta Admin Console Access**
  - Navigate to: https://myorg.oktapreview.com/admin
  - ✅ Pass: Can log in with super admin privileges
  - ❌ Fail: Cannot access or insufficient permissions

- [ ] **GitHub Repository Access**
  - Navigate to: https://github.com/joevanhorn/okta-terraform-complete-demo
  - ✅ Pass: Can view repository and trigger actions
  - ❌ Fail: No access or read-only

- [ ] **GitHub Environments Configured**
  ```bash
  gh api repos/joevanhorn/okta-terraform-complete-demo/environments | jq -r '.environments[].name'
  # Expected: MyOrg, Production, Staging, Development
  ```
  - ✅ Pass: All 4 environments exist
  - ❌ Fail: Missing environments

### 1.3 Secrets Validation

- [ ] **Repository Secret - AWS Role**
  - Check in GitHub: Settings → Secrets and variables → Actions
  - Required repository secret:
    - `AWS_ROLE_ARN`
  - ✅ Pass: Secret exists with valid ARN format
  - ❌ Fail: Missing or invalid format
  - **Expected Format:** `arn:aws:iam::ACCOUNT_ID:role/GitHubActions-OktaTerraform`

- [ ] **MyOrg Environment Secrets Present**
  - Check in GitHub: Settings → Environments → MyOrg
  - Required secrets:
    - `OKTA_API_TOKEN`
    - `OKTA_ORG_NAME`
    - `OKTA_BASE_URL`
  - ✅ Pass: All 3 secrets configured
  - ❌ Fail: Missing secrets

- [ ] **API Token Permissions**
  ```bash
  # Test API token with a simple call
  curl -X GET "https://myorg.oktapreview.com/api/v1/users?limit=1" \
    -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
    -H "Accept: application/json"
  ```
  - ✅ Pass: Returns user data (HTTP 200)
  - ❌ Fail: Permission denied or error

---

## 2. Environment Validation

### 2.1 Directory Structure

**Objective:** Verify repository structure matches documentation

- [ ] **Main Directories Present**
  ```bash
  ls -la
  # Expected directories:
  # - environments/
  # - scripts/
  # - docs/
  # - .github/workflows/
  # - testing/
  ```
  - ✅ Pass: All directories exist
  - ❌ Fail: Missing directories

- [ ] **Environment Structure**
  ```bash
  ls -la environments/myorg/
  # Expected:
  # - terraform/
  # - imports/
  # - config/
  # - README.md
  ```
  - ✅ Pass: Complete structure
  - ❌ Fail: Missing subdirectories

### 2.2 Configuration Files

- [ ] **Terraform Configuration**
  ```bash
  cd environments/myorg/terraform
  ls *.tf
  # Expected core files:
  # - provider.tf (with provider >= 7.0.0, < 8.0.0)
  # - variables.tf
  # - backend.tf (optional)
  # - oig_entitlements.tf (OIG resources)
  #
  # NOTE: Standard Okta resources (apps, users, groups) are imported
  # via terraformer into environments/myorg/imports/ directory
  # and should be consolidated into terraform/ after review
  ```
  - ✅ Pass: Core terraform files present
  - ❌ Fail: Missing provider.tf or oig_entitlements.tf

- [ ] **Terraform Init**
  ```bash
  terraform init
  # Expected: Successful initialization
  ```
  - ✅ Pass: Initializes without errors
  - ❌ Fail: Errors during initialization

- [ ] **Terraform Validate**
  ```bash
  terraform validate
  # Expected: Success! The configuration is valid.
  ```
  - ✅ Pass: Configuration is valid
  - ❌ Fail: Validation errors

### 2.3 Environment Isolation

**Objective:** Verify strict environment isolation - one directory = one Okta org

- [ ] **Verify Environment README Exists**
  ```bash
  cat environments/README.md
  # Should document isolation rules
  ```
  - ✅ Pass: README exists with isolation documentation
  - ❌ Fail: Missing or incomplete documentation

- [ ] **Verify No Cross-Environment Resources**
  ```bash
  # Lowerdecklabs should only have myorg.oktapreview.com resources
  cd environments/myorg/terraform
  grep -r "okta.com" . && echo "FAIL: Found okta.com references" || echo "PASS"
  grep -r "dev-" . && echo "FAIL: Found dev org references" || echo "PASS"

  # Expected: No references to other orgs
  ```
  - ✅ Pass: Only myorg.oktapreview.com references found
  - ❌ Fail: References to other orgs detected

- [ ] **Verify Environment-Specific Secrets**
  ```bash
  # Check GitHub environments are configured
  gh api repos/joevanhorn/okta-terraform-complete-demo/environments \
    | jq -r '.environments[] | select(.name=="MyOrg") | .name'
  # Expected: MyOrg
  ```
  - ✅ Pass: MyOrg environment exists with secrets
  - ❌ Fail: Environment missing or misconfigured

- [ ] **Verify Workflow Environment Specification**
  ```bash
  # All terraform workflows should specify environment
  grep -l "environment:" .github/workflows/terraform-*.yml | wc -l
  # Expected: All terraform workflows (at least 3)
  ```
  - ✅ Pass: All terraform workflows use environment parameter
  - ❌ Fail: Some workflows missing environment specification

- [ ] **Test Environment Isolation in Practice**
  ```bash
  # Trigger a terraform plan - should use MyOrg secrets
  gh workflow run terraform-plan.yml

  # Monitor and verify it uses myorg.oktapreview.com
  gh run watch <RUN_ID>
  # Check logs for: "Configured for org: myorg"
  ```
  - ✅ Pass: Workflow uses correct environment secrets
  - ❌ Fail: Wrong org detected or secrets not applied

---

## 3. Import Workflow Validation

### 3.1 GitHub Actions Workflow - Import All Resources

**Objective:** Test the complete import workflow

- [ ] **Trigger Workflow**
  ```bash
  gh workflow run import-all-resources.yml \
    -f tenant_environment=MyOrg \
    -f update_terraform=false \
    -f commit_changes=false
  ```
  - ✅ Pass: Workflow triggered successfully
  - ❌ Fail: Workflow failed to trigger

- [ ] **Monitor Workflow**
  ```bash
  gh run list --workflow=import-all-resources.yml --limit 1
  gh run watch <RUN_ID>
  ```
  - ✅ Pass: Workflow completes successfully (status: completed)
  - ❌ Fail: Workflow fails or times out
  - **Expected Duration:** 1-2 minutes
  - **Note Warnings:** Document any warnings in output

- [ ] **Download Artifacts**
  ```bash
  gh run download <RUN_ID>
  ls -la import-results-*/
  ```
  - Expected files:
    - `imports/entitlements.json`
    - `imports/reviews.json`
    - `terraform/oig_entitlements.tf`
    - `terraform/oig_reviews.tf`
    - `config/owner_mappings.json`
    - `config/label_mappings.json`
  - ✅ Pass: All expected files present
  - ❌ Fail: Missing files

### 3.2 Validate Import Results

- [ ] **Check Resource Counts**
  ```bash
  # Count entitlement bundles
  jq '. | length' import-results-*/imports/entitlements.json
  # Expected: 31 (based on current MyOrg tenant)

  # Count reviews
  jq '. | length' import-results-*/imports/reviews.json
  # Expected: 200 (based on current MyOrg tenant)
  ```
  - ✅ Pass: Counts match expected values (±5%)
  - ❌ Fail: Significant discrepancy (>10%)

- [ ] **Validate Terraform Syntax**
  ```bash
  cd import-results-*/terraform
  terraform fmt -check
  terraform validate
  ```
  - ✅ Pass: Valid Terraform syntax
  - ❌ Fail: Syntax errors

- [ ] **Check for Sensitive Data**
  ```bash
  # Search for potential secrets in generated files
  grep -r "SSWS" import-results-*/
  grep -r "api_token" import-results-*/
  ```
  - ✅ Pass: No secrets found
  - ❌ Fail: Secrets detected in files

### 3.3 OIG-Specific Import Workflow

**Objective:** Test the dedicated OIG import workflow

- [ ] **Trigger OIG Import Workflow**
  ```bash
  # Note: Use import-all-resources.yml instead of archived import-oig workflow
  gh workflow run import-all-resources.yml \
    -f tenant_environment=MyOrg \
    -f update_terraform=false \
    -f commit_changes=false
  ```
  - ✅ Pass: Workflow triggered successfully
  - ❌ Fail: Workflow failed to trigger
  - **Note:** The new `import-all-resources.yml` replaces archived import workflows

- [ ] **Monitor OIG Workflow**
  ```bash
  gh run list --workflow=import-all-resources.yml --limit 1
  gh run watch <RUN_ID>
  ```
  - ✅ Pass: Workflow completes successfully
  - ❌ Fail: Workflow fails or times out
  - **Expected Duration:** 2-5 minutes (imports both base and OIG resources)
  - **Note:** This workflow includes both Terraformer and API-based imports

- [ ] **Verify OIG Artifacts**
  ```bash
  gh run download <RUN_ID>
  ls -la oig-import-*/
  ```
  - Expected OIG files:
    - `imports/entitlements.json`
    - `imports/reviews.json`
    - `terraform/oig_entitlements.tf`
    - `terraform/oig_reviews.tf`
  - ✅ Pass: All OIG files present and valid
  - ❌ Fail: Missing or corrupted OIG files

- [ ] **Validate OIG Resource Structure**
  ```bash
  # Check entitlement bundle structure
  jq '.[0] | keys' oig-import-*/imports/entitlements.json
  # Expected keys: id, name, description, etc.

  # Check reviews structure
  jq '.[0] | keys' oig-import-*/imports/reviews.json
  # Expected keys: id, name, type, status, etc.
  ```
  - ✅ Pass: Valid JSON structure with expected fields
  - ❌ Fail: Malformed or incomplete data

- [ ] **Test Workflow with Auto-Commit**
  ```bash
  # Test with update_terraform=true to verify end-to-end flow
  gh workflow run import-all-resources.yml \
    -f tenant_environment=MyOrg \
    -f update_terraform=true \
    -f commit_changes=true

  gh run watch <RUN_ID>
  ```
  - ✅ Pass: Workflow completes and creates commit
  - ❌ Fail: Workflow fails or doesn't commit
  - **Note:** Check that commit message follows format and includes updated files

### 3.4 Complete Environment Import with Terraformer

**Objective:** Test complete environment import with terraformer for all standard Okta resources

- [ ] **Trigger Complete Environment Import**
  ```bash
  # Note: Use import-all-resources.yml for complete imports
  gh workflow run import-all-resources.yml \
    -f tenant_environment=MyOrg \
    -f update_terraform=false \
    -f commit_changes=false
  ```
  - ✅ Pass: Workflow triggered successfully
  - ❌ Fail: Workflow failed to trigger
  - **Note:** This workflow replaces `myorg-import-complete.yml`

- [ ] **Monitor Terraformer Import Workflow**
  ```bash
  gh run list --workflow=import-all-resources.yml --limit 1
  gh run watch <RUN_ID>
  ```
  - ✅ Pass: Workflow completes successfully
  - ❌ Fail: Workflow fails or times out
  - **Expected Duration:** 5-10 minutes (depending on org size)
  - **Note:** Imports ALL resources (base via Terraformer + OIG via API)

- [ ] **Verify Terraformer Artifacts**
  ```bash
  gh run download <RUN_ID>
  ls -la terraformer-import-*/
  ```
  - Expected directory structure:
    - `identity/` - Users, groups, group rules
    - `applications/` - OAuth, SAML, SWA apps
    - `authorization/` - Auth servers, policies, claims, scopes
    - `policies/` - MFA, password, sign-on policies
    - `security/` - Network zones, trusted origins, IdPs
    - `schemas/` - User and group custom attributes
    - `IMPORT_SUMMARY.md` - Import summary report
  - ✅ Pass: All categories present with terraform files
  - ❌ Fail: Missing categories or malformed structure

- [ ] **Validate Terraformer Import Quality**
  ```bash
  # Check that terraform files are valid
  cd terraformer-import-*/identity/okta_user
  terraform validate

  # Check for tfer-- prefixes (expected in raw terraformer output)
  grep -r "tfer--" . | wc -l
  # Expected: >0 (terraformer adds tfer-- prefixes)
  ```
  - ✅ Pass: Valid terraform syntax, tfer-- prefixes present (expected)
  - ❌ Fail: Invalid terraform or unexpected resource names

- [ ] **Verify Environment Isolation**
  ```bash
  # Confirm import went to correct environment directory
  ls -la environments/myorg/imports/terraformer-*/

  # Verify no cross-contamination with other environments
  ls environments/ | grep -v myorg
  # Should show no terraformer imports in other environment dirs
  ```
  - ✅ Pass: Import only in myorg, isolated from other environments
  - ❌ Fail: Cross-environment contamination detected

---

## 4. Resource Management Validation

### 4.1 Terraform Plan (Read-Only)

**Objective:** Verify Terraform can plan without making changes

- [ ] **Initial Plan**
  ```bash
  cd environments/myorg/terraform
  terraform plan -out=tfplan
  ```
  - ✅ Pass: Plan succeeds, shows existing resources
  - ❌ Fail: Plan errors or shows unexpected changes
  - **Expected Output:** Should show current state, no pending changes (or only additions if new resources imported)

- [ ] **Plan Output Analysis**
  ```bash
  terraform show -json tfplan | jq '.resource_changes | length'
  # Expected: 0 (if no changes) or count of new resources
  ```
  - ✅ Pass: Output matches expectations
  - ❌ Fail: Unexpected resource modifications or deletions

### 4.2 Create Test Resources

**Objective:** Verify ability to create new resources

- [ ] **Create Test User**
  ```bash
  # Add to user.tf or create test_user.tf
  cat > test_resources.tf <<'EOF'
  resource "okta_user" "validation_test_user" {
    email      = "validation.test@example.com"
    first_name = "Validation"
    last_name  = "Test"
    login      = "validation.test@example.com"
    status     = "STAGED"  # Won't send activation email
  }
  EOF

  terraform plan
  # Expected: Shows 1 resource to add
  ```
  - ✅ Pass: Plan shows 1 addition
  - ❌ Fail: Errors or unexpected changes

- [ ] **Apply Test User**
  ```bash
  terraform apply -auto-approve
  # Expected: Successfully created
  ```
  - ✅ Pass: User created successfully
  - ❌ Fail: Apply failed
  - **Record User ID:** `______________________`

- [ ] **Verify in Okta Admin Console**
  - Navigate to: Directory → People
  - Search for: validation.test@example.com
  - ✅ Pass: User exists in Okta
  - ❌ Fail: User not found

- [ ] **Verify State File**
  ```bash
  terraform state list | grep validation_test_user
  # Expected: okta_user.validation_test_user
  ```
  - ✅ Pass: Resource in state
  - ❌ Fail: Not in state

### 4.3 Update Test Resources

**Objective:** Verify ability to update existing resources

- [ ] **Modify Test User**
  ```bash
  # Update test_resources.tf
  # Change first_name from "Validation" to "Updated"

  terraform plan
  # Expected: Shows 1 resource to update
  ```
  - ✅ Pass: Shows in-place update
  - ❌ Fail: Shows replacement or errors

- [ ] **Apply Update**
  ```bash
  terraform apply -auto-approve
  ```
  - ✅ Pass: Update successful
  - ❌ Fail: Update failed

- [ ] **Verify Update in Okta**
  - Check user profile in Okta Admin Console
  - ✅ Pass: First name updated to "Updated"
  - ❌ Fail: Change not reflected

### 4.4 Drift Detection

**Objective:** Verify Terraform detects manual changes

- [ ] **Manual Change in Okta**
  - In Okta Admin Console:
    - Navigate to validation test user
    - Change last name to "ManualChange"
    - Save

- [ ] **Detect Drift**
  ```bash
  terraform plan -refresh-only
  # Expected: Shows drift detected
  ```
  - ✅ Pass: Drift detected
  - ❌ Fail: No drift detected

- [ ] **Refresh State**
  ```bash
  terraform apply -refresh-only -auto-approve
  terraform plan
  # Expected: Shows change to revert last_name back to "Test"
  ```
  - ✅ Pass: Plan shows correction needed
  - ❌ Fail: No changes detected

---

## 5. OIG Governance Validation

### 5.1 Entitlement Bundles

**Objective:** Verify OIG entitlement bundle import and management

- [ ] **Review Imported Bundles**
  ```bash
  cd environments/myorg/imports
  jq '.[0]' entitlements.json
  # Review structure of first bundle
  ```
  - ✅ Pass: Valid JSON structure with expected fields
  - ❌ Fail: Malformed or missing data

- [ ] **Check Terraform Configuration**
  ```bash
  cd ../terraform
  grep -c "resource \"okta_entitlement_bundle\"" oig_entitlements.tf
  # Expected: 31 (or current count)
  ```
  - ✅ Pass: Resource count matches import count
  - ❌ Fail: Mismatch

- [ ] **Verify in Okta Admin Console**
  - Navigate to: Identity Governance → Entitlements
  - ✅ Pass: Can see entitlement bundles
  - ❌ Fail: Page not accessible or empty

### 5.2 Access Reviews

- [ ] **Review Imported Campaigns**
  ```bash
  jq '.[0]' ../imports/reviews.json
  # Review structure
  ```
  - ✅ Pass: Valid structure
  - ❌ Fail: Invalid or missing data

- [ ] **Check Terraform Configuration**
  ```bash
  grep -c "resource \"okta_campaign\"" oig_reviews.tf
  # Expected: 200 (or current count)
  ```
  - ✅ Pass: Count matches
  - ❌ Fail: Mismatch

### 5.3 Resource Owners (API-Only)

**Objective:** Verify API-based resource owner management

- [ ] **Sync Resource Owners**
  ```bash
  python3 ../../scripts/sync_owner_mappings.py \
    --output ../config/owner_mappings.json
  ```
  - ✅ Pass: Completes successfully
  - ❌ Fail: Script errors

- [ ] **Validate JSON Structure**
  ```bash
  jq '.' ../config/owner_mappings.json
  # Expected: Valid JSON with apps, groups, bundles sections
  ```
  - ✅ Pass: Valid structure
  - ❌ Fail: Malformed JSON

- [ ] **Test Apply Owners**
  ```bash
  python3 ../../scripts/apply_resource_owners.py \
    --config ../config/owner_mappings.json \
    --dry-run
  ```
  - ✅ Pass: Dry run successful, shows changes
  - ❌ Fail: Errors during dry run

### 5.4 Governance Labels (API-Only)

**Objective:** Verify hierarchical label management system

#### 5.4.1 Sync Labels from Okta

- [ ] **Sync Governance Labels**
  ```bash
  python3 ../../scripts/sync_label_mappings.py \
    --output ../config/label_mappings.json
  ```
  - ✅ Pass: Completes successfully
  - ❌ Fail: Script errors

- [ ] **Validate Hierarchical Structure**
  ```bash
  jq '.labels | length' ../config/label_mappings.json
  # Expected: 3 (Privileged, Crown Jewel, Compliance)

  jq '.labels.Compliance.type' ../config/label_mappings.json
  # Expected: "multi_value"

  jq '.labels.Compliance.values | keys' ../config/label_mappings.json
  # Expected: ["SOX", "GDPR", "PII"]
  ```
  - ✅ Pass: Hierarchical structure correct, multi-value labels supported
  - ❌ Fail: Flat structure or missing values

- [ ] **Validate Assignment Format**
  ```bash
  jq '.assignments.apps | keys' ../config/label_mappings.json
  # Expected: Includes "Compliance:SOX", "Compliance:GDPR", "Compliance:PII"
  ```
  - ✅ Pass: Uses "Label:Value" format for multi-value labels
  - ❌ Fail: Wrong format

#### 5.4.2 Apply Labels to Okta (Dry Run)

- [ ] **Test Dry Run Mode**
  ```bash
  python3 ../../scripts/apply_labels_from_config.py \
    --config ../config/label_mappings.json \
    --dry-run
  ```
  - ✅ Pass: Completes without errors, shows what would be done
  - ❌ Fail: Errors during dry run

- [ ] **Verify Dry Run Output**
  - Check console output for:
    - Labels that would be created
    - Label values that would be created
    - Assignments that would be applied
  - ✅ Pass: Output shows expected operations
  - ❌ Fail: Unexpected operations or errors

- [ ] **Check Results JSON**
  ```bash
  jq '.' label_application_results.json
  # Expected fields:
  # - dry_run: true
  # - labels_created: number
  # - labels_skipped: number
  # - label_values_created: number
  # - assignments_applied: number
  # - errors: []
  ```
  - ✅ Pass: Results JSON has all expected fields
  - ❌ Fail: Missing fields or errors array not empty

#### 5.4.3 GitOps Label Validation Workflow

The repository uses a two-phase GitOps approach for label management:

**Phase 1: PR Validation (Syntax Check)**
- Validates JSON syntax and ORN formats on PRs
- No Okta API calls required (no secrets needed)
- Posts validation results as PR comments

**Phase 2: Deployment Validation (API Check)**
- Runs automatically on merge to main (dry-run mode)
- Manual dispatch for actual deployment (dry_run=false)
- Uses environment secrets for API validation

**GitOps Flow:**
```
PR with label changes → Syntax validation (automatic)
  ↓
Merge to main → API validation dry-run (automatic)
  ↓
Review results → Manual apply (workflow dispatch with dry_run=false)
```

##### Phase 1: PR Validation Testing

- [ ] **Create Test PR with Label Changes**
  ```bash
  # Create feature branch with label changes
  git checkout -b test/label-validation

  # Edit label configuration (add a test label or assignment)
  vim environments/myorg/config/label_mappings.json

  # Example change: Add a new label value or resource assignment
  # {
  #   "labels": {
  #     "Privileged": {
  #       "values": ["Admin", "SuperAdmin", "NewTestValue"]  # Added NewTestValue
  #     }
  #   }
  # }

  git add environments/myorg/config/label_mappings.json
  git commit -m "test: Add new label value for validation testing"
  git push -u origin test/label-validation

  # Create PR
  gh pr create \
    --title "Test: Label Validation Workflow" \
    --body "Testing the GitOps label validation workflow with PR validation"
  ```
  - ✅ Pass: PR created successfully
  - ❌ Fail: PR creation failed

- [ ] **Monitor PR Validation Workflow**
  ```bash
  # List recent workflow runs
  gh run list --workflow=validate-label-mappings.yml --limit 3

  # Watch the most recent run
  gh run watch <RUN_ID>
  ```
  - ✅ Pass: Workflow triggers automatically when PR created
  - ❌ Fail: Workflow doesn't trigger or fails to start
  - **Expected:** Runs on pull_request event when label_mappings.json changed

- [ ] **Verify PR Validation Results**
  - Check PR for automated comment from workflow:
    - ✅ Valid JSON syntax indicator
    - ✅ Valid ORN format indicator
    - ✅ Configuration summary (labels defined, assignments, resources)
    - ✅ Next steps guidance (merge → dry-run → apply)
  - ✅ Pass: Comment posted with all validation details
  - ❌ Fail: No comment or incomplete validation
  - **Note:** This validation runs WITHOUT Okta API secrets (syntax only)

- [ ] **Test Invalid JSON Scenario**
  ```bash
  # Create another branch with intentionally broken JSON
  git checkout -b test/invalid-label-json

  # Break the JSON (add trailing comma or remove bracket)
  echo '{ "labels": { "test": "missing_bracket"' > \
    environments/myorg/config/label_mappings.json

  git add environments/myorg/config/label_mappings.json
  git commit -m "test: Invalid JSON for validation testing"
  git push -u origin test/invalid-label-json

  gh pr create --title "Test: Invalid JSON Detection" --body "Testing validation error handling"
  ```
  - ✅ Pass: Workflow detects and reports JSON syntax error
  - ❌ Fail: Invalid JSON not detected
  - **Cleanup:** Close PR and delete branch after verification

- [ ] **Test Invalid ORN Format Scenario**
  ```bash
  # Create branch with invalid ORN
  git checkout main && git pull
  git checkout -b test/invalid-orn-format

  # Edit to add invalid ORN (missing 'orn:' prefix)
  vim environments/myorg/config/label_mappings.json
  # Add assignment with: "badformat:okta:app:123" instead of "orn:okta:..."

  git add environments/myorg/config/label_mappings.json
  git commit -m "test: Invalid ORN format for validation"
  git push -u origin test/invalid-orn-format

  gh pr create --title "Test: Invalid ORN Detection" --body "Testing ORN format validation"
  ```
  - ✅ Pass: Workflow detects and reports invalid ORN format
  - ❌ Fail: Invalid ORN not detected
  - **Cleanup:** Close PR and delete branch after verification

##### Phase 2: Deployment Validation Testing

- [ ] **Merge Valid PR to Main**
  ```bash
  # Merge the valid test PR from Phase 1
  gh pr merge test/label-validation --squash --delete-branch
  ```
  - ✅ Pass: PR merged successfully
  - ❌ Fail: Merge conflicts or errors

- [ ] **Verify Automatic Dry-Run Execution**
  ```bash
  # Deployment workflow should trigger automatically on push to main
  gh run list --workflow=apply-labels-from-config.yml --limit 3

  # Monitor the automatic dry-run
  gh run watch <RUN_ID>
  ```
  - ✅ Pass: Workflow runs automatically in dry-run mode
  - ❌ Fail: Workflow doesn't trigger or fails
  - **Expected:** Triggered by push to main, detects environment from file path, runs with dry_run=true

- [ ] **Review Dry-Run Results**
  - Check workflow summary for:
    - Mode indicator: "DRY RUN (no changes made)"
    - Labels to create count
    - Labels already existing count
    - Label assignments to apply count
    - Errors count (should be 0)
    - Full operation log
  - ✅ Pass: Dry-run shows what would be done without errors
  - ❌ Fail: Errors in dry-run or missing information

##### Phase 3: Manual Deployment Testing

**Warning:** Only perform if you want to actually apply label changes to Okta

- [ ] **Manual Workflow Dispatch for Apply**
  ```bash
  # Manually trigger with dry_run=false to apply changes
  gh workflow run apply-labels-from-config.yml \
    -f environment=myorg \
    -f dry_run=false
  ```
  - ✅ Pass: Workflow triggered successfully
  - ❌ Fail: Failed to trigger
  - **Note:** Environment parameter is now required

- [ ] **Monitor Apply Workflow**
  ```bash
  gh run watch <RUN_ID>
  ```
  - ✅ Pass: Workflow completes successfully, labels applied
  - ❌ Fail: Workflow fails during apply
  - **Expected Duration:** 1-2 minutes
  - **Expected Mode:** "APPLY (labels applied to Okta)"

- [ ] **Verify in Okta Admin Console**
  - Navigate to: Identity Governance → Labels
  - Check for new labels or label values created
  - Navigate to labeled resources
  - Verify assignments are correct
  - ✅ Pass: Labels visible in Okta UI, assignments correct
  - ❌ Fail: Labels not found or assignments incorrect

- [ ] **Verify Workflow Artifacts**
  ```bash
  # Download workflow artifacts for review
  gh run download <RUN_ID>

  # Review results
  cat label-application-results-*/label_application_results.json | jq '.'
  cat label-application-results-*/apply.log
  ```
  - ✅ Pass: Artifacts contain detailed results and logs
  - ❌ Fail: Missing artifacts or incomplete data

##### Validation Script Testing

- [ ] **Test Standalone Validation Script**
  ```bash
  # Run the validation script directly
  python3 scripts/validate_label_config.py \
    environments/myorg/config/label_mappings.json
  ```
  - Expected output:
    - ✅ Required structure present
    - Configuration summary (labels, assignments, resources)
    - Label list
    - ✅ All ORNs have valid format
  - ✅ Pass: Script validates configuration successfully
  - ❌ Fail: Script errors or validation failures

- [ ] **Test Validation Script with Invalid File**
  ```bash
  # Create temporary invalid config
  echo '{"invalid": "config"}' > /tmp/bad_config.json

  python3 scripts/validate_label_config.py /tmp/bad_config.json

  # Should exit with error code
  echo "Exit code: $?"
  ```
  - ✅ Pass: Script detects missing required keys and exits with error
  - ❌ Fail: Script doesn't detect invalid structure

##### Workflow Integration Testing

- [ ] **Verify Environment Protection**
  - Deployment workflow requires `environment` input parameter
  - Corresponding GitHub Environment (e.g., MyOrg) has Okta API secrets configured
  - PR validation workflow does NOT use environment (no secrets needed)
  - ✅ Pass: Correct environment usage for each workflow
  - ❌ Fail: Environment misconfiguration

- [ ] **Test Workflow Path Triggers**
  ```bash
  # Verify workflows only trigger on correct file changes
  git checkout -b test/non-label-change

  # Change a different file
  echo "# Test" >> README.md
  git add README.md
  git commit -m "test: Non-label change"
  git push -u origin test/non-label-change

  gh pr create --title "Test: Non-Label Change" --body "Should NOT trigger label validation"
  ```
  - ✅ Pass: Label validation workflow does NOT run
  - ❌ Fail: Workflow runs for non-label changes
  - **Cleanup:** Close PR and delete branch

- [ ] **Verify Workflow Permissions**
  - Check `.github/workflows/validate-label-mappings.yml` permissions:
    - `contents: read` - Can read repository
    - `pull-requests: write` - Can post PR comments
  - Check `.github/workflows/apply-labels-from-config.yml` permissions:
    - `contents: write` - Can commit if needed
    - `actions: read` - Can read workflow info
  - ✅ Pass: Minimal necessary permissions configured
  - ❌ Fail: Excessive or insufficient permissions

#### 5.4.4 API Methods Validation

- [ ] **Test create_label_with_values()**
  ```bash
  # Create test script to verify API method
  cat > /tmp/test_label_api.py <<'EOF'
  import sys
  sys.path.insert(0, '/home/joevanhorn/projects/okta-terraform-complete-demo')
  from scripts.okta_api_manager import OktaAPIManager

  manager = OktaAPIManager()

  # Test creating multi-value label
  result = manager.create_label_with_values(
      name="TestValidation",
      description="Validation test label",
      values=[
          {"name": "Value1", "description": "Test value 1"},
          {"name": "Value2", "description": "Test value 2"}
      ]
  )

  print(f"Label created: {result.get('labelId')}")
  print(f"Values: {len(result.get('values', []))}")
  EOF

  python3 /tmp/test_label_api.py
  ```
  - ✅ Pass: Label created with multiple values
  - ❌ Fail: API error or wrong structure

- [ ] **Test get_label_value_id()**
  ```python
  value_id = manager.get_label_value_id("Compliance", "SOX")
  print(f"SOX value ID: {value_id}")
  # Expected: Returns valid labelValueId
  ```
  - ✅ Pass: Returns correct labelValueId
  - ❌ Fail: Returns None or wrong ID

- [ ] **Test assign_label_values_to_resources()**
  ```python
  # Test assigning label value to test resource
  sox_id = manager.get_label_value_id("Compliance", "SOX")
  manager.assign_label_values_to_resources(
      label_value_ids=[sox_id],
      resource_orns=["orn:okta:application:..."]
  )
  # Expected: Assignment successful
  ```
  - ✅ Pass: Assignment succeeds
  - ❌ Fail: API error or assignment fails

- [ ] **Cleanup Test Label**
  - Manually delete "TestValidation" label in Okta Admin Console
  - ✅ Pass: Cleanup successful
  - ❌ Fail: Unable to delete

---

## 6. State Management Validation

### 6.1 AWS Backend Infrastructure

**Objective:** Verify AWS backend infrastructure is properly configured

- [ ] **Verify S3 Bucket Exists**
  ```bash
  aws s3 ls s3://okta-terraform-demo/
  # Expected: Bucket exists and is accessible
  ```
  - ✅ Pass: Bucket accessible
  - ❌ Fail: AccessDenied or bucket doesn't exist

- [ ] **Check S3 Bucket Versioning**
  ```bash
  aws s3api get-bucket-versioning --bucket okta-terraform-demo
  # Expected: "Status": "Enabled"
  ```
  - ✅ Pass: Versioning enabled
  - ❌ Fail: Versioning not enabled

- [ ] **Check S3 Bucket Encryption**
  ```bash
  aws s3api get-bucket-encryption --bucket okta-terraform-demo
  # Expected: AES256 or aws:kms
  ```
  - ✅ Pass: Encryption enabled
  - ❌ Fail: No encryption

- [ ] **Verify DynamoDB Lock Table**
  ```bash
  aws dynamodb describe-table --table-name okta-terraform-state-lock
  # Expected: Table exists with LockID hash key
  ```
  - ✅ Pass: Table exists and configured correctly
  - ❌ Fail: Table missing or misconfigured

- [ ] **Check IAM Role for GitHub Actions**
  ```bash
  aws iam get-role --role-name GitHubActions-OktaTerraform
  # Expected: Role exists
  ```
  - ✅ Pass: Role exists
  - ❌ Fail: Role not found

- [ ] **Verify OIDC Provider**
  ```bash
  aws iam list-open-id-connect-providers | grep token.actions.githubusercontent.com
  # Expected: Provider exists
  ```
  - ✅ Pass: OIDC provider configured
  - ❌ Fail: Provider missing

### 6.2 S3 State Storage

**Objective:** Verify state files are properly stored in S3

- [ ] **List State Files in S3**
  ```bash
  aws s3 ls s3://okta-terraform-demo/Okta-GitOps/ --recursive
  # Expected: State files for each environment
  ```
  - ✅ Pass: State files present for configured environments
  - ❌ Fail: Missing state files
  - **Environments Found:** `______`

- [ ] **Verify MyOrg State**
  ```bash
  aws s3 ls s3://okta-terraform-demo/Okta-GitOps/myorg/terraform.tfstate
  # Expected: File exists
  ```
  - ✅ Pass: State file exists
  - ❌ Fail: State file missing
  - **File Size:** `______`

- [ ] **Download and Validate State**
  ```bash
  aws s3 cp s3://okta-terraform-demo/Okta-GitOps/myorg/terraform.tfstate /tmp/state.json
  jq '.version' /tmp/state.json
  # Expected: 4 (Terraform state version)
  ```
  - ✅ Pass: Valid state file structure
  - ❌ Fail: Corrupted or invalid state

- [ ] **Check State Versions**
  ```bash
  aws s3api list-object-versions \
    --bucket okta-terraform-demo \
    --prefix Okta-GitOps/myorg/terraform.tfstate | \
    jq '.Versions | length'
  # Expected: Multiple versions (versioning working)
  ```
  - ✅ Pass: Multiple versions exist
  - ❌ Fail: Only one version (versioning not working)
  - **Version Count:** `______`

### 6.3 State Locking with DynamoDB

**Objective:** Verify state locking prevents concurrent modifications

- [ ] **Test State Lock Acquisition**
  ```bash
  cd environments/myorg/terraform
  # Terminal 1: Run this and leave waiting at "Enter a value:" prompt
  terraform apply

  # Terminal 2 (in new terminal): Try to run plan while Terminal 1 is waiting
  terraform plan
  # Expected: "Error acquiring the state lock"
  ```
  - ✅ Pass: Second command blocked by lock
  - ❌ Fail: Second command proceeds (locking not working!)
  - **Lock ID (if blocked):** `______`

- [ ] **Verify Lock Released After Operation**
  ```bash
  # After canceling Terminal 1 (Ctrl+C), run in Terminal 2:
  terraform plan
  # Expected: Plan runs successfully
  ```
  - ✅ Pass: Lock released, plan succeeds
  - ❌ Fail: Lock stuck (may need force-unlock)

- [ ] **Check DynamoDB for Locks**
  ```bash
  aws dynamodb scan --table-name okta-terraform-state-lock
  # While operation running: Expected to see lock item
  # After operation: Expected empty or no items
  ```
  - ✅ Pass: Locks appear/disappear as expected
  - ❌ Fail: Locks stuck or not appearing

- [ ] **Test Force Unlock (If Needed)**
  ```bash
  # If lock is stuck from previous test:
  terraform force-unlock <LOCK_ID>
  # LOCK_ID from error message
  ```
  - ✅ Pass: Unlock succeeds
  - ❌ Fail: Unable to unlock
  - **Notes:** `______`

### 6.4 State File Integrity

**Objective:** Verify Terraform state is valid and consistent

- [ ] **Validate State via Terraform**
  ```bash
  cd environments/myorg/terraform
  terraform state list | wc -l
  # Count resources in state
  ```
  - ✅ Pass: Returns resource count
  - ❌ Fail: Error or empty
  - **Resource Count:** `______`

- [ ] **Pull State from S3**
  ```bash
  terraform state pull > /tmp/state_validation.json
  jq '.version' /tmp/state_validation.json
  # Expected: 4 (Terraform state version)
  ```
  - ✅ Pass: Valid state version
  - ❌ Fail: Corrupted or invalid

- [ ] **Verify State Matches Reality**
  ```bash
  terraform plan -refresh-only
  # Expected: No changes if state is accurate
  ```
  - ✅ Pass: State matches Okta
  - ❌ Fail: Drift detected (may indicate state issue)
  - **Drift Items (if any):** `______`

### 6.5 GitHub Actions OIDC Authentication

**Objective:** Verify GitHub Actions can authenticate with AWS

- [ ] **Trigger Terraform Plan Workflow**
  ```bash
  # Make a trivial change and push
  git checkout -b test-aws-auth
  echo "# Test" >> environments/myorg/terraform/README.md
  git add .
  git commit -m "test: Verify AWS OIDC authentication"
  git push -u origin test-aws-auth

  # Create PR
  gh pr create --title "Test AWS Authentication" --body "Testing OIDC"
  ```
  - ✅ Pass: PR created successfully
  - ❌ Fail: Push or PR creation failed

- [ ] **Monitor Workflow for AWS Authentication**
  ```bash
  gh run list --workflow=terraform-plan.yml --limit 1
  gh run watch <RUN_ID>
  ```
  - Check for step: "Configure AWS Credentials via OIDC"
  - ✅ Pass: Authentication succeeds
  - ❌ Fail: "Error: failed to refresh cached credentials"
  - **Workflow Run:** `______`

- [ ] **Verify Terraform Init with S3 Backend**
  - Check workflow logs for "Terraform Init" step
  - Expected output should show:
    ```
    Initializing the backend...
    Successfully configured the backend "s3"!
    ```
  - ✅ Pass: Backend initialized successfully
  - ❌ Fail: Backend initialization errors

- [ ] **Verify Plan Uses Remote State**
  - Check workflow logs for state lock acquisition
  - Expected: Should show DynamoDB lock operation
  - ✅ Pass: Remote state and locking working
  - ❌ Fail: Using local state or no locking

- [ ] **Clean Up Test PR**
  ```bash
  gh pr close --delete-branch
  ```
  - ✅ Pass: PR closed and branch deleted
  - ❌ Fail: Cleanup failed

### 6.6 State Backup and Recovery

- [ ] **Create Manual State Backup**
  ```bash
  cd environments/myorg/terraform
  terraform state pull > state_backup_$(date +%Y%m%d).json
  ls -lh state_backup_*.json
  ```
  - ✅ Pass: Backup created successfully
  - ❌ Fail: Backup failed

- [ ] **Verify Backup Integrity**
  ```bash
  jq '.' state_backup_*.json > /dev/null
  echo $?
  # Expected: 0 (valid JSON)
  ```
  - ✅ Pass: Valid JSON
  - ❌ Fail: Invalid JSON (exit code != 0)

- [ ] **Test State Recovery from S3 Version**
  ```bash
  # List available versions
  aws s3api list-object-versions \
    --bucket okta-terraform-demo \
    --prefix Okta-GitOps/myorg/terraform.tfstate \
    --query 'Versions[*].[VersionId,LastModified]' \
    --output table

  # Download specific version (for reference only - don't restore yet!)
  VERSION_ID="<copy-version-id>"
  aws s3api get-object \
    --bucket okta-terraform-demo \
    --key Okta-GitOps/myorg/terraform.tfstate \
    --version-id $VERSION_ID \
    /tmp/state_old_version.json

  jq '.version' /tmp/state_old_version.json
  ```
  - ✅ Pass: Can retrieve old versions
  - ❌ Fail: Cannot access versions
  - **Number of Versions:** `______`

- [ ] **Verify S3 Access Logging**
  ```bash
  aws s3 ls s3://okta-terraform-demo-logs/state-access-logs/
  # Expected: Log files from S3 access
  ```
  - ✅ Pass: Access logs being created
  - ❌ Fail: No logs or bucket doesn't exist
  - **Recent Log Files:** `______`

---

## 7. Documentation Validation

### 7.1 README Accuracy

**Objective:** Verify documentation matches actual implementation

- [ ] **Quick Start Commands Work**
  ```bash
  # Test commands from environments/myorg/README.md
  cd environments/myorg/terraform
  terraform init
  terraform plan
  ```
  - ✅ Pass: All commands execute successfully
  - ❌ Fail: Commands fail or produce errors

- [ ] **Resource Counts Match Documentation**
  - Check `environments/myorg/README.md`
  - Expected counts:
    - Entitlement Bundles: 31
    - Access Reviews: 200
    - Governance Labels: 2
  - Compare with actual:
  ```bash
  jq '. | length' ../imports/entitlements.json
  jq '. | length' ../imports/reviews.json
  jq '.labels | length' ../config/label_mappings.json
  ```
  - ✅ Pass: Counts match (±5%)
  - ❌ Fail: Significant discrepancy

### 7.2 Resource Documentation

- [ ] **TERRAFORM_RESOURCES.md Complete**
  - Open: `docs/TERRAFORM_RESOURCES.md`
  - Verify sections present:
    - [ ] Part 1: Complete Resource Catalog (116 resources)
    - [ ] Part 2: Data Source Catalog (63 data sources)
    - [ ] Part 3: Detailed Attribute Guides
    - [ ] Part 4: Management Best Practices
  - ✅ Pass: All sections complete
  - ❌ Fail: Missing sections

- [ ] **Table of Contents Works**
  - Click various TOC links in TERRAFORM_RESOURCES.md
  - ✅ Pass: All links navigate correctly
  - ❌ Fail: Broken links

### 7.3 Workflow Documentation

- [ ] **Workflow Files Match Documentation**
  ```bash
  ls .github/workflows/*.yml | wc -l
  # Compare with docs/PROJECT_STRUCTURE.md
  ```
  - ✅ Pass: All documented workflows exist
  - ❌ Fail: Missing workflows

---

## 8. Security Validation

### 8.1 Secrets Management

**Objective:** Ensure no secrets are committed to repository

- [ ] **Search for API Tokens**
  ```bash
  git grep -i "SSWS" || echo "No tokens found"
  git grep -i "api_token" || echo "No explicit tokens found"
  ```
  - ✅ Pass: No secrets found
  - ❌ Fail: Secrets detected

- [ ] **Check .gitignore**
  ```bash
  grep -E "terraform.tfvars|.tfstate|.env" .gitignore
  ```
  - ✅ Pass: Critical files are ignored
  - ❌ Fail: Missing .gitignore entries

- [ ] **Verify State Files Not Committed**
  ```bash
  git ls-files | grep -E "\.tfstate$|terraform.tfvars$"
  echo $?
  # Expected: 1 (no matches)
  ```
  - ✅ Pass: No state files in git
  - ❌ Fail: State files committed

### 8.2 Workflow Security

- [ ] **GitHub Environment Protection**
  - Check: Settings → Environments → MyOrg
  - Verify:
    - [ ] Required reviewers: At least 1
    - [ ] Deployment branches: Protected
  - ✅ Pass: Protection rules enabled
  - ❌ Fail: No protection

- [ ] **Workflow Permissions**
  - Review: `.github/workflows/import-all-resources.yml`
  - Verify `permissions:` block exists and is minimal
  - ✅ Pass: Minimal permissions
  - ❌ Fail: Excessive permissions

---

## 9. Cleanup and Rollback

### 9.1 Remove Test Resources

**Objective:** Clean up resources created during validation

- [ ] **Remove Test User**
  ```bash
  cd environments/myorg/terraform
  rm test_resources.tf
  terraform plan
  # Expected: Shows 1 resource to destroy
  ```
  - ✅ Pass: Plan shows destruction
  - ❌ Fail: Errors or no changes

- [ ] **Apply Destruction**
  ```bash
  terraform apply -auto-approve
  ```
  - ✅ Pass: Resource destroyed
  - ❌ Fail: Destruction failed

- [ ] **Verify Removal in Okta**
  - Check Okta Admin Console
  - ✅ Pass: Test user no longer exists
  - ❌ Fail: User still present

### 9.2 Restore Original State

- [ ] **Verify Clean State**
  ```bash
  terraform plan
  # Expected: No changes
  ```
  - ✅ Pass: No pending changes
  - ❌ Fail: Unexpected changes remain

- [ ] **Remove Backup Files**
  ```bash
  rm -f state_backup_*.json
  rm -rf import-results-*/
  ```
  - ✅ Pass: Cleanup successful
  - ❌ Fail: Files remain

---

## 10. Validation Sign-Off

### 10.1 Summary Checklist

- [ ] All pre-validation checks passed
- [ ] Environment structure validated
- [ ] Import workflow completed successfully
- [ ] Resource management (CRUD operations) validated
- [ ] OIG governance features tested
- [ ] State management verified
- [ ] Documentation accurate and complete
- [ ] Security checks passed
- [ ] Cleanup completed successfully

### 10.2 Test Results Summary

**Validation Date:** `____________________`
**Validator Name:** `____________________`
**Environment:** `MyOrg`

**Results:**
- Total Tests: `____/85`
- Passed: `____`
- Failed: `____`
- Skipped: `____`

**Pass Rate:** `____%`

### 10.3 Issues Found

| Issue # | Severity | Description | Status |
|---------|----------|-------------|--------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Severity Levels:**
- **Critical:** Blocks core functionality
- **High:** Significant issue, workaround available
- **Medium:** Minor issue, does not block usage
- **Low:** Cosmetic or documentation issue

### 10.4 Recommendations

Based on validation results, document any recommendations:

1.
2.
3.

### 10.5 Sign-Off

**Validated By:** `____________________`
**Date:** `____________________`
**Signature:** `____________________`

**Approved By:** `____________________`
**Date:** `____________________`
**Signature:** `____________________`

---

## Appendix A: Troubleshooting Common Issues

### Issue: Workflow fails with "Environment not found"

**Solution:**
1. Verify environment exists in GitHub: Settings → Environments
2. Check spelling matches exactly (case-sensitive)
3. Ensure secrets are configured

### Issue: Terraform plan shows unexpected changes

**Solution:**
1. Run `terraform refresh` to sync state
2. Check for manual changes in Okta Admin Console
3. Verify `.tf` files haven't been manually edited

### Issue: Import returns 0 resources

**Solution:**
1. Verify API token has correct permissions
2. Check OKTA_ORG_NAME and OKTA_BASE_URL are correct
3. Verify resources exist in Okta tenant

### Issue: State file conflicts

**Solution:**
1. Ensure only one person/process is running Terraform
2. Use state locking (remote backend)
3. If corrupted, restore from backup

---

## Appendix B: Validation Automation

For automated validation, consider creating test scripts:

```bash
#!/bin/bash
# validate_all.sh - Automated validation runner

set -e

echo "Running validation tests..."

# Run all validation steps programmatically
# (Can be expanded based on this manual plan)

echo "✅ All validations passed!"
```

---

## Appendix C: References

- [Terraform Okta Provider Documentation](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Okta API Documentation](https://developer.okta.com/docs/reference/)
- [Project README](../README.md)
- [Resource Documentation](../docs/TERRAFORM_RESOURCES.md)
- [Environment README](../environments/myorg/README.md)

---

**End of Validation Plan**
