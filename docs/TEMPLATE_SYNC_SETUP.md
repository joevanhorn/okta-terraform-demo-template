# Template Sync Setup Guide

This guide explains how to set up automatic template synchronization for repositories created from this template.

## Overview

The template sync workflow (`.github/workflows/sync-template.yml`) automatically syncs updates from the template repository to your derived repository. It runs weekly and can also be triggered manually.

## Why You Need a Personal Access Token (PAT)

GitHub has security restrictions that prevent the default `GITHUB_TOKEN` from modifying workflow files (`.github/workflows/*`), even with the `workflows: write` permission declared. This is a security feature to prevent malicious code from modifying CI/CD pipelines.

**Without a PAT:** Template sync will fail when trying to sync workflow file changes with this error:
```
refusing to allow a GitHub App to create or update workflow without `workflows` permission
```

**With a PAT:** Template sync works for all files, including workflow updates.

## Setup Instructions

### Step 1: Create a Personal Access Token (Classic)

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click **"Developer settings"** (left sidebar)
3. Click **"Personal access tokens"** → **"Tokens (classic)"**
4. Click **"Generate new token"** → **"Generate new token (classic)"**
5. Configure the token:
   - **Note:** `Template Sync - [Your Repo Name]`
   - **Expiration:** Choose an appropriate expiration (90 days, 1 year, or no expiration)
   - **Scopes:** Select the following:
     - ✅ `repo` (Full control of private repositories)
       - This includes `repo:status`, `repo_deployment`, `public_repo`, and `repo:invite`
     - ✅ `workflow` (Update GitHub Actions workflows)
6. Click **"Generate token"**
7. **IMPORTANT:** Copy the token immediately (you won't be able to see it again)

### Step 2: Add Token as Repository Secret

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Configure the secret:
   - **Name:** `PERSONAL_ACCESS_TOKEN` (must be exactly this name)
   - **Secret:** Paste the token you copied in Step 1
5. Click **"Add secret"**

**Note:** GitHub restricts secret names containing "GITHUB" in them, which is why we use `PERSONAL_ACCESS_TOKEN` instead of names like `GITHUB_PAT`.

### Step 3: Verify Setup

You can verify the setup by manually triggering the sync workflow:

```bash
# Trigger the workflow manually
gh workflow run sync-template.yml

# Wait a moment, then check the run status
gh run list --workflow sync-template.yml --limit 1

# Watch the run in real-time
gh run watch
```

If the workflow completes successfully and creates a PR with workflow file changes, your setup is correct.

## What Happens During Sync

1. **Workflow triggers** (weekly schedule or manual)
2. **Fetches updates** from the template repository
3. **Creates a branch** with template updates
4. **Merges changes** (may have conflicts if you customized files)
5. **Creates a Pull Request** with all changes for review
6. **You review and merge** the PR to apply updates

## Workflow Behavior

### With PERSONAL_ACCESS_TOKEN configured:
- ✅ Syncs all files including workflow files
- ✅ Creates PRs with complete updates
- ✅ Fully automated

### Without PERSONAL_ACCESS_TOKEN configured:
- ✅ Syncs non-workflow files successfully
- ❌ Fails when workflow files have changes
- ⚠️ Partial automation

## Security Considerations

### Token Security
- **Store safely:** Never commit the PAT to your repository
- **Use secrets:** Always store as a GitHub repository secret
- **Limit scope:** Only grant `repo` and `workflow` scopes (don't grant admin permissions)
- **Set expiration:** Use token expiration to limit exposure window
- **Rotate regularly:** Replace tokens before they expire

### Token Permissions
The PAT has these capabilities:
- **Read and write** repository content
- **Create and update** workflow files
- **Create** pull requests
- **Cannot:** Delete the repository, change settings, or modify branch protection rules (unless you grant additional scopes)

### Least Privilege Alternative
If you're concerned about token permissions, you can:
1. **Not use the PAT** - Manually sync workflow file changes when needed
2. **Use fine-grained tokens** - GitHub's newer token type (beta) with more granular permissions
3. **Use a dedicated bot account** - Create a separate GitHub account for automation

## Troubleshooting

### Error: "refusing to allow a GitHub App to create or update workflow"
**Cause:** PERSONAL_ACCESS_TOKEN is not configured or is invalid.

**Solution:**
1. Verify the secret exists: Repository Settings → Secrets → Actions → Check for `PERSONAL_ACCESS_TOKEN`
2. Verify the secret name is exactly `PERSONAL_ACCESS_TOKEN` (case-sensitive)
3. Check token hasn't expired: GitHub Settings → Personal Access Tokens
4. Regenerate token if needed and update the secret

### Error: "authentication failed" or "401 Unauthorized"
**Cause:** PAT is invalid, expired, or has insufficient permissions.

**Solution:**
1. Go to GitHub Settings → Personal Access Tokens
2. Check if token is expired
3. Verify token has `repo` and `workflow` scopes
4. Generate a new token and update the repository secret

### Workflow runs but doesn't sync workflow files
**Cause:** Template doesn't have workflow file changes, or PAT isn't being used.

**Solution:**
1. Check if template actually has workflow file changes: Compare `.github/workflows/` between repos
2. Verify PAT is configured correctly
3. Check workflow run logs to see which token is being used

### PR has merge conflicts
**Cause:** You've customized files that also changed in the template.

**Solution:**
1. Check out the sync branch locally:
   ```bash
   git fetch origin
   git checkout sync-template-YYYYMMDD-HHMMSS
   ```
2. Resolve conflicts manually:
   ```bash
   git status  # See conflicted files
   # Edit files to resolve conflicts
   git add .
   git commit -m "Resolve merge conflicts"
   git push origin sync-template-YYYYMMDD-HHMMSS
   ```
3. Merge the PR

## Disabling Template Sync

If you want to stop syncing updates from the template:

1. **Delete the workflow file:**
   ```bash
   git rm .github/workflows/sync-template.yml
   git commit -m "chore: Disable template sync"
   git push
   ```

2. **Or disable the workflow in GitHub UI:**
   - Go to Actions → Sync Template Updates
   - Click "..." → "Disable workflow"

## Manual Sync Alternative

If you prefer not to use automated sync, you can manually sync updates:

```bash
# Add template as a remote
git remote add template https://github.com/joevanhorn/okta-terraform-demo-template.git

# Fetch template updates
git fetch template main

# Create a branch for merging
git checkout -b sync-template-manual

# Merge template changes
git merge template/main --allow-unrelated-histories

# Resolve any conflicts, then push
git push -u origin sync-template-manual

# Create PR via GitHub UI or gh CLI
gh pr create --title "Sync template updates" --body "Manual sync from template"
```

## Updating the Template URL

If the template repository moves or renames:

1. Edit `.github/workflows/sync-template.yml`
2. Update the template URL in the "Add template remote" step:
   ```yaml
   git remote add template https://github.com/NEW-ORG/NEW-REPO.git
   ```
3. Commit and push the change

## Additional Resources

- [GitHub Personal Access Tokens Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub Actions Permissions Documentation](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
- [About Workflow Permissions](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#permissions)

## Support

If you encounter issues not covered in this guide:
1. Check the [GitHub Actions logs](https://github.com/YOUR-ORG/YOUR-REPO/actions)
2. Review [closed issues](https://github.com/joevanhorn/okta-terraform-demo-template/issues?q=is%3Aissue+is%3Aclosed+label%3Atemplate-sync) in the template repository
3. [Open a new issue](https://github.com/joevanhorn/okta-terraform-demo-template/issues/new/choose) with:
   - Error message
   - Workflow run URL
   - Steps you've tried
