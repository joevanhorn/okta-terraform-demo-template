# Troubleshooting Guide

Quick solutions for common issues with Okta Terraform management.

---

## By Error Message

### Authentication Errors

#### "401 Unauthorized"

**Cause:** Invalid or expired Okta API token

**Solutions:**
1. Create a new token: Okta Admin Console → Security → API → Tokens
2. Update your configuration with the new token
3. Verify token has required scopes

#### "403 Forbidden"

**Cause:** API token lacks required permissions

**Solutions:**
1. Check token scopes in Okta Admin Console
2. For OIG features, need: `okta.governance.accessRequests.manage`, etc.
3. Create new token with all required scopes

#### "Invalid credentials"

**Cause:** Wrong org name or base URL

**Solutions:**
1. Verify org name from your Okta URL: `https://[THIS-PART].okta.com`
2. Check base URL: `okta.com`, `oktapreview.com`, or `okta-emea.com`
3. No `https://` prefix in base URL

---

### Resource Errors

#### "Resource already exists"

**Cause:** Resource exists in Okta but not in Terraform state

**Solutions:**
```bash
# Import the existing resource
terraform import okta_user.myuser "00u1234567890"
terraform import okta_group.mygroup "00g1234567890"
terraform import okta_app_oauth.myapp "0oa1234567890"
```

Find IDs in Okta Admin Console URLs.

#### "Resource not found"

**Cause:** Resource was deleted outside Terraform

**Solutions:**
```bash
# Remove from state
terraform state rm okta_user.deleted_user

# Or refresh state
terraform refresh
```

#### "Invalid value for 'login'"

**Cause:** Email/login already exists or invalid format

**Solutions:**
1. Check for duplicate emails in Okta
2. Ensure valid email format
3. Login must be unique across the entire Okta org

---

### Configuration Errors

#### "Error: Invalid provider configuration"

**Cause:** Missing or incorrect provider block

**Solution:** Verify `provider.tf`:
```hcl
provider "okta" {
  org_name  = "your-org-name"  # No https://
  base_url  = "okta.com"       # No trailing slash
  api_token = "your-token"
}
```

#### "Error: Invalid reference"

**Cause:** Referencing resource that doesn't exist

**Solutions:**
1. Check spelling of resource names
2. Ensure referenced resource is defined
3. Use `depends_on` if needed

#### "Provider produced inconsistent result"

**Cause:** Usually a timing issue with Okta API

**Solution:** Run `terraform apply` again. If persists, check Okta service status.

---

### Template/Syntax Errors

#### "Invalid template interpolation"

**Cause:** Using `${}` which Terraform interprets

**Solution:** Use `$${}` for Okta template strings:
```hcl
# Wrong
user_name_template = "${source.login}"

# Correct
user_name_template = "$${source.login}"
```

#### "Error: Invalid character"

**Cause:** Copy-paste introduced special characters

**Solution:** Retype the line or remove invisible characters.

---

### State Errors

#### "Error acquiring state lock"

**Cause:** Previous Terraform run didn't complete

**Solutions:**
```bash
# Wait a few minutes, then force unlock
terraform force-unlock LOCK-ID

# The LOCK-ID is shown in the error message
```

#### "State file not found"

**Cause:** Deleted or moved state file

**Solutions:**
1. Check if `terraform.tfstate` exists
2. If using S3 backend, verify bucket/key configuration
3. May need to re-import resources

---

## OIG-Specific Issues

### "Feature not enabled for organization"

**Cause:** Entitlement Management not enabled

**Solution:**
1. Go to Applications → [Your App] → General
2. Disable Provisioning first (Provisioning tab)
3. Enable "Entitlement Management"
4. Wait 1-2 minutes
5. Re-enable Provisioning if needed

See [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md)

### "Error reading campaign"

**Cause:** Entitlement bundle references deleted access review

**Solution:**
```bash
# Run fix workflow (if using GitOps)
gh workflow run fix-bundle-campaign-errors.yml \
  -f environment=myorg \
  -f dry_run=false

# Or manually clear the campaign_id in Okta Admin UI
```

### Labels API returns 405

**Cause:** Using label name instead of ID

**Solution:** Always use label ID, not name. Check your `label_mappings.json`.

### "Resource owner assignment failed"

**Cause:** Invalid user ID or user not admin

**Solutions:**
1. Verify user ID exists and is active
2. User must have admin role in Okta
3. Check JSON format in `owner_mappings.json`

---

## GitHub Actions Issues

### "Environment not found"

**Cause:** Environment name doesn't match exactly

**Solutions:**
1. Go to Settings → Environments
2. Note EXACT name (case-sensitive!)
3. Use exact same name in workflow input

### "Secret not found"

**Cause:** Secret name wrong or in wrong location

**Solutions:**
1. Secrets must be UPPERCASE: `OKTA_API_TOKEN`
2. Must be in Environment secrets, not Repository secrets
3. Check: Settings → Environments → [Name] → Secrets

### "Permission denied" on workflow

**Cause:** Workflow permissions not configured

**Solution:**
1. Settings → Actions → General
2. Set "Read and write permissions"
3. Enable "Allow Actions to create PRs"

### "OIDC token request failed"

**Cause:** AWS role trust policy issue

**Solutions:**
1. Verify `AWS_ROLE_ARN` secret is correct
2. Check role trust policy allows your repository
3. Repository name is case-sensitive in trust policy

---

## AWS Backend Issues

### "Access Denied" to S3

**Cause:** AWS credentials not configured

**Solutions (local):**
```bash
aws configure
# Or
aws sso login
```

**Solutions (GitHub Actions):**
1. Verify `AWS_ROLE_ARN` secret
2. Check OIDC provider in AWS IAM
3. Verify role trust policy

### "DynamoDB access denied"

**Cause:** IAM role lacks DynamoDB permissions

**Solution:** Check IAM role has `dynamodb:*` for the lock table.

### "State lock timeout"

**Cause:** Previous run crashed while holding lock

**Solution:**
```bash
terraform force-unlock LOCK-ID
```

---

## Quick Diagnostic Commands

### Check Terraform Setup

```bash
terraform version
terraform init
terraform validate
```

### Check AWS Access (if using S3 backend)

```bash
aws sts get-caller-identity
aws s3 ls s3://your-bucket/
```

### Check Okta API Access

```bash
curl -X GET "https://YOUR-ORG.okta.com/api/v1/users?limit=1" \
  -H "Authorization: SSWS YOUR-TOKEN"
```

### Check Terraform State

```bash
terraform state list
terraform state show okta_user.myuser
```

### Force Refresh

```bash
terraform refresh
terraform plan
```

---

## Prevention Tips

### Always Use Plan First
```bash
terraform plan   # Review changes
terraform apply  # Only if plan looks good
```

### Use Version Control
Keep your `.tf` files in Git. Easy to roll back.

### Keep Tokens Secure
- Never commit tokens to Git
- Use environment variables
- Rotate tokens every 90 days

### Test in Development First
Don't experiment in production Okta org.

### Check Okta Status
Before troubleshooting: [status.okta.com](https://status.okta.com)

---

## Getting More Help

### Documentation
- [TERRAFORM-BASICS.md](./TERRAFORM-BASICS.md) - Resource examples
- [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md) - OIG setup
- [docs/LESSONS_LEARNED.md](./docs/LESSONS_LEARNED.md) - Deep troubleshooting

### External Resources
- [Terraform Okta Provider](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Okta Developer Docs](https://developer.okta.com/)
- [Okta System Status](https://status.okta.com)

### Community
- [GitHub Issues](https://github.com/joevanhorn/okta-terraform-demo-template/issues)
- [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions)
