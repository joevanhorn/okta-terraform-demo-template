# Label Management Guide

Comprehensive guide for managing Okta Identity Governance labels using GitOps workflows.

## Table of Contents

- [Overview](#overview)
- [Label Structure](#label-structure)
- [Configuration File](#configuration-file)
- [Adding New Labels](#adding-new-labels)
- [Assigning Labels to Resources](#assigning-labels-to-resources)
- [GitOps Workflow](#gitops-workflow)
- [API Methods](#api-methods)
- [Scripts Reference](#scripts-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

This repository provides a complete GitOps-based label management system for Okta Identity Governance (OIG). Labels help categorize and organize resources like applications, groups, and entitlement bundles.

**Key Features:**
- **Hierarchical labels**: Support for labels with multiple values (e.g., Compliance: SOX, GDPR, PII)
- **GitOps workflow**: label_mappings.json as source of truth
- **Bi-directional sync**: Import from Okta OR apply to Okta
- **Dry-run mode**: Preview changes before applying
- **GitHub Actions integration**: Automated workflows with approval gates

**Okta Label Constraints:**
- Maximum 10 custom label keys per org
- Each key supports up to 10 values (max 100 total labels)
- Each resource can have up to 10 labels assigned
- Predefined labels: Crown Jewel, Privileged

---

## Label Structure

### Hierarchical Model

Labels use a hierarchical structure:

```
Label (key)
├── Label Value 1
├── Label Value 2
└── Label Value 3
```

**Example:**
```
Compliance                    ← Label (labelId: lbc...)
├── SOX                      ← Label Value (labelValueId: lbl...)
├── GDPR                     ← Label Value (labelValueId: lbl...)
└── PII                      ← Label Value (labelValueId: lbl...)
```

### Single-Value vs Multi-Value Labels

**Single-Value Labels:**
- Have one value that matches the label name
- Examples: "Privileged", "Crown Jewel"
- Typically used for predefined Okta labels
- Assignment format: `"Privileged"`

**Multi-Value Labels:**
- Have multiple distinct values under one label key
- Example: "Compliance" with values "SOX", "GDPR", "PII"
- Assignment format: `"Compliance:SOX"`, `"Compliance:GDPR"`

### Assignment Mechanism

**Critical Understanding:**

You assign **label VALUES** (not labels) to resources:

```python
# ✅ CORRECT: Assign the "SOX" value of the "Compliance" label
assign_label_values_to_resources(
    label_value_ids=["lbl..."],  # SOX's labelValueId
    resource_orns=["orn:okta:application:..."]
)

# ❌ WRONG: You cannot assign an entire label
# Labels are containers; you assign specific values within them
```

---

## Configuration File

### File Location

```
environments/{environment}/config/label_mappings.json
```

**Example:** `environments/myorg/config/label_mappings.json`

### File Structure

```json
{
  "description": "Label ID mappings synced from Okta OIG",
  "last_synced": "2025-11-10T22:21:53.307711Z",

  "labels": {
    "Compliance": {
      "labelId": "lbc...",
      "description": "Compliance framework label",
      "type": "multi_value",
      "values": {
        "SOX": {
          "labelValueId": "lbl...",
          "description": "Sarbanes-Oxley Act compliance",
          "color": "blue",
          "metadata": {"backgroundColor": "blue"}
        },
        "GDPR": {
          "labelValueId": "lbl...",
          "description": "GDPR compliance",
          "color": "blue",
          "metadata": {"backgroundColor": "blue"}
        }
      }
    }
  },

  "assignments": {
    "apps": {
      "Compliance:SOX": [
        "orn:okta:application:{orgId}:apps:{appId1}",
        "orn:okta:application:{orgId}:apps:{appId2}"
      ],
      "Compliance:GDPR": []
    },
    "groups": {},
    "entitlement_bundles": {},
    "other": {}
  }
}
```

### Field Definitions

**labels section:**
- `labelId`: Okta's unique identifier for the label key (auto-populated)
- `description`: Human-readable description
- `type`: `"single_value"` or `"multi_value"`
- `values`: Dictionary of label values
  - `labelValueId`: Okta's unique identifier for this value (auto-populated)
  - `description`: Description of this value
  - `color`: Display color (red, green, blue, orange, yellow, purple)
  - `metadata`: Additional properties

**assignments section:**
- Organized by resource type: `apps`, `groups`, `entitlement_bundles`, `other`
- Keys use format:
  - Single-value: `"Privileged"`
  - Multi-value: `"Compliance:SOX"`
- Values are arrays of ORNs (Okta Resource Names)

### ORN Formats

```
Apps:                orn:okta:application:{orgId}:apps:{appId}
Groups:              orn:okta:directory:{orgId}:groups:{groupId}
Entitlement Bundles: orn:okta:governance:{orgId}:entitlement-bundles:{bundleId}
```

---

## Adding New Labels

### Step 1: Edit label_mappings.json

Add the label definition to the `labels` section:

```json
{
  "labels": {
    "DataClassification": {
      "labelId": "",
      "description": "Data sensitivity classification",
      "type": "multi_value",
      "values": {
        "Public": {
          "labelValueId": "",
          "description": "Public data - no restrictions",
          "color": "green",
          "metadata": {"backgroundColor": "green"}
        },
        "Internal": {
          "labelValueId": "",
          "description": "Internal use only",
          "color": "yellow",
          "metadata": {"backgroundColor": "yellow"}
        },
        "Confidential": {
          "labelValueId": "",
          "description": "Confidential data - restricted access",
          "color": "red",
          "metadata": {"backgroundColor": "red"}
        }
      }
    }
  }
}
```

**Notes:**
- Leave `labelId` and `labelValueId` fields empty - they will be created automatically
- Choose appropriate colors for visual distinction
- Include clear descriptions

### Step 2: Initialize Assignments

Add empty arrays to the `assignments` section:

```json
{
  "assignments": {
    "apps": {
      "DataClassification:Public": [],
      "DataClassification:Internal": [],
      "DataClassification:Confidential": []
    },
    "groups": {
      "DataClassification:Public": [],
      "DataClassification:Internal": [],
      "DataClassification:Confidential": []
    },
    "entitlement_bundles": {},
    "other": {}
  }
}
```

### Step 3: Submit PR

1. Create feature branch
2. Commit changes to `label_mappings.json`
3. Submit pull request
4. PR will automatically trigger dry-run validation

---

## Assigning Labels to Resources

### Step 1: Get Resource ORNs

Find the ORN for the resource you want to label:

**From Okta Admin Console:**
- Navigate to the resource
- Copy the ID from the URL
- Construct ORN using format above

**From API:**
```bash
# List apps
curl -X GET "https://{org}.okta.com/api/v1/apps" \
  -H "Authorization: SSWS {token}"

# Construct ORN using correct format:
# orn:{partition}:idp:{orgId}:apps:{appName}:{appId}
#
# partition: oktapreview (for oktapreview.com), okta (for okta.com),
#            okta-emea (for okta-emea.com), trexcloud (for trexcloud.com)
# orgId: Numeric org ID from Admin URL (00omx5xxhePEbjFNp1d7)
# appName: Normalized app name (lowercase, spaces→underscores, special chars→underscores)
# appId: App ID from API (0oamxiwg4zsrWaeJF1d7)

# Example:
ORN="orn:oktapreview:idp:00omx5xxhePEbjFNp1d7:apps:salesforce:0oamxiwg4zsrWaeJF1d7"
```

### Step 2: Add to Assignments

Edit the `assignments` section:

```json
{
  "assignments": {
    "apps": {
      "Compliance:SOX": [
        "orn:oktapreview:idp:00omx5xxhePEbjFNp1d7:apps:salesforce:0oamxiwg4zsrWaeJF1d7",
        "orn:oktapreview:idp:00omx5xxhePEbjFNp1d7:apps:workday:0oaq4iodcifSLp30Q1d7",
        "orn:oktapreview:idp:00omx5xxhePEbjFNp1d7:apps:successfactors:0oan4ssz4lmqTnQry1d7",
        "orn:oktapreview:idp:00omx5xxhePEbjFNp1d7:apps:demo_myorg_salesday_1:0oamxc34dudXXjGJT1d7"
      ]
    },
    "groups": {
      "Compliance:PII": [
        "orn:oktapreview:idp:00omx5xxhePEbjFNp1d7:groups:00g..."
      ]
    }
  }
}
```

### Step 3: Submit PR

Follow same process as adding new labels.

---

## GitOps Workflow

### Overview

```
┌─────────────────┐
│ Developer       │
│ Edits Config    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create PR       │
│ (Feature Branch)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Automatic       │
│ Dry-Run (PR)    │◄──── Shows what would change
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Code Review &   │
│ Approval        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Merge PR        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Manual Workflow │
│ Trigger         │◄──── Run "Apply Labels from Config"
└────────┬────────┘      with dry_run=false
         │
         ▼
┌─────────────────┐
│ Labels Applied  │
│ to Okta         │
└─────────────────┘
```

### Workflow Details

**On Pull Request:**
- Workflow: `myorg-apply-labels-from-config.yml`
- Trigger: Automatic when `label_mappings.json` changes
- Mode: Always dry-run
- Output: PR comment with preview of changes

**After Merge:**
- Workflow: Manual trigger via GitHub Actions UI
- Input: `dry_run` (true/false)
- Approval: Required via GitHub Environment protection
- Output: Labels created and assigned in Okta

### Running Workflows

**Via GitHub Actions UI:**
```
1. Go to Actions tab
2. Select "MyOrg - Apply Labels from Config"
3. Click "Run workflow"
4. Select branch: main
5. Set dry_run: false
6. Approve when prompted
```

**Via GitHub CLI:**
```bash
# Dry run
gh workflow run apply-labels-from-config.yml \
  -f environment=myorg \
  -f dry_run=true

# Apply changes
gh workflow run apply-labels-from-config.yml \
  -f environment=myorg \
  -f dry_run=false
```

---

## API Methods

### OktaAPIManager Methods

Located in `scripts/okta_api_manager.py`

#### create_label_with_values()

Create a label with multiple values in a single API call.

```python
manager.create_label_with_values(
    name="Compliance",
    description="Compliance framework label",
    values=[
        {"name": "SOX", "description": "Sarbanes-Oxley"},
        {"name": "GDPR", "description": "GDPR compliance"},
        {"name": "PII", "description": "Personal data"}
    ]
)
```

**Returns:**
```json
{
  "labelId": "lbc...",
  "name": "Compliance",
  "values": [
    {"name": "SOX", "labelValueId": "lbl..."},
    {"name": "GDPR", "labelValueId": "lbl..."},
    {"name": "PII", "labelValueId": "lbl..."}
  ]
}
```

#### get_label_value_id()

Get labelValueId for a specific label value.

```python
value_id = manager.get_label_value_id(
    label_name="Compliance",
    value_name="SOX"
)
# Returns: "lbl11keklzHO41LJ11d7"
```

#### assign_label_values_to_resources()

Assign specific label values to resources.

```python
manager.assign_label_values_to_resources(
    label_value_ids=["lbl...", "lbl..."],  # SOX and GDPR
    resource_orns=[
        "orn:okta:application:00omx5...:apps:0oamxiw...",
        "orn:okta:application:00omx5...:apps:0oan4ss..."
    ]
)
```

**Important:** Use `labelValueIds`, NOT `labelIds`

---

## Scripts Reference

### apply_labels_from_config.py

Applies labels FROM config file TO Okta (deploy direction).

**Usage:**
```bash
# Dry run (preview)
python3 scripts/apply_labels_from_config.py \
  --config environments/myorg/config/label_mappings.json \
  --dry-run

# Apply changes
python3 scripts/apply_labels_from_config.py \
  --config environments/myorg/config/label_mappings.json
```

**What it does:**
1. Reads `label_mappings.json`
2. Creates labels (if they don't exist) with all values
3. Assigns label values to resources
4. Outputs results JSON for workflow consumption

**Outputs:**
- Console output with progress
- `label_application_results.json` - Results for workflow parsing

### sync_label_mappings.py

Syncs labels FROM Okta TO config file (import direction).

**Usage:**
```bash
python3 scripts/sync_label_mappings.py \
  --output environments/myorg/config/label_mappings.json
```

**What it does:**
1. Queries all labels from Okta
2. Queries all resource-label assignments
3. Builds hierarchical structure
4. Saves to `label_mappings.json`

**When to use:**
- After manual label changes in Okta Admin UI
- To refresh config file with latest state
- To detect drift between config and Okta

---

## Examples

### Example 1: Create Compliance Label with SOX Assignment

**1. Edit label_mappings.json:**

```json
{
  "labels": {
    "Compliance": {
      "labelId": "",
      "description": "Compliance framework label",
      "type": "multi_value",
      "values": {
        "SOX": {
          "labelValueId": "",
          "description": "Sarbanes-Oxley compliance",
          "color": "blue",
          "metadata": {"backgroundColor": "blue"}
        }
      }
    }
  },
  "assignments": {
    "apps": {
      "Compliance:SOX": [
        "orn:okta:application:00omx5xxhePEbjFNp1d7:apps:0oamxiwg4zsrWaeJF1d7"
      ]
    }
  }
}
```

**2. Submit PR:**
```bash
git checkout -b feature/add-compliance-label
git add environments/myorg/config/label_mappings.json
git commit -m "feat: Add Compliance label with SOX value"
git push -u origin feature/add-compliance-label
gh pr create --title "Add Compliance Label" --body "Adds SOX compliance label"
```

**3. Review dry-run output in PR comment**

**4. Merge PR**

**5. Apply to Okta:**
```bash
gh workflow run apply-labels-from-config.yml -f environment=myorg -f dry_run=false
```

### Example 2: Sync Labels from Okta

After making manual changes in Okta Admin UI:

```bash
# Set environment variables
export OKTA_ORG_NAME="myorg"
export OKTA_BASE_URL="oktapreview.com"
export OKTA_API_TOKEN="00xxx..."

# Run sync
python3 scripts/sync_label_mappings.py \
  --output environments/myorg/config/label_mappings.json

# Review changes
git diff environments/myorg/config/label_mappings.json

# Commit if desired
git add environments/myorg/config/label_mappings.json
git commit -m "chore: Sync labels from Okta"
```

### Example 3: Add PII Label to Group

**1. Find group ID:**
```bash
# Via Okta Admin Console URL
# https://myorg.oktapreview.com/admin/group/00g...
GROUP_ID="00g..."

# Construct ORN
ORG_ID="00omx5xxhePEbjFNp1d7"
ORN="orn:okta:directory:${ORG_ID}:groups:${GROUP_ID}"
```

**2. Edit label_mappings.json:**
```json
{
  "assignments": {
    "groups": {
      "Compliance:PII": [
        "orn:okta:directory:00omx5xxhePEbjFNp1d7:groups:00g..."
      ]
    }
  }
}
```

**3. Follow standard PR workflow**

---

## Troubleshooting

### Label Already Exists Error

**Error:**
```
❌ Error creating label: 409 - Label already exists
```

**Solution:**
The script handles this gracefully. If a label exists, it will:
1. Retrieve existing labelId and labelValueIds
2. Continue with assignments
3. Not create duplicate labels

### Label Value ID Not Found

**Error:**
```
⚠️ Label value ID not found for 'Compliance:SOX'
```

**Possible causes:**
1. Label not created yet - Run apply workflow first
2. Typo in assignment key - Check spelling matches label definition
3. Cache issue - Ensure label exists before assignments

**Solution:**
```bash
# Verify label exists
python3 scripts/apply_labels_from_config.py \
  --config config/label_mappings.json \
  --dry-run
```

### Assignment Format Errors

**Error:**
```
⚠️ Label value ID not found for 'SOX'
```

**Cause:** Using wrong assignment format

**Fix:**
```json
// ❌ WRONG - missing label name
"assignments": {
  "apps": {
    "SOX": [...]
  }
}

// ✅ CORRECT - use Label:Value format
"assignments": {
  "apps": {
    "Compliance:SOX": [...]
  }
}
```

### ORN Format Errors

**Error:**
```
❌ Invalid ORN format
```

**Common mistakes:**
```
❌ Wrong: "apps:0oamxiwg..."
✅ Right: "orn:okta:application:00omx5...:apps:0oamxiwg..."

❌ Wrong: Using app ID instead of ORN
✅ Right: Full ORN with org ID
```

### Maximum Labels Exceeded

**Error:**
```
❌ Maximum number of labels exceeded
```

**Okta limits:**
- Max 10 custom label keys
- Max 10 values per key
- Max 10 labels per resource

**Solution:**
1. Review existing labels
2. Consolidate similar labels under one key with multiple values
3. Archive unused labels

### Dry Run Shows No Changes

**Scenario:** Dry run completes but shows 0 changes

**Possible causes:**
1. Labels already exist (check `labels_skipped` in output)
2. Assignments already applied
3. Empty assignments arrays

**Verification:**
```bash
# Check current state in Okta
python3 scripts/sync_label_mappings.py \
  --output /tmp/current_labels.json

# Compare with your config
diff environments/myorg/config/label_mappings.json /tmp/current_labels.json
```

---

## Additional Resources

- [Okta Labels API Documentation](https://developer.okta.com/docs/guides/iga-labels/main/)
- [Okta Resource Labels Help](https://help.okta.com/oie/en-us/content/topics/identity-governance/resource-labels/resource-labels.htm)
- [Repository README](../README.md)
- [API Management Guide](./API_MANAGEMENT.md)
- [GitOps Workflow Guide](./GITOPS_WORKFLOW.md)

---

## Summary

This label management system provides:

✅ **Hierarchical labels** - Support for multi-value labels
✅ **GitOps workflow** - Config file as source of truth
✅ **Bi-directional sync** - Import OR apply
✅ **Automation** - GitHub Actions workflows
✅ **Safety** - Dry-run mode and approval gates
✅ **Flexibility** - Works with single and multi-value labels

Use this system to maintain consistent, auditable label management across your Okta Identity Governance environment.
