# Prompt: Manage Risk Rules (SOD Policies)

Use this prompt to generate risk rules configuration for Separation of Duties (SOD) policies.

---

## Prerequisites

- Okta Identity Governance license required
- Understanding of SOD concepts and conflicting access patterns
- Entitlement bundles or apps already created

---

## Step 1: Provide Context

Paste these context files:

```
[Paste: ai-assisted/context/repository_structure.md]
[Paste: ai-assisted/context/terraform_examples.md]
[Paste: ai-assisted/context/okta_resource_guide.md]
```

---

## Step 2: Use This Prompt Template

```
I need to create risk rules (Separation of Duties policies) configuration for Okta Identity Governance.

ENVIRONMENT: myorg
FILE: environments/myorg/config/risk_rules.json

RISK RULES TO CREATE:
[List risk rules with descriptions]
Example:
- Change Management Conflict: Users who approve changes should not implement changes
- Financial Approval Conflict: Users who create purchase orders should not approve them
- Data Access Conflict: Users with read access should not have delete permissions

For each risk rule, specify:
1. Rule name and description
2. Resource (app, bundle, or collection ORN)
3. Conflicting entitlement sets (List 1 and List 2)
4. Operation type (CONTAINS_ALL or CONTAINS_ONE)

OUTPUT REQUIREMENTS:
1. Generate risk_rules.json configuration file
2. Use proper JSON format with description and metadata
3. Include realistic entitlement IDs (or placeholders if not available)
4. Follow repository patterns exactly
5. Include helpful notes for customization

IMPORTANT NOTES:
- Risk rules are managed via Python scripts, not Terraform
- Each rule can have ONE resource (app, bundle, or collection)
- Conflict criteria use AND logic between lists
- Entitlement values must be actual entitlement value IDs from Okta

Please generate the risk rules configuration.
```

---

## Step 3: Post-Generation Steps

After generating risk rules configuration:

### 1. Get Resource ORNs and Entitlement IDs

First, you need actual resource ORNs and entitlement IDs from your Okta tenant:

```bash
# Import existing risk rules to see format
python3 scripts/import_risk_rules.py \
  --output environments/myorg/config/risk_rules_current.json

# This shows you:
# - Actual resource ORNs from your tenant
# - Real entitlement set IDs
# - Proper entitlement value IDs
```

### 2. Update Configuration with Real Values

Edit `environments/myorg/config/risk_rules.json`:
- Replace placeholder ORNs with actual resource ORNs
- Replace entitlement set IDs with real IDs from your apps/bundles
- Replace entitlement value IDs with real values

### 3. Validate Configuration

```bash
# Dry-run to validate (doesn't make changes)
python3 scripts/apply_risk_rules.py \
  --config environments/myorg/config/risk_rules.json \
  --dry-run

# Review the plan output
```

### 4. Apply Risk Rules

```bash
# Apply the risk rules to Okta
python3 scripts/apply_risk_rules.py \
  --config environments/myorg/config/risk_rules.json

# Or use GitHub Actions workflow
gh workflow run apply-risk-rules.yml \
  -f environment=myorg \
  -f dry_run=false
```

### 5. Verify in Okta Admin Console

```
1. Navigate to: Identity Governance → Risk Rules
2. Verify your rules appear
3. Check rule details match your configuration
4. Test with sample users to verify violations are detected
```

---

## Example 1: Change Management SOD

**Scenario:** Prevent users who implement changes from also approving them in ServiceNow.

**Prompt:**
```
Create a risk rule for change management separation of duties.

RESOURCE: ServiceNow app (orn:okta:idp:00omx5xxhePEbjFNp1d7:apps:servicenow_ud:0oar0edy8iuBrRn6t1d7)

CONFLICT:
- List 1: Change Implementers (CONTAINS_ALL)
  - Entitlement: change_implementer role
- List 2: Change Approvers (CONTAINS_ONE)
  - Entitlement: change_approver role

A user having BOTH lists creates a conflict.

OUTPUT: Generate risk_rules.json entry.
```

