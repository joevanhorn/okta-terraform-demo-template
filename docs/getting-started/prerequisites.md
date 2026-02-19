# OIG (Okta Identity Governance) Prerequisites

If you plan to use the OIG features in the **`terraform/`** directory, you **must** complete these prerequisites before running Terraform.

---

## 🚨 Critical: Manual GUI Configuration Required

**Entitlement Management CANNOT be enabled via API or Terraform.** It must be manually enabled in the Okta Admin Console by a super administrator.

---

## Step-by-Step Setup

### Step 1: Verify OIG License

Before you begin, ensure your Okta organization has an active OIG license.

**Check License Status:**
1. Log into Okta Admin Console as super admin
2. Navigate to **Settings** → **Account**
3. Check **Subscription** section
4. Verify "Okta Identity Governance" is listed and active

**If you don't have OIG:**
- Contact your Okta account manager
- Request a trial or purchase OIG add-on
- Wait for license activation

---

### Step 2: Enable Entitlement Management (GUI Required)

**⚠️ This is the most critical step and MUST be done manually for each application.**

#### Location in Admin Console

**Path:** Applications → [Select Application] → General tab

**Important:** Entitlement Management is enabled **per application**, not globally.

#### Step-by-Step Instructions

1. **Log in** to your Okta Admin Console as a **super administrator**

2. **Navigate to the application:**
   - Click **Applications** → **Applications** in the left sidebar
   - Select the application you want to enable entitlements for
   - Click the **General** tab

3. **Disable Provisioning (Required First):**
   - ⚠️ **CRITICAL:** Provisioning **must be OFF** before enabling Entitlement Management
   - Navigate to the **Provisioning** tab
   - Disable **To App** provisioning if enabled
   - Click **Save**

4. **Enable Entitlement Management:**
   - Return to the **General** tab
   - Scroll to the "Entitlement Management" section
   - Toggle the switch to **ON**
   - Click **Save**

5. **Wait for Activation:**
   - Activation may take 1-2 minutes
   - Do not proceed until status shows "Enabled"
   - Refresh the page to check status

6. **Re-enable Provisioning (Optional):**
   - ✅ Once Entitlement Management is **fully online**, provisioning can be re-enabled
   - Navigate to the **Provisioning** tab
   - Re-enable **To App** provisioning if desired
   - Click **Save**

7. **Verify Enablement:**
   - General tab should show "Entitlement Management: Enabled"
   - You should now see entitlement options for this application

#### What This Enables

When you enable Entitlement Management, Okta activates:
- ✅ Entitlements API endpoints
- ✅ `okta_principal_entitlements` Terraform resource
- ✅ Entitlement catalog in Admin Console
- ✅ Entitlement-based access requests

#### Historical Note

This feature was formerly called the "Governance Engine" and may appear with that name in older documentation or UI versions.

---

### Step 3: Configure API Token Permissions

Your Okta API token must have the appropriate scopes for OIG operations.

#### Required Scopes

```
okta.users.manage
okta.groups.manage
okta.apps.manage
okta.governance.accessRequests.manage
okta.governance.accessReviews.manage
okta.governance.catalogs.manage
```

#### How to Create Token with Correct Scopes

1. Navigate to **Security** → **API** → **Tokens**
2. Click **Create Token**
3. Name it descriptively (e.g., "Terraform OIG Management")
4. Ensure all governance scopes are selected
5. **Copy the token immediately** - you won't see it again!
6. Store securely (password manager, vault, etc.)

---

### Step 4: Verify Setup

Before running Terraform, verify your setup is correct.

#### Test API Access

```bash
# Set environment variables
export OKTA_ORG_NAME="your-org-name"
export OKTA_BASE_URL="oktapreview.com"  # or okta.com
export OKTA_API_TOKEN="your-api-token"

# Test API access to entitlements endpoint
curl -X GET "https://${OKTA_ORG_NAME}.${OKTA_BASE_URL}/api/v1/governance/entitlements" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Accept: application/json"
```

**Expected Response:**
- ✅ HTTP 200 with JSON array (may be empty)
- ❌ HTTP 403 "Forbidden" → Check API token scopes
- ❌ HTTP 404 "Not Found" → Entitlement Management not enabled
- ❌ HTTP 401 "Unauthorized" → Check API token validity

---

## Common Errors and Solutions

### Error: "Feature not enabled"

**Error Message:**
```
Error: failed to create principal entitlements: The API returned an error:
Feature not enabled for organization
```

**Cause:** Entitlement Management is not enabled for the application

