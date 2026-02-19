# Troubleshooting Entitlement Bundles

## Issue: "Error reading campaign: 404 Not Found" During Terraform Plan

### Symptoms

When running `terraform plan` or `terraform apply`, you encounter errors like:

```
Error: Error reading campaign

  with okta_entitlement_bundle.purchasing,
  on oig_entitlements.tf line 20, in resource "okta_entitlement_bundle" "purchasing":
  20: resource "okta_entitlement_bundle" "purchasing" {

404 Not Found
```

### Root Cause

This error occurs when:

1. Entitlement bundles were previously included in an Okta access review campaign
2. That campaign was subsequently deleted in the Okta Admin Console
3. The Terraform provider tries to read the campaign association during state refresh
4. The provider gets a 404 error for the deleted campaign

**Important:** The bundles themselves still exist in Okta - only the campaign association is missing.

### Why This Happens

- Okta Identity Governance tracks relationships between bundles and campaigns
- When a campaign is deleted, these associations become "orphaned"
- The Terraform provider (v6.0.0 - v6.4.0) attempts to read campaign data during refresh
- The provider does not gracefully handle deleted campaign associations
- This is a **known limitation** of the Terraform provider's campaign/bundle integration

### Affected Provider Versions

- **Introduced:** v6.0.0 (September 2025) - First version with `okta_campaign` support
- **Current:** v6.4.0 (October 2025) - Still affected
- **Fixed:** Not yet fixed (as of November 2025)

### Pattern Recognition

Bundles that fail typically:
- Were created after other bundles in your tenant
- Were added to access review campaigns that no longer exist
- Have the same structure as working bundles (no campaign-related attributes)

In our case:
- ✅ **18 working bundles**: Created June 4, 2025 (before campaigns existed)
- ❌ **13 failing bundles**: Created June-November 2025 (added to campaigns)

## Solutions

### Option 1: Re-import Affected Bundles (Recommended)

This clears stale state and resolves the 404 errors.

#### Automated Script

```bash
# Use the provided script
./scripts/reimport_bundles_with_campaign_errors.sh myorg
```

#### Manual Steps

```bash
cd environments/myorg/terraform

# 1. Remove affected bundles from state
terraform state rm okta_entitlement_bundle.purchasing
terraform state rm okta_entitlement_bundle.datadog_read_only
# ... repeat for all affected bundles

# 2. Re-import them fresh
terraform import okta_entitlement_bundle.purchasing enb13o2ewjNG3y8LM1d7
terraform import okta_entitlement_bundle.datadog_read_only enb12zbvfgMan9Qak1d7
# ... repeat for all affected bundles

# 3. Verify
terraform plan
```

#### Expected Outcome

- Bundles remain in Okta (unchanged)
- Terraform state is refreshed without campaign associations
- `terraform plan` completes successfully

### Option 2: Use -refresh=false Flag (Temporary Workaround)

**⚠️ Not recommended for production - use only for testing**

```bash
terraform plan -refresh=false
terraform apply -refresh=false
```