**Generated Configuration:**
```json
{
  "description": "Risk rules (Separation of Duties policies) for Okta tenant",
  "last_synced": null,
  "version": "1.0",
  "rules": [
    {
      "name": "Change Management Conflict",
      "description": "Users who approve changes should not be the same as individuals who implement changes",
      "notes": "Prevents SOD violation in ServiceNow change management process",
      "type": "SEPARATION_OF_DUTIES",
      "resources": [
        {
          "resourceOrn": "orn:okta:idp:00omx5xxhePEbjFNp1d7:apps:servicenow_ud:0oar0edy8iuBrRn6t1d7"
        }
      ],
      "conflictCriteria": {
        "and": [
          {
            "name": "List 1 - Change Implementers",
            "operation": "CONTAINS_ALL",
            "value": {
              "type": "ENTITLEMENTS",
              "value": [
                {
                  "entitlementSetId": "ens12abcdefghijk1d7",
                  "entitlementValueId": "env12xyz1234567891d7"
                }
              ]
            }
          },
          {
            "name": "List 2 - Change Approvers",
            "operation": "CONTAINS_ONE",
            "value": {
              "type": "ENTITLEMENTS",
              "value": [
                {
                  "entitlementSetId": "ens12abcdefghijk1d7",
                  "entitlementValueId": "env12xyz9876543211d7"
                }
              ]
            }
          }
        ]
      }
    }
  ],
  "notes": [
    "HOW TO ADD A RISK RULE:",
    "1. Copy an example rule into the 'rules' array above",
    "2. Update the name, description, and resourceOrn for your app",
    "3. Update the entitlement set IDs and entitlement value IDs",
    "4. Use import_risk_rules.py to see actual IDs from your tenant",
    "5. Submit a PR with your changes",
    "6. Run: gh workflow run apply-risk-rules.yml -f environment=myorg -f dry_run=false"
  ]
}
```

---

## Example 2: Financial Controls

**Scenario:** Prevent users who create invoices from also approving payments.

**Prompt:**
```
Create a risk rule for financial controls.

RESOURCE: NetSuite app bundle

CONFLICT:
- List 1: Invoice Creators (CONTAINS_ALL)
  - Entitlement: create_invoice permission
  - Entitlement: submit_invoice permission
- List 2: Payment Approvers (CONTAINS_ONE)
  - Entitlement: approve_payment permission

OUTPUT: Generate risk_rules.json entry.
```

**Use Case:** Prevents fraud where single user can create and approve their own payments.

---

## Example 3: Data Access Controls

**Scenario:** Users with administrative database access should not also have production deployment rights.

**Prompt:**
```
Create a risk rule for database and deployment separation.

RESOURCE: Engineering Access Bundle

CONFLICT:
- List 1: Database Admins (CONTAINS_ONE)
  - Entitlement: db_admin role
  - Entitlement: db_superuser role
- List 2: Production Deployers (CONTAINS_ALL)
  - Entitlement: deploy_production permission

OUTPUT: Generate risk_rules.json entry.
```

**Use Case:** Reduces risk of data breaches by separating data access from deployment authority.

---

## Understanding Operations

### CONTAINS_ALL
User must have **ALL** listed entitlements in this set to match.

**Example:**
```json
{
  "operation": "CONTAINS_ALL",
  "value": {
    "type": "ENTITLEMENTS",
    "value": [
      {"entitlementSetId": "ens1", "entitlementValueId": "env1"},
      {"entitlementSetId": "ens2", "entitlementValueId": "env2"}
    ]
  }
}
```
**Result:** User must have BOTH env1 AND env2.

### CONTAINS_ONE
User must have **AT LEAST ONE** of the listed entitlements.

**Example:**
```json
{
  "operation": "CONTAINS_ONE",
  "value": {
    "type": "ENTITLEMENTS",
    "value": [
      {"entitlementSetId": "ens1", "entitlementValueId": "env1"},
      {"entitlementSetId": "ens2", "entitlementValueId": "env2"}
    ]
  }
}
```
**Result:** User has env1 OR env2 (or both).

