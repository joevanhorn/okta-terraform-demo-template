# Workflow Fixes - Import All Resources

**Date:** 2024-12-16
**Affected File:** `.github/workflows/import-all-resources.yml`

## Issue 1: Workflow Hangs on Terraform Variable Prompt

### Problem
The workflow hangs indefinitely at Step 6 ("Import Resources into Terraform State") because Terraform prompts for OPA (Okta Privileged Access) provider variables interactively. CI environments cannot respond to interactive prompts.

### Root Cause
The `oktapam` provider is enabled in `provider.tf` but the workflow only passes Okta variables to `terraform.tfvars`, not the OPA variables:
- `oktapam_key`
- `oktapam_secret`
- `oktapam_team`

### Fix
In `.github/workflows/import-all-resources.yml`, find the section that creates `terraform.tfvars` (around line 360) and add the OPA variables:

**Before:**
```yaml
          # Create terraform.tfvars
          cat > terraform.tfvars << EOF
          okta_org_name  = "${{ secrets.OKTA_ORG_NAME }}"
          okta_base_url  = "${{ secrets.OKTA_BASE_URL }}"
          okta_api_token = "${{ secrets.OKTA_API_TOKEN }}"
          EOF
```

**After:**
```yaml
          # Create terraform.tfvars
          cat > terraform.tfvars << EOF
          okta_org_name  = "${{ secrets.OKTA_ORG_NAME }}"
          okta_base_url  = "${{ secrets.OKTA_BASE_URL }}"
          okta_api_token = "${{ secrets.OKTA_API_TOKEN }}"
          oktapam_key    = "${{ secrets.OKTAPAM_KEY }}"
          oktapam_secret = "${{ secrets.OKTAPAM_SECRET }}"
          oktapam_team   = "${{ secrets.OKTAPAM_TEAM }}"
          EOF
```

### Prerequisites
Ensure these secrets are configured in the GitHub Environment:
- `OKTAPAM_KEY`
- `OKTAPAM_SECRET`
- `OKTAPAM_TEAM`

---

## Issue 2: PR Creation Fails with Exit Code 4

### Problem
Step 9 ("Create Pull Request with Changes") fails with:
```
gh: To use GitHub CLI in a GitHub Actions workflow, set the GH_TOKEN environment variable.
```

### Root Cause
The `gh` CLI requires the `GH_TOKEN` environment variable to be explicitly set, even though `github.token` is available.

### Fix
In `.github/workflows/import-all-resources.yml`, find Step 9 (around line 495) and add the `env` block:

**Before:**
```yaml
      - name: "Step 9: Create Pull Request with Changes"
        if: inputs.commit_changes == 'true' && success()
        run: |
```

**After:**
```yaml
      - name: "Step 9: Create Pull Request with Changes"
        if: inputs.commit_changes == 'true' && success()
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
```

### Note
`${{ github.token }}` is automatically provided by GitHub Actions - no secret configuration needed.

---

## Summary of Changes

| Line (approx) | Change |
|---------------|--------|
| ~361-367 | Add `oktapam_key`, `oktapam_secret`, `oktapam_team` to terraform.tfvars |
| ~497-498 | Add `env: GH_TOKEN: ${{ github.token }}` to Step 9 |

---

## Issue 3: Terraform State Lock (Runtime)

### Problem
If a previous workflow run was cancelled or failed mid-execution, a stale lock may remain in DynamoDB:
```
Error: Error acquiring the state lock
ConditionalCheckFailedException: The conditional request failed
```

### Fix
Clear the lock from DynamoDB:

**Option A - AWS Console:**
1. Go to DynamoDB → Tables → `<env>-tf-state-lock`
2. Find and delete the item with `LockID` = `<bucket>/Okta-GitOps/<env>/terraform.tfstate`

**Option B - AWS CLI:**
```bash
aws dynamodb delete-item \
  --table-name <env>-tf-state-lock \
  --region <region> \
  --key '{"LockID": {"S": "<bucket>/Okta-GitOps/<env>/terraform.tfstate"}}'
```

---

## Issue 4: PR Creation Permission Denied

### Problem
```
GitHub Actions is not permitted to create or approve pull requests
```

### Fix
This is a **repository setting**, not a code fix:

1. Go to **Repository Settings**
2. Navigate to **Actions → General**
3. Scroll to **Workflow permissions**
4. Check **"Allow GitHub Actions to create and approve pull requests"**
5. Click **Save**

---

## Verification

After applying fixes, run:
```bash
gh workflow run import-all-resources.yml -f tenant_environment=<your-environment>
```

The workflow should:
1. Complete Step 6 without hanging
2. Successfully create a PR in Step 9