**Limitations:**
- Skips drift detection (won't catch manual Okta changes)
- May cause state inconsistencies over time
- Not a long-term solution

### Option 3: Report Issue to Okta (Long-term Solution)

File a bug report: https://github.com/okta/terraform-provider-okta/issues/new

**Suggested issue content:**

```markdown
## Bug: okta_entitlement_bundle returns "Error reading campaign: 404" for bundles with deleted campaign associations

### Terraform Version & Provider Version
- Terraform: v1.9.0+
- Provider: okta/okta v6.4.0

### Affected Resource
- `okta_entitlement_bundle`

### Current Behavior
When running `terraform plan` or `terraform apply`, bundles that were previously included in access review campaigns (now deleted) fail during refresh with:

```
Error: Error reading campaign
404 Not Found
```

### Expected Behavior
The provider should:
1. Gracefully handle deleted campaign associations
2. Not fail refresh when campaigns no longer exist
3. Ideally, provide a way to opt-out of campaign association checks for bundles

### Steps to Reproduce
1. Create entitlement bundles in Okta
2. Add bundles to an access review campaign
3. Delete the campaign in Okta Admin Console
4. Run `terraform plan` against the bundle resources
5. Observe 404 errors during refresh phase

### Workaround
Remove and re-import affected bundles:
```bash
terraform state rm okta_entitlement_bundle.example
terraform import okta_entitlement_bundle.example <bundle_id>
```

### Additional Context
- Bundles themselves exist and are accessible via API
- The 404 only occurs for the campaign association
- Newer bundles are more likely to be affected (if created after campaigns were introduced)
- The error message "Error reading campaign" is misleading (bundle reads succeed, campaign association read fails)
```

## Prevention

### Best Practices

1. **Avoid deleting campaigns in Okta UI if bundles were included**
   - End campaigns instead of deleting them
   - Or, remove bundles from campaign scope before deletion

2. **Keep campaign management in Terraform**
   - Don't manage campaigns in Terraform (current recommendation)
   - OR, fully manage campaigns in Terraform (not recommended until provider is more stable)

3. **Monitor for new provider versions**
   - Check https://github.com/okta/terraform-provider-okta/releases
   - Look for fixes related to entitlement bundles and campaigns
   - Update provider when fixes are released

4. **Regular state refresh testing**
   ```bash
   # Test refresh without applying changes
   terraform plan -detailed-exitcode
   ```

### Workflow Integration

Add a check to your CI/CD workflow to detect this issue:

```yaml
- name: Detect Campaign Association Errors
  working-directory: environments/${{ env.ENVIRONMENT }}/terraform
  run: |
    if terraform plan 2>&1 | grep -q "Error reading campaign"; then
      echo "⚠️  Detected campaign association errors"
      echo "Run: ./scripts/reimport_bundles_with_campaign_errors.sh"
      exit 1
    fi
```

## Related Issues

- GitHub Issue #2527: [Unexpected behaviour with okta_campaign resource](https://github.com/okta/terraform-provider-okta/issues/2527)
  - Related to campaign resource limitations
  - Campaigns don't support updates properly
  - May share underlying provider bugs

- Provider PR #2485: Added entitlement bundle resource (September 2025)
- Provider PR #2424: Added campaign and entitlement resources (August 2025)

## Technical Details

### Why -refresh=false "Works"

The `-refresh=false` flag skips the state refresh phase where Terraform:
1. Reads current resource state from Okta API
2. Compares it to stored state
3. Detects drift

Without refresh, Terraform:
- Uses only the stored state file
- Doesn't make API calls to read resources
- Won't detect the campaign association issue
- But also won't detect ANY drift

### Why Re-import Works

Re-importing a bundle:
1. Makes a fresh API call to `/governance/api/v1/entitlement-bundles/{id}`
2. Gets current bundle data WITHOUT campaign associations
3. Stores clean state without stale campaign references
4. Future refreshes use the clean state

### Provider Code Location

The `okta_entitlement_bundle` resource code is in the official provider:
- Repository: https://github.com/okta/terraform-provider-okta
- Documentation: `/docs/resources/entitlement_bundle.md`
- Implementation: Likely in `/internal/framework/` (provider uses terraform-plugin-framework)

## FAQ

**Q: Will this delete my bundles in Okta?**
A: No. `terraform state rm` only removes from Terraform state. Bundles remain in Okta.

**Q: How do I know which bundles are affected?**
A: Run `terraform plan` - it will list all bundles that fail with "Error reading campaign"

**Q: Can I prevent this from happening again?**
A: Currently, no. Avoid using bundles in campaigns, or manage campaigns fully in Terraform.

**Q: Does this affect entitlement assignments?**
A: No. This only affects bundle definitions, not principal assignments.

**Q: Should I upgrade to a newer provider version?**
A: As of v6.4.0 (latest), this issue is not fixed. Check release notes for future fixes.

**Q: Is this a Terraform bug or an Okta API bug?**
A: Terraform provider bug. The Okta API works correctly; the provider should handle missing campaigns gracefully.

## Summary

**Short-term:** Use the re-import script to fix affected bundles
**Long-term:** Report the issue to Okta and wait for a provider fix
**Prevention:** Avoid deleting campaigns that include entitlement bundles

This is a known limitation of the current Terraform Okta provider's implementation of governance resources. The issue is expected to be resolved in future provider versions.
