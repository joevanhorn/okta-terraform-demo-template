# Rollback and Recovery Guide

**Quick Reference:** How to recover from mistakes and rollback changes safely.

This guide covers recovery procedures for common failure scenarios when managing Okta with Terraform.

---

## Table of Contents

1. [Quick Rollback Scenarios](#quick-rollback-scenarios)
2. [Detailed Recovery Procedures](#detailed-recovery-procedures)
3. [State File Recovery](#state-file-recovery)
4. [Prevention Best Practices](#prevention-best-practices)
5. [Recovery Checklist](#recovery-checklist)

---

## Quick Rollback Scenarios

### Scenario 1: Just Applied Bad Changes

**Problem:** Ran `terraform apply` with wrong configuration, changes are live in Okta

**Symptoms:**
- Resources created with wrong settings
- Users assigned to wrong groups
- Apps misconfigured

**Quick Rollback:**

```bash
# 1. Revert the git commit
git revert HEAD
git push origin main

# 2. Navigate to environment
cd environments/myenv/terraform

# 3. Review what will change back
terraform plan

# Expected: Shows reverting to previous configuration

# 4. Apply the revert
terraform apply

# 5. Verify in Okta Admin Console
```

**Time to recovery:** 5-10 minutes

**Success criteria:**
- Terraform plan shows resources back to previous state
- Okta Admin Console shows corrected configuration
- No unexpected side effects

---

### Scenario 2: Accidentally Deleted Resources

**Problem:** Ran `terraform destroy` or deleted critical resources

**Symptoms:**
- Users can't access apps
- Groups missing
- Entitlement bundles gone

**Recovery Steps:**

**Step 1: Stop further damage**
```bash
# Cancel any running workflows immediately
# Go to GitHub Actions → Cancel workflow
```

**Step 2: Assess damage**
```bash
cd environments/myenv/terraform

# Check what's missing
terraform plan

# Expected: Shows many resources "will be created"
```

**Step 3: Restore from git history**
```bash
# Find the last good commit
git log --oneline environments/myenv/terraform/

# Checkout the last good configuration
git checkout <last-good-commit> -- environments/myenv/terraform/

# Verify files restored
git diff
```

**Step 4: Apply to recreate resources**
```bash
terraform plan
# Review: Should show recreating deleted resources

terraform apply
# Confirm: yes
```

**Step 5: Verify in Okta**
- Check Okta Admin Console
- Verify users can access apps
- Test critical workflows

**Time to recovery:** 15-30 minutes

**Note:** Some resources may need manual reconfiguration (e.g., entitlement assignments, which Terraform doesn't manage).

---

### Scenario 3: State File Corrupted

**Problem:** Terraform state file corrupted or out of sync with Okta

**Symptoms:**
```bash
terraform plan
# Error: state file corrupted
# Error: resource not found in state
```

**Recovery via S3 Versioning:**

**Step 1: Check available versions**
```bash
# List state file versions
aws s3api list-object-versions \
  --bucket okta-terraform-demo \
  --prefix Okta-GitOps/myenv/terraform.tfstate

# Output shows version IDs and timestamps
```

**Step 2: Identify last working version**
```bash
# Look for version just before corruption
# Note the VersionId
```

**Step 3: Download previous version**
```bash
# Create backup directory
mkdir -p ~/terraform-recovery

# Download corrupted version (for reference)
aws s3 cp \
  s3://okta-terraform-demo/Okta-GitOps/myenv/terraform.tfstate \
  ~/terraform-recovery/corrupted.tfstate

# Download previous working version
aws s3api get-object \
  --bucket okta-terraform-demo \
  --key Okta-GitOps/myenv/terraform.tfstate \
  --version-id <PREVIOUS_VERSION_ID> \
  ~/terraform-recovery/previous.tfstate
```

**Step 4: Replace state file**
```bash
# Upload previous version as current
aws s3 cp \
  ~/terraform-recovery/previous.tfstate \
  s3://okta-terraform-demo/Okta-GitOps/myenv/terraform.tfstate
```

**Step 5: Verify recovery**
```bash
cd environments/myenv/terraform

# Re-initialize to refresh local cache
terraform init -reconfigure

# Test state
terraform state list

# Check if plan works
terraform plan

# Expected: Should complete without state errors
```

**Time to recovery:** 10-20 minutes

---

### Scenario 4: Wrong Environment Applied

**Problem:** Applied staging config to production (or vice versa)

**Symptoms:**
- Production has staging users/apps
- Resources in wrong Okta org
- Confusion about what's where

**Recovery Steps:**

**Step 1: STOP IMMEDIATELY**
- Don't apply more changes
- Cancel any running workflows

**Step 2: Identify what was applied wrong**
```bash
# Check GitHub Actions logs
gh run list --workflow=terraform-apply-with-approval.yml --limit 5

# View specific run
gh run view <run-id> --log
```

**Step 3: Destroy wrong resources**
```bash
# In the WRONG environment where staging was applied
cd environments/myorg/terraform

# List what doesn't belong
terraform state list

# Targeted destroy of staging resources
terraform destroy -target=okta_user.staging_user1
terraform destroy -target=okta_user.staging_user2
# ... repeat for all wrong resources
```

**Step 4: Verify environment secrets**
```bash
# Check repository secrets
gh secret list

# Check environment secrets
gh secret list -e Production
gh secret list -e Staging

# Ensure they point to correct Okta orgs
```

**Step 5: Apply correct config to correct environment**
```bash
# Apply production config to production
cd environments/myorg/terraform
terraform plan
terraform apply

# Apply staging config to staging
cd environments/myorg/terraform
terraform plan
terraform apply
```

**Time to recovery:** 30-60 minutes

**Prevention:** Always use environment-specific secrets (see [SECURITY.md](../SECURITY.md))

---

### Scenario 5: Workflow Failed Mid-Apply

**Problem:** GitHub Actions workflow crashed during `terraform apply`

**Symptoms:**
- Some resources created, others not
- State file may be locked
- Okta partially updated

**Recovery Steps:**

**Step 1: Check state lock**
```bash
cd environments/myenv/terraform

terraform plan
# If locked: Error: state locked
```

**Step 2: Force unlock (if stuck)**
```bash
# Only do this if you're SURE no other process is running
terraform force-unlock <LOCK_ID>

# Get LOCK_ID from error message
```

**Step 3: Assess partial completion**
```bash
# See what was created
terraform plan

# Shows:
# - Resources that were created (no change)
# - Resources that failed (will be created)
```

**Step 4: Complete the apply**
```bash
# Run apply to finish
terraform apply

# Or use targeted apply for specific resources
terraform apply -target=okta_group.failed_group
```

**Time to recovery:** 10-15 minutes

---

## Detailed Recovery Procedures

### Restoring Deleted Entitlement Bundles

**Challenge:** Terraform recreates bundle definition, but NOT assignments

**Recovery:**

1. **Restore bundle definition via Terraform**
```bash
git checkout <last-good-commit> -- environments/myenv/terraform/oig_entitlements.tf
terraform apply
```

2. **Manually restore assignments in Okta**
   - Check `environments/myenv/imports/entitlements.json` for previous assignments
   - Log into Okta Admin Console
   - Go to Identity Governance → Entitlement Bundles
   - For each bundle: Click Assign → Select users/groups

3. **Document the incident**
   - Note which bundles were affected
   - Record manual steps taken
   - Update procedures to prevent recurrence

**Time:** 30-60 minutes (depending on number of bundles)

---

### Recovering Resource Owners

**Challenge:** Resource owners are API-managed, not in Terraform state

**Recovery:**

1. **Check if owners were backed up**
```bash
# Look for previous owner mappings
git log -- environments/myenv/config/owner_mappings.json

# Checkout previous version
git show <commit>:environments/myenv/config/owner_mappings.json > /tmp/previous_owners.json
```

2. **Restore owners via script**
```bash
python3 scripts/apply_resource_owners.py \
  --config /tmp/previous_owners.json \
  --dry-run

# Review output, then apply
python3 scripts/apply_resource_owners.py \
  --config /tmp/previous_owners.json
```

3. **Verify in Okta**
   - Check resource owners in Identity Governance
   - Confirm owners match expected configuration

**Time:** 10-15 minutes

---

### Recovering Governance Labels

**Challenge:** Labels are API-managed with complex assignments

**Recovery:**

1. **Restore label configuration**
```bash
git checkout <last-good-commit> -- environments/myenv/config/label_mappings.json
```

2. **Apply via workflow (dry-run first)**
```bash
gh workflow run apply-labels-from-config.yml \
  -f environment=myenv \
  -f dry_run=true

# Review output in Actions tab
```

3. **Apply for real**
```bash
gh workflow run apply-labels-from-config.yml \
  -f environment=myenv \
  -f dry_run=false
```

4. **Verify in Okta**
   - Check labels exist: Identity Governance → Labels
   - Verify assignments on resources

**Time:** 15-20 minutes

---

## State File Recovery

### Understanding State Versions

S3 versioning keeps history of all state file changes:

```bash
# List all versions
aws s3api list-object-versions \
  --bucket okta-terraform-demo \
  --prefix Okta-GitOps/myenv/terraform.tfstate \
  --query 'Versions[*].[VersionId,LastModified,Size]' \
  --output table

# Output:
# VersionId              | LastModified           | Size
# ----------------------|------------------------|------
# abc123 (current)      | 2025-11-12T10:30:00Z  | 45678
# def456 (1 hour ago)   | 2025-11-12T09:30:00Z  | 45123
# ghi789 (1 day ago)    | 2025-11-11T10:30:00Z  | 44567
```

### Restoring Specific Version

```bash
# Download specific version
aws s3api get-object \
  --bucket okta-terraform-demo \
  --key Okta-GitOps/myenv/terraform.tfstate \
  --version-id def456 \
  recovered-state.tfstate

# Verify it's not corrupted
cat recovered-state.tfstate | jq '.version'

# Upload as current version
aws s3 cp \
  recovered-state.tfstate \
  s3://okta-terraform-demo/Okta-GitOps/myenv/terraform.tfstate

# Verify in terraform
cd environments/myenv/terraform
terraform init -reconfigure
terraform state list
```

### State Backup Best Practice

```bash
# Create manual backup before risky operations
mkdir -p ~/terraform-backups/$(date +%Y-%m-%d)

aws s3 cp \
  s3://okta-terraform-demo/Okta-GitOps/myenv/terraform.tfstate \
  ~/terraform-backups/$(date +%Y-%m-%d)/myenv-pre-change.tfstate

# Document what you're about to do
echo "About to apply major refactor" > \
  ~/terraform-backups/$(date +%Y-%m-%d)/myenv-notes.txt
```

---

## Prevention Best Practices

### 1. Always Use Plan First

```bash
# NEVER run apply without plan
terraform plan -out=tfplan

# Review plan file output carefully
terraform show tfplan

# If safe, apply
terraform apply tfplan
```

### 2. Use Targeted Applies for Risky Changes

```bash
# Instead of applying everything
terraform apply

# Apply specific resources
terraform apply -target=okta_group.new_group
terraform apply -target=okta_app_oauth.new_app
```

### 3. Test in Staging First

**Always follow environment promotion:**
```
Development → Staging → Production
```

- Test change in development
- Verify in staging (production-like)
- Apply to production with confidence

### 4. Enable Maximum Protection

**GitHub Environment Protection:**
```yaml
# Settings → Environments → Production
Required reviewers: 2
Wait timer: 10 minutes
Deployment branches: main only
```

**Branch Protection:**
```yaml
# Settings → Branches → main
Require pull request: ✅
Require approvals: 1+
Require status checks: ✅
Include administrators: ✅
```

### 5. Regular State Backups

```bash
# Weekly state backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=~/terraform-backups/$DATE

mkdir -p $BACKUP_DIR

for env in production staging development; do
  aws s3 cp \
    s3://okta-terraform-demo/Okta-GitOps/$env/terraform.tfstate \
    $BACKUP_DIR/$env.tfstate
done

# Compress and archive
tar czf ~/terraform-backups/backup-$DATE.tar.gz $BACKUP_DIR
```

### 6. Use Dry-Run Everywhere

**For workflows:**
```bash
# Always dry-run first
-f dry_run=true
```

**For scripts:**
```bash
python3 script.py --dry-run
```

**Never skip dry-run in production!**

### 7. Monitor Okta System Log

- Set up alerts for unexpected changes
- Review system log weekly
- Filter by Terraform API token actor
- Look for anomalies

---

## Recovery Checklist

Use this template when disaster strikes:

```markdown
## Incident Recovery Log

**Date/Time:** [YYYY-MM-DD HH:MM]
**Reporter:** [Your name]
**Environment:** [Production/Staging/Development]
**Incident Type:** [Describe what happened]

### Impact Assessment
- [ ] Resources affected: [List]
- [ ] Users impacted: [Number/which users]
- [ ] Services down: [Which apps/integrations]
- [ ] Data lost: [What data if any]

### Immediate Actions Taken
- [ ] Step 1: [What you did]
- [ ] Step 2: [What you did]
- [ ] Step 3: [What you did]

### Recovery Steps
- [ ] State file backup created
- [ ] Git history checked for last good config
- [ ] Rollback plan documented
- [ ] Approvals obtained (if needed)
- [ ] Rollback executed
- [ ] State file restored (if needed)

### Verification
- [ ] `terraform plan` shows no unexpected changes
- [ ] Resources verified in Okta Admin Console
- [ ] Users can access affected applications
- [ ] All critical workflows tested
- [ ] State file consistent

### Communication
- [ ] Team notified of incident
- [ ] Stakeholders informed
- [ ] Users notified (if needed)
- [ ] Status updates provided

### Prevention
- [ ] Root cause identified
- [ ] Documentation updated
- [ ] Validation added to prevent recurrence
- [ ] Process improved
- [ ] Team training completed (if needed)

### Timeline
- **Incident detected:** HH:MM
- **Recovery started:** HH:MM
- **Systems restored:** HH:MM
- **Verification complete:** HH:MM
- **Total downtime:** XX minutes

### Lessons Learned
[What went wrong, what went right, what to do differently]

### Follow-up Actions
- [ ] Post-mortem meeting scheduled
- [ ] Documentation PR created
- [ ] Process changes implemented
```

---

## Common Recovery Scenarios

### Scenario: Import Script Overwrote Manual Changes

**Problem:** Ran import workflow, lost manual Okta changes

**Recovery:**
1. Check git diff to see what changed
2. If valuable manual changes: Extract from Okta System Log
3. Cherry-pick important changes back into code
4. Re-apply with controlled merge

**Prevention:** Always commit before running import

---

### Scenario: Terraform Provider Upgrade Broke Everything

**Problem:** Upgraded Okta provider, plan shows destroying/recreating all resources

**Recovery:**
1. Don't apply! Downgra provider first
2. Edit `provider.tf`: Revert to previous version
3. Run `terraform init -upgrade=false`
4. Verify plan looks normal
5. Research provider upgrade path before trying again

**Prevention:** Test provider upgrades in staging first

---

### Scenario: Accidentally Committed Secrets

**Problem:** Committed API token or secrets to git

**Immediate Actions:**
1. **Revoke secret immediately** in Okta/AWS
2. Generate new secret
3. Update GitHub Environment secret
4. Remove from git history:

```bash
# Use BFG Repo-Cleaner
brew install bfg
bfg --replace-text secrets.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force-with-lease
```

**Time:** 15-30 minutes

---

## Recovery Time Estimates

| Scenario | Recovery Time | Complexity |
|----------|---------------|------------|
| Revert bad apply | 5-10 min | Low |
| Restore deleted resources | 15-30 min | Medium |
| State file recovery | 10-20 min | Medium |
| Wrong environment applied | 30-60 min | High |
| Workflow failed mid-apply | 10-15 min | Low |
| Entitlement bundle restoration | 30-60 min | High |
| Resource owners recovery | 10-15 min | Low |
| Labels recovery | 15-20 min | Medium |
| Provider upgrade rollback | 15-30 min | Medium |
| Secret exposure remediation | 15-30 min | High |

---

## Emergency Contacts

**When you need help:**

1. **Internal team:** [Your team Slack/contact info]
2. **Okta support:** [Your support contact]
3. **GitHub support:** For Actions/OIDC issues
4. **AWS support:** For state backend issues

**Escalation path:**
1. Attempt recovery using this guide (15-30 min)
2. Consult team (if no progress after 30 min)
3. Contact Okta support (if Okta API issues)
4. Engage emergency response (if production down >1 hour)

---

## Additional Resources

**Related Documentation:**
- [SECURITY.md](../SECURITY.md) - Security best practices and incident response
- [05-TROUBLESHOOTING.md](./05-TROUBLESHOOTING.md) - Common issues and solutions
- [AWS_BACKEND_SETUP.md](./AWS_BACKEND_SETUP.md) - State backend configuration
- [GITOPS_WORKFLOW.md](./GITOPS_WORKFLOW.md) - Standard workflows

**External Resources:**
- [Terraform State Recovery](https://www.terraform.io/docs/cli/commands/state/)
- [AWS S3 Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [Okta System Log](https://help.okta.com/en/prod/Content/Topics/Reports/Reports_SysLog.htm)
- [GitHub Actions Logs](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs)

---

## Summary

**Key Takeaways:**

1. **Plan before apply** - Always review changes
2. **Test in staging** - Never test in production
3. **Backup state files** - Automate weekly backups
4. **Git is your friend** - Commit often, revert easily
5. **S3 versioning saves lives** - State history is invaluable
6. **Dry-run everything** - Preview before executing
7. **Document incidents** - Learn from mistakes

**Most Common Recoveries:**
- Revert git commit + terraform apply (5-10 min)
- Restore state from S3 version (10-20 min)
- Recreate deleted resources from git (15-30 min)

**Remember:** Most disasters are recoverable. Stay calm, follow the checklists, and ask for help when needed.

**Questions?**
- Check [05-TROUBLESHOOTING.md](./05-TROUBLESHOOTING.md)
- Ask in team Slack/chat
- Create GitHub issue for documentation updates
