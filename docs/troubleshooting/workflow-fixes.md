# Workflow Fixes - Import All Resources

**Date:** 2024-12-16
**Status:** FIXED (Applied 2024-12-22)
**Affected File:** `.github/workflows/import-all-resources.yml`

---

## Issue 1: Workflow Hangs on Terraform Variable Prompt

### Problem
The workflow hangs indefinitely at Step 6 ("Import Resources into Terraform State") because Terraform prompts for OPA (Okta Privileged Access) provider variables interactively. CI environments cannot respond to interactive prompts.

### Root Cause
The `oktapam` provider may be enabled in `provider.tf` but the workflow was only passing Okta variables to `terraform.tfvars`, not the OPA variables:
- `oktapam_key`
- `oktapam_secret`
- `oktapam_team`

### Fix Applied
OPA variables are now included in the terraform.tfvars creation (around line 360):

```yaml
          # Create terraform.tfvars
          # Note: OPA variables prevent terraform init from hanging on interactive prompts
          # even if OPA provider is commented out but variables are defined
          cat > terraform.tfvars << EOF
          okta_org_name  = "${{ secrets.OKTA_ORG_NAME }}"
          okta_base_url  = "${{ secrets.OKTA_BASE_URL }}"
          okta_api_token = "${{ secrets.OKTA_API_TOKEN }}"
          oktapam_key    = "${{ secrets.OKTAPAM_KEY }}"
          oktapam_secret = "${{ secrets.OKTAPAM_SECRET }}"
          oktapam_team   = "${{ secrets.OKTAPAM_TEAM }}"
          EOF
```

### Prerequisites (if using OPA)
Ensure these secrets are configured in the GitHub Environment:
- `OKTAPAM_KEY`
- `OKTAPAM_SECRET`
- `OKTAPAM_TEAM`

**Note:** If you're not using OPA, these can be left empty - the workflow will not fail if the secrets don't exist, it just needs values (even empty) to avoid interactive prompts.

---

## Issue 2: PR Creation Fails with Exit Code 4

### Problem
Step 9 ("Create Pull Request with Changes") fails with:
```
gh: To use GitHub CLI in a GitHub Actions workflow, set the GH_TOKEN environment variable.
```

### Root Cause
The `gh` CLI requires the `GH_TOKEN` environment variable to be explicitly set, even though `github.token` is available.

### Fix Applied
`GH_TOKEN` environment variable is now set in Step 9 (around line 497):

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

## Summary of Applied Changes

| Line (approx) | Change | Status |
|---------------|--------|--------|
| ~361-370 | Add `oktapam_key`, `oktapam_secret`, `oktapam_team` to terraform.tfvars | FIXED |
| ~499-500 | Add `env: GH_TOKEN: ${{ github.token }}` to Step 9 | FIXED |

---

## Issue 3: Terraform State Lock (Runtime)

### Problem
If a previous workflow run was cancelled or failed mid-execution, a stale lock may remain in DynamoDB:
```
Error: Error acquiring the state lock
ConditionalCheckFailedException: The conditional request failed
```

### Fix
This is a runtime issue that requires manual intervention. Clear the lock from DynamoDB:

**Option A - AWS Console:**
1. Go to DynamoDB → Tables → `okta-terraform-state-lock`
2. Find and delete the item with `LockID` = `<bucket>/Okta-GitOps/<env>/terraform.tfstate`

**Option B - AWS CLI:**
```bash
aws dynamodb delete-item \
  --table-name okta-terraform-state-lock \
  --region us-east-1 \
  --key '{"LockID": {"S": "okta-terraform-demo/Okta-GitOps/<env>/terraform.tfstate"}}'
```

**Option C - Terraform Force Unlock:**
```bash
cd environments/<env>/terraform
terraform force-unlock <LOCK_ID>
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

After forking this template, run:
```bash
gh workflow run import-all-resources.yml -f tenant_environment=<your-environment>
```

The workflow should:
1. Complete Step 6 without hanging
2. Successfully create a PR in Step 9