### AND Logic
The `and` array means user must match ALL conditions to violate the rule.

**Example:**
```json
{
  "and": [
    {"name": "List 1", "operation": "CONTAINS_ALL", ...},
    {"name": "List 2", "operation": "CONTAINS_ONE", ...}
  ]
}
```
**Result:** Violation occurs when user matches List 1 AND List 2.

---

## Common SOD Patterns

### 1. Maker-Checker Pattern
**Concept:** Creator and approver must be different people.

**Examples:**
- Purchase Order Creator ≠ Purchase Order Approver
- Code Committer ≠ Code Reviewer
- Change Creator ≠ Change Approver

### 2. Segregation of Access
**Concept:** Administrative access and operational access separated.

**Examples:**
- Database Admin ≠ Application Developer
- Network Admin ≠ Security Auditor
- Financial Controller ≠ Accounts Payable Clerk

### 3. Audit Independence
**Concept:** People being audited can't be auditors.

**Examples:**
- Operations Staff ≠ Operations Auditor
- Developer ≠ Code Quality Auditor
- Financial Staff ≠ Financial Auditor

---

## Troubleshooting

### How do I find resource ORNs?

```bash
# Import existing risk rules to see ORN format
python3 scripts/import_risk_rules.py --output current_rules.json

# ORN format:
# orn:okta:{idp|directory}:{orgId}:apps:{appType}:{appId}
# orn:okta:directory:{orgId}:entitlementBundles:{bundleId}
```

### How do I find entitlement IDs?

1. **Via API:**
   ```bash
   # Get entitlements for an app
   curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
     "https://${OKTA_ORG_NAME}.${OKTA_BASE_URL}/api/v1/apps/${APP_ID}/entitlements"
   ```

2. **Via Import:**
   ```bash
   python3 scripts/import_risk_rules.py --output current.json
   # Review entitlement IDs in existing rules
   ```

### Rule not detecting violations

**Checks:**
1. ✅ Are entitlement IDs correct?
2. ✅ Is the resource ORN valid?
3. ✅ Do users actually have these entitlements assigned?
4. ✅ Is the rule status ACTIVE?
5. ✅ Are you using the correct operation (CONTAINS_ALL vs CONTAINS_ONE)?

### Dry-run shows unexpected changes

**This is normal if:**
- Okta returns rules in different order (use name matching)
- Metadata IDs differ (scripts match by name)
- Rule descriptions have minor differences

**Review carefully** - ensure it's not deleting rules you want to keep.

---

## Demo Value Proposition

When demoing risk rules (SOD policies):

**Without Risk Rules:**
- "Manual review of user access combinations is time-consuming"
- "Easy to miss conflicting permissions across systems"
- "Violations discovered during audits, not prevented"
- "Compliance gaps expose organization to risk"

**With Risk Rules:**
- "Automated detection of conflicting access patterns"
- "Proactive prevention of SOD violations"
- "Real-time alerts when conflicts are detected"
- "Continuous compliance monitoring"
- "Audit-ready reports showing no violations"

---

## Related Documentation

- **Documentation Index:** `docs/00-INDEX.md`
- **API Management Guide:** `docs/API_MANAGEMENT.md` (Risk Rules section)
- **OIG Setup:** `prompts/oig_setup.md`
- **Labels Workflow:** `docs/LABEL_WORKFLOW_GUIDE.md`
- **Risk Rules API:** Okta Developer Docs (Governance API)

---

## GitHub Workflows

### Import Risk Rules Workflow

```bash
# Import existing rules from Okta
gh workflow run import-risk-rules.yml \
  -f environment=myorg \
  -f commit_changes=true
```

### Apply Risk Rules Workflow

```bash
# Dry-run first (safe)
gh workflow run apply-risk-rules.yml \
  -f environment=myorg \
  -f dry_run=true

# Apply after reviewing dry-run
gh workflow run apply-risk-rules.yml \
  -f environment=myorg \
  -f dry_run=false
```

---

**Last Updated:** 2025-11-13
