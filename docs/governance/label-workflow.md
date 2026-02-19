# Label Management Workflow Guide

**Quick Start:** How to add and modify governance labels using GitOps workflow.

This guide explains the **two-phase validation pattern** used for label management and why it works this way.

---

## Table of Contents

1. [The Two-Phase Pattern](#the-two-phase-pattern)
2. [Visual Process Flow](#visual-process-flow)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Understanding the Workflows](#understanding-the-workflows)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting](#troubleshooting)

---

## The Two-Phase Pattern

Label management uses **two separate workflows** for security and flexibility:

### Phase 1: PR Validation (No Secrets)

**Purpose:** Validate syntax and format without Okta API access

**What it does:**
- ✅ Validates JSON syntax
- ✅ Checks ORN format correctness
- ✅ Validates label structure
- ❌ **Does NOT** connect to Okta
- ❌ **Does NOT** use environment secrets

**When it runs:**
- Automatically on every pull request
- When `label_mappings.json` changes

**Workflow:** `validate-label-mappings.yml`

### Phase 2: Deployment (With Secrets)

**Purpose:** Apply label changes to Okta

**What it does:**
- ✅ Connects to Okta API
- ✅ Creates/updates labels
- ✅ Assigns labels to resources
- ✅ Uses environment secrets
- ⚠️ **Changes your Okta org!**

**When it runs:**
- Auto dry-run after merge to main
- Manual apply via workflow trigger

**Workflow:** `apply-labels-from-config.yml`

### Why Two Phases?

**Problem:** GitHub Environment protection rules block PR triggers
- Can't run workflows with environment secrets on PRs from forks
- Security risk if PR validation had Okta access

**Solution:** Separate validation from deployment
- Phase 1: Syntax validation (safe, no secrets, PR-triggered)
- Phase 2: API deployment (requires secrets, manual/merge-triggered)

---

## Visual Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 1: VALIDATION                      │
│                    (No Okta Secrets)                         │
└─────────────────────────────────────────────────────────────┘

    Developer                  Pull Request                GitHub Actions
        │                           │                            │
        │  1. Edit label_mappings.json                           │
        │──────────────────────────>│                            │
        │                           │                            │
        │  2. Create PR             │                            │
        │──────────────────────────>│                            │
        │                           │                            │
        │                           │  3. Trigger validate-label-mappings.yml
        │                           │───────────────────────────>│
        │                           │                            │
        │                           │                            │  4. Validate
        │                           │                            │     - JSON syntax
        │                           │                            │     - ORN formats
        │                           │                            │     - Structure
        │                           │                            │
        │                           │  5. Post results           │
        │                           │<───────────────────────────│
        │                           │                            │
        │  6. Review results        │                            │
        │<──────────────────────────│                            │
        │                           │                            │


┌─────────────────────────────────────────────────────────────┐
│                     PHASE 2: DEPLOYMENT                      │
│                    (With Okta Secrets)                       │
└─────────────────────────────────────────────────────────────┘

        │  7. Get approval          │                            │
        │──────────────────────────>│                            │
        │                           │                            │
        │  8. Merge PR              │                            │
        │──────────────────────────>│                            │
        │                           │                            │
        │                           │  9. Trigger auto dry-run   │
        │                           │───────────────────────────>│
        │                           │                            │
        │                           │                            │  10. Dry-run with
        │                           │                            │      Okta API
        │                           │                            │      (preview only)
        │                           │                            │
        │                           │  11. Post dry-run results  │
        │                           │<───────────────────────────│
        │                           │                            │
        │  12. Review dry-run       │                            │
        │<──────────────────────────│                            │
        │                           │                            │
        │  13. Manual trigger apply (dry_run=false)              │
        │────────────────────────────────────────────────────────>│
        │                           │                            │
        │                           │                            │  14. Apply changes
        │                           │                            │      to Okta
        │                           │                            │      (LIVE!)
        │                           │                            │
        │  15. Confirm completion   │                            │
        │<────────────────────────────────────────────────────────│
```

---

## Step-by-Step Guide

### Step 1: Edit Label Configuration

```bash
# Navigate to your environment
cd environments/myenv/config

# Edit the label mappings
vim label_mappings.json
```

**Example: Add a new label**

```json
{
  "labels": [
    {
      "name": "Compliance",
      "values": ["SOX", "GDPR", "PII"]
    },
    {
      "name": "Risk Level",
      "values": ["Low", "Medium", "High", "Critical"]
    }
  ],
  "assignments": {
    "orn:okta:app:0oa123": ["Compliance:SOX", "Risk Level:High"],
    "orn:okta:group:00g456": ["Risk Level:Medium"]
  }
}
```

### Step 2: Create Pull Request

```bash
# Create feature branch
git checkout -b feature/add-risk-labels

# Commit changes
git add environments/myenv/config/label_mappings.json
git commit -m "feat: Add Risk Level labels for compliance tracking"

# Push to GitHub
git push -u origin feature/add-risk-labels

# Create PR
gh pr create \
  --title "Add Risk Level labels" \
  --body "Adding new Risk Level label with 4 values for compliance tracking"
```

### Step 3: Automatic Validation (Phase 1)

GitHub Actions automatically runs `validate-label-mappings.yml`:

**What it checks:**
- ✅ JSON syntax is valid
- ✅ ORNs are properly formatted (`orn:okta:type:id`)
- ✅ Label structure is correct
- ✅ No duplicate assignments

**Expected output in PR:**
```
✅ Validation passed!

Summary:
- Labels defined: 2
- Label values: 7
- Resource assignments: 2
- No errors found
```

### Step 4: Code Review

**Reviewer checks:**
- Labels make sense for the organization
- Assignments are appropriate
- No sensitive information in label names

**If validation failed:**
- Fix errors shown in PR comment
- Push new commit (validation re-runs automatically)

### Step 5: Merge Pull Request

Once approved:
```bash
# Merge via GitHub UI or CLI
gh pr merge --squash
```

### Step 6: Automatic Dry-Run (Phase 2 Preview)

After merge, `apply-labels-from-config.yml` runs automatically with `dry_run=true`:

**What it does:**
- ✅ Connects to Okta API (read-only)
- ✅ Shows what WOULD be created/updated
- ❌ **Does NOT** make changes yet

**Expected output:**
```
🔍 DRY RUN - No changes made

Would create:
- Label: "Risk Level" with values ["Low", "Medium", "High", "Critical"]

Would assign:
- orn:okta:app:0oa123 → ["Compliance:SOX", "Risk Level:High"]
- orn:okta:group:00g456 → ["Risk Level:Medium"]
```

### Step 7: Manual Apply (Phase 2 Execution)

**⚠️ This step changes your Okta org!**

```bash
# Via GitHub CLI
gh workflow run apply-labels-from-config.yml \
  -f environment=myenv \
  -f dry_run=false

# Or via GitHub UI:
# 1. Actions → Apply Labels from Config
# 2. Run workflow
# 3. Select environment: myenv
# 4. Set dry_run: false
# 5. Click "Run workflow"
```

**If environment protection is configured:**
- Approver receives notification
- Reviews dry-run output from Step 6
- Approves or rejects

**Workflow executes:**
```
✅ Labels applied successfully!

Created:
- Label: "Risk Level" (ID: lbc789)
  - Value: "Low" (ID: lbl101)
  - Value: "Medium" (ID: lbl102)
  - Value: "High" (ID: lbl103)
  - Value: "Critical" (ID: lbl104)

Assigned:
- orn:okta:app:0oa123: 2 labels
- orn:okta:group:00g456: 1 label
```

### Step 8: Verify in Okta Admin Console

1. Log into Okta Admin Console
2. Go to **Identity Governance → Labels**
3. Verify new labels appear
4. Navigate to labeled resources
5. Confirm labels are assigned

**✅ Complete!** Labels are now live in Okta.

---

## Understanding the Workflows

### validate-label-mappings.yml

**Trigger:** Pull request with `label_mappings.json` changes
**Secrets:** None (syntax validation only)
**Safety:** Safe - no Okta API calls

```yaml
# Runs on:
on:
  pull_request:
    paths:
      - 'environments/*/config/label_mappings.json'

# Does NOT use:
# environment: <none>  # No secrets needed!
```

**Purpose:** Fast feedback without requiring Okta access

### apply-labels-from-config.yml

**Trigger 1:** Automatic dry-run on merge to main
**Trigger 2:** Manual workflow dispatch

**Secrets:** Requires environment secrets
- `OKTA_API_TOKEN`
- `OKTA_ORG_NAME`
- `OKTA_BASE_URL`

**Safety:** Always dry-run first, manual apply required

```yaml
# Runs on:
on:
  push:
    branches: [main]  # Auto dry-run
  workflow_dispatch:  # Manual trigger
    inputs:
      dry_run:
        type: boolean
        default: true

environment: ${{ inputs.environment }}  # Uses environment secrets
```

**Safety Gates:**
1. Auto dry-run shows preview
2. Manual trigger required for apply
3. Environment protection can require approval
4. All changes logged in workflow output

---

## Common Scenarios

### Scenario 1: Adding a New Label

**Goal:** Add "Data Classification" label with values

**Steps:**
1. Edit `label_mappings.json`:
```json
{
  "labels": [
    {
      "name": "Data Classification",
      "values": ["Public", "Internal", "Confidential", "Restricted"]
    }
  ]
}
```
2. Create PR
3. Wait for validation ✅
4. Get approval and merge
5. Review auto dry-run output
6. Manually trigger apply with `dry_run=false`

**Time:** 15-20 minutes total

### Scenario 2: Assigning Labels to Resources

**Goal:** Label 5 apps as "SOX" compliant

**Steps:**
1. Get resource ORNs from Okta or terraform state
2. Edit `label_mappings.json`:
```json
{
  "assignments": {
    "orn:okta:app:0oa111": ["Compliance:SOX"],
    "orn:okta:app:0oa222": ["Compliance:SOX"],
    "orn:okta:app:0oa333": ["Compliance:SOX"],
    "orn:okta:app:0oa444": ["Compliance:SOX"],
    "orn:okta:app:0oa555": ["Compliance:SOX"]
  }
}
```
3. Follow standard workflow (PR → Validation → Merge → Dry-run → Apply)

**Time:** 10-15 minutes

### Scenario 3: Removing a Label Assignment

**Goal:** Remove "Crown Jewel" label from an app

**Steps:**
1. Edit `label_mappings.json` - remove from assignments
2. Create PR with title: "Remove Crown Jewel label from App X"
3. Standard workflow
4. Dry-run shows: "Would remove: orn:okta:app:0oa123 → Crown Jewel"
5. Apply

**Note:** Removing an assignment does NOT delete the label itself, just the assignment.

### Scenario 4: Bulk Label Assignment

**Goal:** Label all admin apps with "Privileged" and "High Risk"

**Steps:**
1. Get list of admin app ORNs:
```bash
cd environments/myenv/terraform
terraform state list | grep 'okta_app.*admin'
terraform state show okta_app_oauth.admin_app | grep orn
```
2. Bulk edit `label_mappings.json`
3. PR comment shows all changes
4. Dry-run previews bulk assignment
5. Apply

**Pro tip:** Use jq or Python to generate bulk assignments from state file.

---

## Troubleshooting

### PR Validation Failed

**Error:** `Invalid ORN format`
```
❌ Validation failed

Error in line 15:
  "orn:app:0oa123": ["Compliance:SOX"]
          ^^^^ Missing okta namespace

Should be: "orn:okta:app:0oa123"
```

**Fix:** Correct the ORN format, push new commit

### Dry-Run Shows Unexpected Changes

**Problem:** Dry-run wants to remove labels you didn't touch

**Cause:** Label exists in Okta but missing from `label_mappings.json`

**Solution:** Sync labels from Okta first:
```bash
python3 scripts/sync_label_mappings.py \
  --output environments/myenv/config/label_mappings.json
```

### Apply Failed: "Label Already Exists"

**Error:** `Label "Compliance" already exists in Okta`

**Cause:** Label was created outside of GitOps workflow

**Solution:**
1. Sync from Okta to get existing label IDs
2. Update `label_mappings.json` with existing label structure
3. Re-run workflow (will update, not recreate)

### Can't Find Resource ORN

**Problem:** Need ORN for a resource not in Terraform

**Solutions:**

**Option 1: From Okta Admin UI**
1. Navigate to resource
2. Check URL: `https://yourorg.okta.com/admin/app/{appId}/settings`
3. ORN is: `orn:okta:app:{appId}`

**Option 2: Via Terraform state**
```bash
terraform state show okta_app_oauth.myapp | grep orn
```

**Option 3: Via import script**
```bash
# Imports include ORNs in comments
cat environments/myenv/imports/entitlements.json | jq '.[] | .orn'
```

### Workflow Not Running

**Problem:** Made changes but no workflow triggered

**Checklist:**
- [ ] Did you change `label_mappings.json`? (Not other files)
- [ ] Is file in `environments/*/config/` directory?
- [ ] Did you push to GitHub?
- [ ] Check Actions tab for workflow status

### Environment Secrets Not Found

**Error:** `OKTA_API_TOKEN not found`

**Cause:** Environment not configured or name mismatch

**Fix:**
1. Go to Settings → Environments
2. Verify environment name matches workflow input
3. Check secrets exist: `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`
4. Re-run workflow

---

## Best Practices

### 1. Always Start with Sync

Before making changes, sync from Okta:
```bash
python3 scripts/sync_label_mappings.py \
  --output environments/myenv/config/label_mappings.json
```

This ensures you have the latest state.

### 2. Use Descriptive PR Titles

**Good:**
- "Add SOX compliance labels for financial apps"
- "Remove Crown Jewel label from App X per security review"

**Bad:**
- "Update labels"
- "Changes"

### 3. Review Dry-Run Before Apply

**Never skip the dry-run review!**
- Check all resources listed
- Verify assignments are correct
- Confirm no unexpected removals

### 4. Test in Staging First

If you have multiple environments:
1. Apply to staging/development first
2. Verify in Okta Admin Console
3. Then apply to production

### 5. Document Why in PR Description

```markdown
## Why

We need to label all financial applications with SOX compliance
for the upcoming audit.

## What

- Added "Compliance:SOX" label to 15 financial apps
- Added "Risk Level:High" to 3 critical apps
```

### 6. Keep label_mappings.json as Source of Truth

**DO:**
- ✅ Make all label changes via GitOps
- ✅ Sync regularly from Okta to detect drift
- ✅ Document manual changes in PR

**DON'T:**
- ❌ Create labels manually in Okta Admin UI
- ❌ Assign labels manually (unless emergency)
- ❌ Edit label_mappings.json directly on main branch

---

## Quick Reference

### Commands

```bash
# Sync labels from Okta
python3 scripts/sync_label_mappings.py \
  --output environments/myenv/config/label_mappings.json

# Validate locally
python3 scripts/validate_label_config.py \
  environments/myenv/config/label_mappings.json

# Dry-run via workflow
gh workflow run apply-labels-from-config.yml \
  -f environment=myenv \
  -f dry_run=true

# Apply via workflow
gh workflow run apply-labels-from-config.yml \
  -f environment=myenv \
  -f dry_run=false
```

### Workflow Files

| Workflow | Path | Purpose |
|----------|------|---------|
| Validation | `.github/workflows/validate-label-mappings.yml` | PR syntax check |
| Deployment | `.github/workflows/apply-labels-from-config.yml` | Apply to Okta |

### Configuration File

| Environment | Label Config Location |
|-------------|-----------------------|
| Production | `environments/myorg/config/label_mappings.json` |
| Staging | `environments/myorg/config/label_mappings.json` |
| Development | `environments/myorg/config/label_mappings.json` |

---

## Related Documentation

**For comprehensive label management details:**
→ [LABEL_MANAGEMENT.md](./LABEL_MANAGEMENT.md) - Complete API reference, examples, architecture

**For general GitOps workflow:**
→ [GITOPS_WORKFLOW.md](./GITOPS_WORKFLOW.md) - GitOps patterns and best practices

**For troubleshooting:**
→ [05-TROUBLESHOOTING.md](./05-TROUBLESHOOTING.md) - Common issues and solutions

**For security:**
→ [../SECURITY.md](../SECURITY.md) - Security best practices

---

## Summary

**Two-Phase Pattern:**
1. **Phase 1 (PR):** Syntax validation, no secrets, automatic
2. **Phase 2 (Deploy):** API calls, with secrets, manual trigger

**Why?**
- Security: PR validation can't access secrets
- Safety: Dry-run before apply
- Flexibility: Manual control over when changes apply

**Typical Flow:**
```
Edit JSON → PR → Validation → Merge → Auto Dry-Run → Manual Apply → Done!
     5min     2min    instant    5min      instant       5min
```

**Total Time:** 15-20 minutes from edit to live in Okta

**Key Takeaway:** Always review dry-run output before manual apply!