**Solution:**
1. Navigate to Applications → [Application] → General tab
2. **First**, disable provisioning in the Provisioning tab
3. Enable "Entitlement Management" in the General tab
4. Wait for activation to complete (1-2 minutes)
5. Optionally re-enable provisioning after activation
6. Retry Terraform operation

---

### Error: "Insufficient privileges"

**Error Message:**
```
Error: failed to create principal entitlements: The API returned an error:
Insufficient privileges to access this resource
```

**Cause:** API token lacks required governance scopes

**Solution:**
1. Create a new API token with all required scopes (see Step 3)
2. Update your `terraform.tfvars` with the new token
3. Retry Terraform operation

---

### Error: "Resource not found"

**Error Message:**
```
Error: error getting principal entitlements: Resource not found
```

**Possible Causes:**
1. Entitlement Management not enabled
2. Invalid principal ID (user or group doesn't exist)
3. OIG license not active

**Solution:**
1. Verify Entitlement Management is enabled
2. Check that referenced users/groups exist
3. Verify OIG license is active

---

### Error: "License required"

**Error Message:**
```
Error: The API returned an error:
This feature requires Okta Identity Governance license
```

**Cause:** Your Okta org doesn't have OIG license

**Solution:**
1. Contact Okta sales or your account manager
2. Request OIG trial or purchase
3. Wait for license activation
4. Retry after activation

---

## Verification Checklist

Before running `terraform apply` with OIG resources, verify:

- [ ] Okta org has active OIG license
- [ ] Logged in as super administrator
- [ ] For each application requiring entitlements:
  - [ ] Provisioning disabled before enabling Entitlement Management
  - [ ] Entitlement Management enabled in application's General tab
  - [ ] Waited 1-2 minutes for activation
  - [ ] Provisioning re-enabled (if needed) after activation
- [ ] API token created with all governance scopes
- [ ] API token has correct permissions (tested with curl)
- [ ] `terraform.tfvars` updated with correct credentials

---

## What Features Require These Prerequisites?

### Requires Entitlement Management Enabled

These resources/features **require** Entitlement Management:
- ✅ `okta_principal_entitlements`
- ✅ Entitlement-based access requests
- ✅ Entitlement catalog

### Does NOT Require Entitlement Management

These OIG resources work **without** Entitlement Management:
- ✅ `okta_reviews` (Access Reviews)
- ✅ `okta_request_settings` (Access Request settings)
- ✅ `okta_request_conditions` (Request conditions)
- ✅ `okta_request_sequences` (Approval workflows)
- ✅ `okta_catalog_entry_*` (Catalog configuration)

**Note:** All still require OIG license, just not the Entitlement Management feature specifically.

---

## Timeline Expectations

| Step | Time Required |
|------|---------------|
| Verify OIG license | 2 minutes |
| Enable Entitlement Management | 1-2 minutes activation |
| Create API token | 2 minutes |
| Test API access | 1 minute |
| **Total** | **~6-7 minutes** |

---

## Additional Resources

### Okta Documentation

- [Okta Identity Governance Overview](https://help.okta.com/oie/en-us/content/topics/identity-governance/iga-main.htm)
- [Entitlement Management](https://help.okta.com/oie/en-us/content/topics/identity-governance/iga-entitlements.htm)
- [OIG API Reference](https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Governance/)

### Terraform Provider

- [Okta Provider Documentation](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [okta_principal_entitlements Resource](https://registry.terraform.io/providers/okta/okta/latest/docs/resources/principal_entitlements)

---

## Still Having Issues?

If you've completed all prerequisites and still encounter errors:

1. **Check Okta Status Page**: https://status.okta.com/
2. **Review Terraform Debug Logs**:
   ```bash
   TF_LOG=DEBUG terraform apply
   ```
3. **Verify API Token**:
   - Token not expired
   - Token has correct scopes
   - Token belongs to super admin
4. **Contact Support**:
   - Okta Support Portal
   - Okta Developer Forums
   - GitHub Issues for this repo

---

## Quick Reference

### Enabling Entitlement Management (TL;DR)

1. Okta Admin Console
2. Applications → [Select Application] → General tab
3. **FIRST:** Disable provisioning (Provisioning tab)
4. Enable "Entitlement Management" (General tab)
5. Wait 1-2 minutes for activation
6. **OPTIONAL:** Re-enable provisioning after activation
7. Repeat for each application requiring entitlements

**Important Notes:**
- ⚠️ **Cannot be done via API** - GUI only!
- ⚠️ **Per-application setting** - not global
- ⚠️ **Provisioning must be OFF** during enablement

---

Last updated: 2025-11-04
