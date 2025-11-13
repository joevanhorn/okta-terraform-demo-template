# Prompt: OIG (Identity Governance) Setup

Use this prompt to generate OIG entitlement bundles and access review campaigns.

---

## Prerequisites

- Okta Identity Governance license required
- Understanding of OIG concepts (see: `testing/DETAILED_DEMO_BUILD_GUIDE.md` Level 5)

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
I need to set up Okta Identity Governance (OIG) features using Terraform.

ENVIRONMENT: myorg
FILES:
- environments/myorg/terraform/oig_entitlements.tf
- environments/myorg/terraform/oig_reviews.tf

ENTITLEMENT BUNDLES TO CREATE:
[List bundles with descriptions]
Example:
- Marketing Tools Bundle: Access to all marketing applications (Salesforce, HubSpot, LinkedIn)
- Engineering Tools Bundle: Access to development tools (GitHub, JIRA, AWS Console)
- Finance Tools Bundle: Access to financial systems (NetSuite, Expensify, Bill.com)

ACCESS REVIEW CAMPAIGNS TO CREATE:
[List review campaigns]
Example:
- Quarterly Access Review Q1 2025: Review all user access, manager-based review
- Annual Admin Review 2025: Review administrative access, CISO review
- Contractor Access Review: Monthly review of contractor permissions

OUTPUT REQUIREMENTS:
1. Generate okta_entitlement_bundle resources in oig_entitlements.tf
2. Generate okta_reviews resources in oig_reviews.tf
3. Use descriptive names and comments
4. Follow repository patterns exactly
5. Include realistic dates for review campaigns

IMPORTANT NOTES:
- Bundle definitions only (principal assignments managed in Okta UI)
- Resource owners managed separately via Python scripts
- Governance labels managed separately via Python scripts

Please generate the OIG Terraform configuration.
```

---

## Step 3: Post-Generation Steps

After generating OIG resources:

### 1. Apply Bundles
```bash
cd environments/myorg/terraform
terraform apply
```

### 2. Assign Apps to Bundles (Okta Admin Console)
```
1. Navigate to: Identity Governance → Entitlements
2. Find your bundle (e.g., "Marketing Tools Bundle")
3. Click "Edit"
4. Add applications to the bundle
5. Save
```

### 3. Assign Bundles to Users (Okta Admin Console)
```
1. Navigate to: Directory → People
2. Select a user
3. Go to "Entitlements" tab
4. Click "Assign Entitlements"
5. Select your bundle
6. Save
```

### 4. Set Resource Owners (Optional, API-Only)
```bash
# Sync current owners
python3 scripts/sync_owner_mappings.py \
  --output environments/myorg/config/owner_mappings.json

# Edit owner_mappings.json to set desired owners

# Apply owners
python3 scripts/apply_resource_owners.py \
  --config environments/myorg/config/owner_mappings.json
```

### 5. Apply Governance Labels (Optional, API-Only)
```bash
# Sync current labels
python3 scripts/sync_label_mappings.py \
  --output environments/myorg/config/label_mappings.json

# Edit label_mappings.json to set desired labels

# Apply labels
python3 scripts/apply_admin_labels.py \
  --config environments/myorg/config/label_mappings.json

# Or use workflow
gh workflow run apply-labels-from-config.yml \
  -f environment=myorg \
  -f dry_run=false
```

### 6. Configure Risk Rules (Optional, API-Only)
```bash
# Import existing risk rules to see format
python3 scripts/import_risk_rules.py \
  --output environments/myorg/config/risk_rules.json

# Edit risk_rules.json to add/modify SOD policies
# See prompts/manage_risk_rules.md for examples

# Apply risk rules
python3 scripts/apply_risk_rules.py \
  --config environments/myorg/config/risk_rules.json \
  --dry-run  # Remove for actual apply

# Or use workflow
gh workflow run apply-risk-rules.yml \
  -f environment=myorg \
  -f dry_run=false
```

---

## Example: Department-Based Bundles

**Prompt:**
```
Create OIG entitlement bundles for a company with three departments.

ENTITLEMENT BUNDLES:
- Marketing Access Bundle: All marketing team tools and applications
- Engineering Access Bundle: Development and infrastructure tools
- Sales Access Bundle: CRM and sales enablement tools

OUTPUT: Generate okta_entitlement_bundle resources.
```

**Generated Code:**
```hcl
# Marketing Access Bundle
resource "okta_entitlement_bundle" "marketing_access" {
  name        = "Marketing Access Bundle"
  description = "Complete access package for marketing team members including CRM, analytics, and content management tools"
}

# Engineering Access Bundle
resource "okta_entitlement_bundle" "engineering_access" {
  name        = "Engineering Access Bundle"
  description = "Development tools bundle including code repositories, CI/CD, cloud infrastructure, and monitoring tools"
}

# Sales Access Bundle
resource "okta_entitlement_bundle" "sales_access" {
  name        = "Sales Access Bundle"
  description = "Sales enablement bundle including CRM, proposal tools, and customer communication platforms"
}
```

---

## Example: Access Review Campaigns

**Prompt:**
```
Create quarterly access review campaigns for 2025.

ACCESS REVIEWS:
- Q1 2025: January 1-31, manager review of all user access
- Q2 2025: April 1-30, manager review of all user access
- Q3 2025: July 1-31, manager review of all user access
- Q4 2025: October 1-31, manager review of all user access

OUTPUT: Generate okta_reviews resources.
```

**Generated Code:**
```hcl
# Q1 2025 Quarterly Access Review
resource "okta_reviews" "q1_2025_access_review" {
  name        = "Quarterly Access Review - Q1 2025"
  description = "Quarterly review of all user access to applications and entitlements"

  start_date = "2025-01-01T00:00:00Z"
  end_date   = "2025-01-31T23:59:59Z"

  review_type   = "USER_ACCESS_REVIEW"
  reviewer_type = "MANAGER"
}

# Q2 2025 Quarterly Access Review
resource "okta_reviews" "q2_2025_access_review" {
  name        = "Quarterly Access Review - Q2 2025"
  description = "Quarterly review of all user access to applications and entitlements"

  start_date = "2025-04-01T00:00:00Z"
  end_date   = "2025-04-30T23:59:59Z"

  review_type   = "USER_ACCESS_REVIEW"
  reviewer_type = "MANAGER"
}

# Q3 2025 Quarterly Access Review
resource "okta_reviews" "q3_2025_access_review" {
  name        = "Quarterly Access Review - Q3 2025"
  description = "Quarterly review of all user access to applications and entitlements"

  start_date = "2025-07-01T00:00:00Z"
  end_date   = "2025-07-31T23:59:59Z"

  review_type   = "USER_ACCESS_REVIEW"
  reviewer_type = "MANAGER"
}

# Q4 2025 Quarterly Access Review
resource "okta_reviews" "q4_2025_access_review" {
  name        = "Quarterly Access Review - Q4 2025"
  description = "Quarterly review of all user access to applications and entitlements"

  start_date = "2025-10-01T00:00:00Z"
  end_date   = "2025-10-31T23:59:59Z"

  review_type   = "USER_ACCESS_REVIEW"
  reviewer_type = "MANAGER"
}
```

---

## Demo Value Proposition

When demoing OIG features:

**Traditional Approach:**
- "Here's how an admin manually reviews access for 100 users..."
- "This takes several hours per quarter..."
- "Easy to miss someone or forget to review"

**OIG Approach:**
- "We've defined access bundles that group related permissions"
- "Automated quarterly reviews notify managers automatically"
- "Managers can approve/revoke access in minutes, not hours"
- "Complete audit trail of all access decisions"
- "Compliance reports generated automatically"

---

## Troubleshooting

### Bundle not appearing in Okta UI
- Verify `terraform apply` succeeded
- Check Okta Identity Governance is enabled
- Refresh the Okta Admin Console page

### Cannot assign apps to bundle
- Ensure apps are already created
- Check app assignment settings
- Verify you have IGA admin permissions

### Review campaign not starting
- Verify dates are in the future (or current)
- Check reviewer_type is valid
- Ensure review_type matches your use case

---

## Related Documentation

- **📖 Documentation Index:** `../docs/00-INDEX.md` - Master guide to all documentation
- **OIG Overview:** `testing/DETAILED_DEMO_BUILD_GUIDE.md` (Level 5)
- **OIG Validation:** `testing/MANUAL_VALIDATION_PLAN.md` (Section 5)
- **Resource Guide:** `docs/TERRAFORM_RESOURCES.md` (OIG section)
- **API Management:** `docs/API_MANAGEMENT.md` - Owners, labels, risk rules
- **Risk Rules Prompt:** `prompts/manage_risk_rules.md` - SOD policies setup
- **Okta OIG Docs:** https://help.okta.com/oie/en-us/content/topics/identity-governance/iga-main.htm
