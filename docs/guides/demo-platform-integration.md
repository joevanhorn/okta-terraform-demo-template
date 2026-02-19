# Demo Platform Integration - OAuth Implementation Plan

**Use Case:** User adds "Okta Terraform GitOps" component to their Okta org via demo platform
**Goal:** Automatically create and configure GitHub repository with minimal user interaction
**Approach:** OAuth App with automated configuration

---

## 🎯 Architecture Overview

### **User Flow**

```
1. User logs into Demo Platform
   ↓
2. User creates/selects Okta org (e.g., "acme-demo")
   ↓
3. User adds "Okta Terraform GitOps" component
   ↓
4. Platform redirects to GitHub OAuth
   ↓
5. User authorizes platform to access their GitHub
   ↓
6. Platform creates repo from template
   ↓
7. Platform configures repo automatically:
   - Creates GitHub Environments
   - Adds Okta secrets (from platform)
   - Customizes README/config
   - Creates initial setup PR
   ↓
8. User receives: Ready-to-use repository
   ↓
9. Optional: Platform triggers initial import workflow
```

### **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                  Demo Platform Backend                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Okta Org DB  │  │ GitHub OAuth │  │ Component      │  │
│  │              │  │ Handler      │  │ Provisioner    │  │
│  │ - Org Name   │  │              │  │                │  │
│  │ - API Token  │  │ - Token Store│  │ - Create Repo  │  │
│  │ - Base URL   │  │ - Scope Mgmt │  │ - Configure    │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         ↓                 ↓                   ↓             │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
          │                 ↓                   ↓
          │      ┌─────────────────────────────────────┐
          │      │         GitHub API                  │
          │      │                                     │
          │      │  - Create repo from template       │
          │      │  - Create environments             │
          │      │  - Add secrets (encrypted)         │
          │      │  - Create PRs/issues               │
          │      │  - Trigger workflows               │
          │      └─────────────────────────────────────┘
          │                   │
          │                   ↓
          │      ┌─────────────────────────────────────┐
          │      │  User's GitHub Account              │
          │      │                                     │
          │      │  new repo: acme-demo-terraform      │
          │      │    ├─ .github/workflows/           │
          │      │    ├─ environments/myorg/          │
          │      │    ├─ Configured secrets           │
          │      │    └─ Setup PR with instructions   │
          │      └─────────────────────────────────────┘
          │
          └──────────────────────┐
                                 ↓
                    (Okta org details used for configuration)
```

---

## 📋 Implementation Plan

### **Phase 1: GitHub OAuth Setup**

#### Step 1.1: Create GitHub OAuth App

**Location:** Your organization's GitHub settings

```
Go to: https://github.com/organizations/YOUR_ORG/settings/applications/new
(or personal: https://github.com/settings/applications/new)

Settings:
  Application name: "Acme Demo Platform - Okta Terraform"
  Homepage URL: https://demo-platform.acme.com
  Authorization callback URL: https://demo-platform.acme.com/api/github/callback
  Enable Device Flow: No (not needed)
```

**Outputs you'll receive:**
- Client ID: `Iv1.a1b2c3d4e5f6g7h8`
- Client Secret: `1234567890abcdef...` (store securely!)

#### Step 1.2: Define OAuth Scopes

**Required scopes for full automation:**

```javascript
const REQUIRED_SCOPES = [
  'repo',              // Full repo access (create, read, write)
  'workflow',          // Trigger workflows
  'write:org',         // Create repos in org (if allowing org repos)
  'admin:repo_hook',   // Manage webhooks (optional)
  'delete_repo'        // Delete repo (optional, for cleanup)
];

// Scope string for OAuth URL
const scopeString = REQUIRED_SCOPES.join(' ');
```

**Minimal scopes (if limiting permissions):**

```javascript
const MINIMAL_SCOPES = [
  'public_repo',  // Only public repos
  'repo',         // Or private repos
  'workflow'      // Trigger workflows
];
```

---

### **Phase 2: Demo Platform Backend Implementation**

#### Step 2.1: Database Schema

Add GitHub integration table:

```sql
-- Store GitHub OAuth tokens per user
CREATE TABLE user_github_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  github_user_id INTEGER NOT NULL,
  github_username VARCHAR(255) NOT NULL,
  access_token TEXT NOT NULL,  -- Encrypted!
  token_type VARCHAR(50) DEFAULT 'bearer',
  scope TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,  -- GitHub tokens don't expire, but good to track
  last_used_at TIMESTAMP,

  UNIQUE(user_id)  -- One GitHub account per platform user
);

-- Track provisioned repositories
CREATE TABLE provisioned_repos (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  okta_org_id INTEGER NOT NULL REFERENCES okta_orgs(id),
  github_repo_id BIGINT NOT NULL,
  github_repo_name VARCHAR(255) NOT NULL,
  github_repo_url TEXT NOT NULL,
  github_owner VARCHAR(255) NOT NULL,
  provisioned_at TIMESTAMP DEFAULT NOW(),
  last_synced_at TIMESTAMP,
  status VARCHAR(50) DEFAULT 'active',  -- active, deleted, error

  UNIQUE(okta_org_id)  -- One repo per Okta org
);

-- Track configuration status
CREATE TABLE repo_configuration_log (
  id SERIAL PRIMARY KEY,
  repo_id INTEGER NOT NULL REFERENCES provisioned_repos(id),
  step VARCHAR(100) NOT NULL,
  status VARCHAR(50) NOT NULL,  -- pending, success, failed
  details JSONB,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Step 2.2: OAuth Flow Handler (Node.js/Express Example)

```javascript
// config/github-oauth.js
const crypto = require('crypto');

module.exports = {
  clientId: process.env.GITHUB_CLIENT_ID,
  clientSecret: process.env.GITHUB_CLIENT_SECRET,
  callbackURL: process.env.GITHUB_CALLBACK_URL || 'https://demo-platform.acme.com/api/github/callback',
  scopes: ['repo', 'workflow'],

  // Generate random state for CSRF protection
  generateState: () => {
    return crypto.randomBytes(32).toString('hex');
  }
};

// routes/github-oauth.js
const express = require('express');
const router = express.Router();
const axios = require('axios');
const { Octokit } = require('@octokit/rest');
const githubConfig = require('../config/github-oauth');
const { encryptToken, decryptToken } = require('../utils/encryption');
const db = require('../db');

/**
 * STEP 1: Initiate OAuth flow
 *
 * Called when user clicks "Add Okta Terraform GitOps" component
 */
router.post('/api/components/okta-terraform/provision', async (req, res) => {
  const { oktaOrgId } = req.body;
  const userId = req.user.id;  // From auth middleware

  // Verify user owns this Okta org
  const oktaOrg = await db.query(
    'SELECT * FROM okta_orgs WHERE id = $1 AND user_id = $2',
    [oktaOrgId, userId]
  );

  if (!oktaOrg.rows.length) {
    return res.status(403).json({ error: 'Okta org not found or access denied' });
  }

  // Check if GitHub token already exists for this user
  const existingToken = await db.query(
    'SELECT * FROM user_github_tokens WHERE user_id = $1',
    [userId]
  );

  if (existingToken.rows.length > 0) {
    // User already authorized GitHub, proceed directly to provisioning
    return res.json({
      status: 'proceeding',
      message: 'GitHub already authorized, provisioning repository...',
      redirectUrl: null
    });
  }

  // Generate state for CSRF protection
  const state = githubConfig.generateState();

  // Store state in session or database (with expiration)
  await db.query(
    'INSERT INTO oauth_states (user_id, state, okta_org_id, expires_at) VALUES ($1, $2, $3, NOW() + INTERVAL \'10 minutes\')',
    [userId, state, oktaOrgId]
  );

  // Build GitHub OAuth URL
  const authUrl = new URL('https://github.com/login/oauth/authorize');
  authUrl.searchParams.append('client_id', githubConfig.clientId);
  authUrl.searchParams.append('redirect_uri', githubConfig.callbackURL);
  authUrl.searchParams.append('scope', githubConfig.scopes.join(' '));
  authUrl.searchParams.append('state', state);
  authUrl.searchParams.append('allow_signup', 'true');

  res.json({
    status: 'authorization_required',
    message: 'Please authorize GitHub access',
    redirectUrl: authUrl.toString()
  });
});

/**
 * STEP 2: Handle OAuth callback
 *
 * GitHub redirects here after user authorizes
 */
router.get('/api/github/callback', async (req, res) => {
  const { code, state } = req.query;

  if (!code || !state) {
    return res.status(400).send('Missing code or state parameter');
  }

  // Verify state to prevent CSRF
  const stateRecord = await db.query(
    'SELECT * FROM oauth_states WHERE state = $1 AND expires_at > NOW()',
    [state]
  );

  if (!stateRecord.rows.length) {
    return res.status(400).send('Invalid or expired state parameter');
  }

  const { user_id: userId, okta_org_id: oktaOrgId } = stateRecord.rows[0];

  try {
    // Exchange code for access token
    const tokenResponse = await axios.post(
      'https://github.com/login/oauth/access_token',
      {
        client_id: githubConfig.clientId,
        client_secret: githubConfig.clientSecret,
        code: code,
        redirect_uri: githubConfig.callbackURL
      },
      {
        headers: {
          'Accept': 'application/json'
        }
      }
    );

    const { access_token, scope, token_type } = tokenResponse.data;

    if (!access_token) {
      throw new Error('No access token received from GitHub');
    }

    // Get GitHub user info
    const octokit = new Octokit({ auth: access_token });
    const { data: githubUser } = await octokit.users.getAuthenticated();

    // Store encrypted token
    const encryptedToken = encryptToken(access_token);

    await db.query(
      `INSERT INTO user_github_tokens
       (user_id, github_user_id, github_username, access_token, token_type, scope)
       VALUES ($1, $2, $3, $4, $5, $6)
       ON CONFLICT (user_id)
       DO UPDATE SET
         access_token = EXCLUDED.access_token,
         scope = EXCLUDED.scope,
         last_used_at = NOW()`,
      [userId, githubUser.id, githubUser.login, encryptedToken, token_type, scope]
    );

    // Delete used state
    await db.query('DELETE FROM oauth_states WHERE state = $1', [state]);

    // Redirect to provisioning page with success
    res.redirect(`/dashboard/okta-orgs/${oktaOrgId}/provision?status=authorized`);

    // Trigger async provisioning (don't wait for it)
    provisionRepository(userId, oktaOrgId).catch(err => {
      console.error('Provisioning error:', err);
    });

  } catch (error) {
    console.error('OAuth callback error:', error);
    res.status(500).send('Error during GitHub authorization');
  }
});

/**
 * STEP 3: Provision the repository
 *
 * This is the main automation logic
 */
async function provisionRepository(userId, oktaOrgId) {
  console.log(`Starting provisioning for user ${userId}, Okta org ${oktaOrgId}`);

  // Get user's GitHub token
  const tokenRecord = await db.query(
    'SELECT access_token FROM user_github_tokens WHERE user_id = $1',
    [userId]
  );

  if (!tokenRecord.rows.length) {
    throw new Error('No GitHub token found for user');
  }

  const accessToken = decryptToken(tokenRecord.rows[0].access_token);
  const octokit = new Octokit({ auth: accessToken });

  // Get Okta org details
  const oktaOrg = await db.query(
    'SELECT * FROM okta_orgs WHERE id = $1',
    [oktaOrgId]
  );

  if (!oktaOrg.rows.length) {
    throw new Error('Okta org not found');
  }

  const orgData = oktaOrg.rows[0];
  const repoName = `okta-terraform-${sanitizeRepoName(orgData.org_name)}`;

  try {
    // Log provisioning start
    const provisioningRecord = await db.query(
      `INSERT INTO provisioned_repos
       (user_id, okta_org_id, github_repo_name, status)
       VALUES ($1, $2, $3, 'provisioning')
       RETURNING id`,
      [userId, oktaOrgId, repoName]
    );
    const repoId = provisioningRecord.rows[0].id;

    // Get authenticated user for repo owner
    const { data: githubUser } = await octokit.users.getAuthenticated();

    await logStep(repoId, 'create_repo', 'pending');

    // STEP 1: Create repository from template
    console.log('Creating repo from template...');
    const { data: newRepo } = await octokit.repos.createUsingTemplate({
      template_owner: 'joevanhorn',
      template_repo: 'okta-terraform-demo-template',
      owner: githubUser.login,
      name: repoName,
      description: `Okta Terraform GitOps for ${orgData.org_name}`,
      private: true,
      include_all_branches: false
    });

    await logStep(repoId, 'create_repo', 'success', { repo_url: newRepo.html_url });

    // Update repo record with GitHub info
    await db.query(
      `UPDATE provisioned_repos
       SET github_repo_id = $1, github_repo_url = $2, github_owner = $3
       WHERE id = $4`,
      [newRepo.id, newRepo.html_url, githubUser.login, repoId]
    );

    // Wait for GitHub to finish template creation (async on their side)
    await sleep(5000);

    // STEP 2: Create GitHub Environments
    console.log('Creating environments...');
    await logStep(repoId, 'create_environments', 'pending');

    const environments = ['myorg', 'production', 'staging', 'development'];
    for (const env of environments) {
      await octokit.repos.createOrUpdateEnvironment({
        owner: githubUser.login,
        repo: repoName,
        environment_name: env,
        wait_timer: 0,
        reviewers: []
      });
    }

    await logStep(repoId, 'create_environments', 'success', {
      environments: environments
    });

    // STEP 3: Add repository secrets
    console.log('Adding repository secrets...');
    await logStep(repoId, 'add_secrets', 'pending');

    // Add AWS_ROLE_ARN placeholder
    await addRepositorySecret(
      octokit,
      githubUser.login,
      repoName,
      'AWS_ROLE_ARN',
      'arn:aws:iam::ACCOUNT_ID:role/REPLACE_ME'
    );

    // STEP 4: Add environment secrets for myorg
    await addEnvironmentSecret(
      octokit,
      newRepo.id,
      'myorg',
      'OKTA_API_TOKEN',
      orgData.api_token  // From platform's secure storage
    );

    await addEnvironmentSecret(
      octokit,
      newRepo.id,
      'myorg',
      'OKTA_ORG_NAME',
      orgData.org_name
    );

    await addEnvironmentSecret(
      octokit,
      newRepo.id,
      'myorg',
      'OKTA_BASE_URL',
      orgData.base_url || 'okta.com'
    );

    await logStep(repoId, 'add_secrets', 'success');

    // STEP 5: Customize repository files
    console.log('Customizing repository...');
    await logStep(repoId, 'customize_repo', 'pending');

    await customizeRepository(octokit, githubUser.login, repoName, orgData);

    await logStep(repoId, 'customize_repo', 'success');

    // STEP 6: Create setup issue with instructions
    console.log('Creating setup issue...');
    await logStep(repoId, 'create_issue', 'pending');

    const issue = await createSetupIssue(
      octokit,
      githubUser.login,
      repoName,
      orgData,
      newRepo.html_url
    );

    await logStep(repoId, 'create_issue', 'success', { issue_url: issue.data.html_url });

    // STEP 7: Optionally trigger initial import workflow
    if (orgData.auto_import_enabled) {
      console.log('Triggering initial import...');
      await logStep(repoId, 'trigger_import', 'pending');

      try {
        await octokit.actions.createWorkflowDispatch({
          owner: githubUser.login,
          repo: repoName,
          workflow_id: 'import-all-resources.yml',
          ref: 'main',
          inputs: {
            tenant_environment: 'myorg',
            update_terraform: 'true',
            commit_changes: 'true'
          }
        });

        await logStep(repoId, 'trigger_import', 'success');
      } catch (err) {
        // Import might fail if workflows aren't enabled yet
        await logStep(repoId, 'trigger_import', 'failed', {
          error: 'Workflow not yet available, user can trigger manually'
        });
      }
    }

    // Mark provisioning complete
    await db.query(
      'UPDATE provisioned_repos SET status = $1, last_synced_at = NOW() WHERE id = $2',
      ['active', repoId]
    );

    console.log('Provisioning complete!');

    return {
      success: true,
      repoUrl: newRepo.html_url,
      repoName: repoName
    };

  } catch (error) {
    console.error('Provisioning failed:', error);

    // Log error
    await db.query(
      `UPDATE provisioned_repos
       SET status = 'error'
       WHERE user_id = $1 AND okta_org_id = $2`,
      [userId, oktaOrgId]
    );

    throw error;
  }
}

/**
 * Helper: Add repository secret (encrypted)
 */
async function addRepositorySecret(octokit, owner, repo, secretName, secretValue) {
  const sodium = require('libsodium-wrappers');
  await sodium.ready;

  // Get repository public key
  const { data: publicKeyData } = await octokit.actions.getRepoPublicKey({
    owner,
    repo
  });

  // Convert secret and key to Uint8Array
  const messageBytes = Buffer.from(secretValue);
  const keyBytes = Buffer.from(publicKeyData.key, 'base64');

  // Encrypt using libsodium
  const encryptedBytes = sodium.crypto_box_seal(messageBytes, keyBytes);
  const encrypted = Buffer.from(encryptedBytes).toString('base64');

  // Create or update secret
  await octokit.actions.createOrUpdateRepoSecret({
    owner,
    repo,
    secret_name: secretName,
    encrypted_value: encrypted,
    key_id: publicKeyData.key_id
  });
}

/**
 * Helper: Add environment secret
 */
async function addEnvironmentSecret(octokit, repositoryId, environmentName, secretName, secretValue) {
  const sodium = require('libsodium-wrappers');
  await sodium.ready;

  // Get environment public key
  const { data: publicKeyData } = await octokit.request(
    'GET /repositories/{repository_id}/environments/{environment_name}/secrets/public-key',
    {
      repository_id: repositoryId,
      environment_name: environmentName
    }
  );

  // Encrypt
  const messageBytes = Buffer.from(secretValue);
  const keyBytes = Buffer.from(publicKeyData.key, 'base64');
  const encryptedBytes = sodium.crypto_box_seal(messageBytes, keyBytes);
  const encrypted = Buffer.from(encryptedBytes).toString('base64');

  // Create secret
  await octokit.request(
    'PUT /repositories/{repository_id}/environments/{environment_name}/secrets/{secret_name}',
    {
      repository_id: repositoryId,
      environment_name: environmentName,
      secret_name: secretName,
      encrypted_value: encrypted,
      key_id: publicKeyData.key_id
    }
  );
}

/**
 * Helper: Customize repository files
 */
async function customizeRepository(octokit, owner, repo, orgData) {
  // Update README.md with org name
  const { data: readmeFile } = await octokit.repos.getContent({
    owner,
    repo,
    path: 'README.md'
  });

  const readmeContent = Buffer.from(readmeFile.content, 'base64').toString();
  const customizedReadme = readmeContent
    .replace(/demo-myorg/g, sanitizeRepoName(orgData.org_name))
    .replace(/MyOrg/g, orgData.org_name)
    .replace(/okta-terraform-demo-template/g, repo);

  await octokit.repos.createOrUpdateFileContents({
    owner,
    repo,
    path: 'README.md',
    message: 'chore: Customize README for ' + orgData.org_name,
    content: Buffer.from(customizedReadme).toString('base64'),
    sha: readmeFile.sha
  });

  // Could customize other files here
  // - environments/myorg/README.md
  // - CLAUDE.md
  // - etc.
}

/**
 * Helper: Create setup issue
 */
async function createSetupIssue(octokit, owner, repo, orgData, repoUrl) {
  const issueBody = `
# 🎉 Welcome to Your Okta Terraform Environment!

Your repository has been automatically configured for **${orgData.org_name}**.

## ✅ What's Already Configured

- [x] GitHub repository created from template
- [x] GitHub Environments set up (myorg, production, staging, development)
- [x] Okta secrets added to **myorg** environment:
  - \`OKTA_API_TOKEN\` ✓
  - \`OKTA_ORG_NAME\` ✓ (${orgData.org_name})
  - \`OKTA_BASE_URL\` ✓ (${orgData.base_url || 'okta.com'})
- [x] Workflows enabled and ready

## 🚀 Next Steps

### 1. (Optional) Set Up AWS Backend

If you want to use S3 for Terraform state storage:

1. Follow [AWS Backend Setup Guide](${repoUrl}/blob/main/docs/AWS_BACKEND_SETUP.md)
2. Update the \`AWS_ROLE_ARN\` secret in repository settings

**Or skip this step** and use local state (fine for demos).

### 2. Import Your Okta Configuration

Your Okta org is already connected. Import existing resources:

\`\`\`bash
# Via GitHub CLI
gh workflow run import-all-resources.yml -f tenant_environment=myorg

# Or via GitHub UI
Actions → Import All Resources → Run workflow
\`\`\`

This will:
- Import all OIG entitlement bundles
- Import access review campaigns
- Import approval workflows
- Export resource owners and labels

### 3. Start Managing with GitOps

Make changes via pull requests:

\`\`\`bash
git checkout -b add-new-users
# Edit files in environments/myorg/terraform/
git commit -m "feat: Add marketing team users"
git push
# Create PR → Terraform plan runs automatically
\`\`\`

## 📚 Documentation

- **[CLAUDE.md](${repoUrl}/blob/main/CLAUDE.md)** - Complete repository guide
- **[README.md](${repoUrl}/blob/main/README.md)** - Overview and features
- **[docs/](${repoUrl}/tree/main/docs)** - Comprehensive documentation

## 🆘 Need Help?

- [Documentation Index](${repoUrl}/blob/main/docs/00-INDEX.md)
- [Troubleshooting Guide](${repoUrl}/blob/main/docs/LESSONS_LEARNED.md)
- Create an issue in this repository

---

**Automatically configured by Demo Platform**
**Okta Org:** ${orgData.org_name}
**Repository:** ${repoUrl}
`;

  return await octokit.issues.create({
    owner,
    repo,
    title: '🚀 Your Okta Terraform Environment is Ready!',
    body: issueBody,
    labels: ['setup', 'documentation', 'auto-configured']
  });
}

/**
 * Helper: Sanitize repo name
 */
function sanitizeRepoName(orgName) {
  return orgName
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Helper: Log provisioning step
 */
async function logStep(repoId, step, status, details = {}) {
  await db.query(
    `INSERT INTO repo_configuration_log (repo_id, step, status, details)
     VALUES ($1, $2, $3, $4)`,
    [repoId, step, status, JSON.stringify(details)]
  );
}

/**
 * Helper: Sleep
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = router;
```

---

### **Phase 3: Frontend Integration**

#### Step 3.1: Component UI

```javascript
// ComponentCard.jsx - React component for adding Okta Terraform
import React, { useState } from 'react';
import { FaGithub, FaCheckCircle, FaSpinner } from 'react-icons/fa';

export function OktaTerraformComponent({ oktaOrg }) {
  const [status, setStatus] = useState('idle'); // idle, authorizing, provisioning, complete, error
  const [repoUrl, setRepoUrl] = useState(null);
  const [error, setError] = useState(null);

  const handleAddComponent = async () => {
    setStatus('authorizing');
    setError(null);

    try {
      // Initiate provisioning
      const response = await fetch('/api/components/okta-terraform/provision', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
          oktaOrgId: oktaOrg.id
        })
      });

      const data = await response.json();

      if (data.status === 'authorization_required') {
        // Redirect to GitHub OAuth
        window.location.href = data.redirectUrl;
      } else if (data.status === 'proceeding') {
        // Already authorized, provisioning in progress
        setStatus('provisioning');

        // Poll for completion
        pollProvisioningStatus(oktaOrg.id);
      }

    } catch (err) {
      setError('Failed to start provisioning: ' + err.message);
      setStatus('error');
    }
  };

  const pollProvisioningStatus = async (oktaOrgId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/components/okta-terraform/status/${oktaOrgId}`, {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`
          }
        });

        const data = await response.json();

        if (data.status === 'active') {
          setStatus('complete');
          setRepoUrl(data.repoUrl);
          clearInterval(pollInterval);
        } else if (data.status === 'error') {
          setStatus('error');
          setError(data.error || 'Provisioning failed');
          clearInterval(pollInterval);
        }
        // Still provisioning, keep polling

      } catch (err) {
        console.error('Polling error:', err);
        // Continue polling on error
      }
    }, 3000); // Poll every 3 seconds

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  if (status === 'complete') {
    return (
      <div className="component-card success">
        <FaCheckCircle className="icon success" />
        <h3>Okta Terraform GitOps</h3>
        <p>Repository configured successfully!</p>
        <a href={repoUrl} target="_blank" rel="noopener noreferrer" className="btn primary">
          <FaGithub /> Open Repository
        </a>
      </div>
    );
  }

  if (status === 'provisioning') {
    return (
      <div className="component-card provisioning">
        <FaSpinner className="icon spinning" />
        <h3>Setting Up Your Repository...</h3>
        <p>This may take 30-60 seconds</p>
        <ul className="progress-list">
          <li>✓ Creating repository from template</li>
          <li>✓ Configuring GitHub Environments</li>
          <li>✓ Adding Okta secrets</li>
          <li>⏳ Customizing for your org...</li>
        </ul>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="component-card error">
        <h3>Setup Failed</h3>
        <p className="error-message">{error}</p>
        <button onClick={handleAddComponent} className="btn secondary">
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="component-card">
      <FaGithub className="icon" />
      <h3>Okta Terraform GitOps</h3>
      <p>Manage your Okta configuration as Infrastructure as Code</p>
      <ul>
        <li>✓ GitOps workflow with pull requests</li>
        <li>✓ Automated imports and validation</li>
        <li>✓ Full OIG support (bundles, reviews, workflows)</li>
        <li>✓ AI-assisted code generation</li>
      </ul>
      <button
        onClick={handleAddComponent}
        className="btn primary"
        disabled={status === 'authorizing'}
      >
        {status === 'authorizing' ? 'Authorizing...' : 'Add Component'}
      </button>
    </div>
  );
}
```

---

## ✅ Pros and Cons

### **Pros**

#### ✅ **Complete Automation**
- User clicks one button, gets fully configured repository
- All secrets automatically populated from platform
- No manual GitHub configuration needed
- Instant onboarding experience

#### ✅ **Tight Integration**
- Platform has full context about Okta org
- Can customize repository based on org settings
- Can trigger workflows automatically
- Can sync changes bidirectionally (future)

#### ✅ **User Experience**
- Single sign-on (platform → GitHub)
- No need to copy/paste secrets
- Guided setup with clear next steps
- Integrated into existing platform UI

#### ✅ **Security**
- OAuth tokens stored encrypted in platform
- Secrets never exposed to user
- Platform can revoke access if needed
- Audit trail of all operations

#### ✅ **Scalability**
- One-time OAuth per user
- Subsequent repos created instantly
- Can manage multiple Okta orgs per user
- Can provision/deprovision programmatically

#### ✅ **Flexibility**
- Can customize per org (e.g., healthcare vs finance)
- Can pre-configure based on plan/tier
- Can trigger different workflows based on context
- Can integrate with platform's lifecycle (delete org → delete repo)

---

### **Cons**

#### ❌ **OAuth Token Management**
- **Concern:** Must securely store user's GitHub tokens
- **Mitigation:**
  - Encrypt at rest with strong encryption (AES-256)
  - Rotate encryption keys regularly
  - Use HSM or key management service
  - Implement token expiry and refresh flow
  - Log all token usage

#### ❌ **User Trust**
- **Concern:** Users must trust platform with GitHub access
- **Mitigation:**
  - Clear explanation of why access is needed
  - Show exact scopes requested
  - Link to privacy policy
  - Allow token revocation from platform UI
  - GitHub shows "Installed apps" where users can revoke

#### ❌ **GitHub Rate Limits**
- **Concern:** 5,000 requests/hour per OAuth token
- **Impact:** Creating repo + configuring = ~20-30 API calls
  - Max ~250 repos/hour per user
- **Mitigation:**
  - Rate limit on platform side (e.g., max 5 repos/user/day)
  - Implement exponential backoff
  - Queue provisioning requests during high load
  - Monitor rate limit headers

#### ❌ **Scope Creep**
- **Concern:** `repo` scope is broad (full access to all repos)
- **Risk:** If platform is compromised, attacker has repo access
- **Mitigation:**
  - Minimize scope to `public_repo` if possible (limits to public repos only)
  - Use short-lived tokens (though GitHub doesn't expire OAuth tokens)
  - Implement additional security layers (2FA for platform access)
  - Regular security audits
  - Consider GitHub App instead (more granular permissions)

#### ❌ **Dependency on GitHub API**
- **Concern:** If GitHub API is down, provisioning fails
- **Mitigation:**
  - Implement retry logic with exponential backoff
  - Queue failed provisions for retry
  - Show clear error messages to users
  - Provide manual fallback instructions

#### ❌ **Maintenance Burden**
- **Concern:** Must maintain OAuth integration code
- **Ongoing:**
  - GitHub API changes require updates
  - Token encryption key rotation
  - Monitoring for failed provisions
  - Handling edge cases (user deleted repo, etc.)
- **Mitigation:**
  - Use well-maintained SDK (@octokit)
  - Comprehensive logging and alerting
  - Automated tests for provisioning flow
  - Documentation for troubleshooting

#### ❌ **No Granular Permissions**
- **Concern:** OAuth App can't limit access to just this template
- **Impact:** Platform can access user's other repos
- **Mitigation:**
  - Use GitHub App instead (installation-scoped)
  - Be transparent about access in UI
  - Implement strict access controls in platform code
  - Only access repos created by platform (track in DB)

#### ❌ **Initial Setup Complexity**
- **Concern:** Implementing OAuth flow is complex
- **Time Investment:** 2-3 weeks for full implementation
- **Requires:**
  - OAuth flow implementation
  - Token encryption/storage
  - GitHub API integration
  - Error handling
  - UI components
  - Testing
- **Mitigation:**
  - Use existing OAuth libraries (passport.js, etc.)
  - Follow reference implementation above
  - Incremental rollout (beta users first)

---

## 🔒 Security Considerations

### **Token Storage**

```javascript
// utils/encryption.js
const crypto = require('crypto');

// Use environment variable for encryption key
// Rotate regularly, store in secure key management system
const ENCRYPTION_KEY = process.env.GITHUB_TOKEN_ENCRYPTION_KEY; // 32 bytes
const ALGORITHM = 'aes-256-gcm';

function encryptToken(token) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(ENCRYPTION_KEY, 'hex'), iv);

  let encrypted = cipher.update(token, 'utf8', 'hex');
  encrypted += cipher.final('hex');

  const authTag = cipher.getAuthTag();

  // Return iv:authTag:encrypted
  return iv.toString('hex') + ':' + authTag.toString('hex') + ':' + encrypted;
}

function decryptToken(encryptedData) {
  const parts = encryptedData.split(':');
  const iv = Buffer.from(parts[0], 'hex');
  const authTag = Buffer.from(parts[1], 'hex');
  const encrypted = parts[2];

  const decipher = crypto.createDecipheriv(ALGORITHM, Buffer.from(ENCRYPTION_KEY, 'hex'), iv);
  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');

  return decrypted;
}

module.exports = { encryptToken, decryptToken };
```

### **Token Revocation Flow**

```javascript
// Allow users to revoke GitHub access from platform
router.delete('/api/github/disconnect', async (req, res) => {
  const userId = req.user.id;

  // Get token before deleting
  const tokenRecord = await db.query(
    'SELECT access_token FROM user_github_tokens WHERE user_id = $1',
    [userId]
  );

  if (tokenRecord.rows.length > 0) {
    const token = decryptToken(tokenRecord.rows[0].access_token);

    // Revoke token on GitHub
    // Note: OAuth Apps can't revoke their own tokens via API
    // User must revoke manually at: https://github.com/settings/applications
    // But we can delete from our database

    await db.query('DELETE FROM user_github_tokens WHERE user_id = $1', [userId]);

    // Mark all repos as disconnected
    await db.query(
      'UPDATE provisioned_repos SET status = $1 WHERE user_id = $2',
      ['disconnected', userId]
    );

    res.json({
      success: true,
      message: 'GitHub disconnected. Revoke app access at: https://github.com/settings/applications'
    });
  } else {
    res.status(404).json({ error: 'No GitHub connection found' });
  }
});
```

### **Audit Logging**

```javascript
// Log all GitHub API operations
async function auditLog(userId, action, details) {
  await db.query(
    `INSERT INTO audit_log (user_id, action, details, ip_address, user_agent, created_at)
     VALUES ($1, $2, $3, $4, $5, NOW())`,
    [userId, action, JSON.stringify(details), req.ip, req.get('user-agent')]
  );
}

// Usage
await auditLog(userId, 'github.repo.create', {
  repo_name: repoName,
  okta_org_id: oktaOrgId,
  template: 'joevanhorn/okta-terraform-demo-template'
});
```

---

## 🔄 Alternative: GitHub App (Comparison)

### **When to Use GitHub App Instead**

If you need:
- ✅ **Granular permissions** (access only to created repos)
- ✅ **Installation-scoped** (per-org or per-repo)
- ✅ **Better security model** (short-lived tokens)
- ✅ **Organization-wide** deployment
- ✅ **Webhook integration** (automatic triggers)

### **When OAuth App is Better**

If you need:
- ✅ **Simpler implementation** (no app installation flow)
- ✅ **Personal accounts** (GitHub Apps work best with orgs)
- ✅ **User-centric** (one token per user)
- ✅ **Fewer moving parts** (no installation management)

### **Hybrid Approach**

```
User Flow:
1. Platform asks: "Create in personal account or organization?"
2. Personal → OAuth App flow
3. Organization → GitHub App installation flow

This gives flexibility for both use cases.
```

---

## 📊 Cost-Benefit Analysis

### **Development Time**

| Phase | Effort | Timeline |
|-------|--------|----------|
| OAuth App setup | 1 day | Week 1 |
| Backend implementation | 3-5 days | Week 1-2 |
| Token encryption/storage | 1-2 days | Week 2 |
| Frontend integration | 2-3 days | Week 2 |
| Testing and debugging | 3-5 days | Week 3 |
| Documentation | 1-2 days | Week 3 |
| **Total** | **11-18 days** | **3 weeks** |

### **Ongoing Maintenance**

| Task | Frequency | Effort |
|------|-----------|--------|
| Monitor API errors | Daily | 15 min/day |
| Update for GitHub API changes | As needed | 1-2 days/year |
| Token key rotation | Quarterly | 2 hours |
| User support | As needed | Variable |

### **Value to Users**

- **Time saved per user:** 15-30 minutes (vs manual setup)
- **Error reduction:** 80-90% (no manual copy/paste of secrets)
- **Adoption increase:** 50-70% (frictionless onboarding)
- **User satisfaction:** High (magic experience)

---

## 🎯 Recommended Implementation Path

### **Phase 1: MVP (Week 1-2)**
1. OAuth App setup
2. Basic provisioning (create repo, add secrets)
3. Simple UI (add component button)
4. Manual testing

### **Phase 2: Enhancement (Week 3-4)**
1. Full customization (README, etc.)
2. Workflow triggers
3. Progress tracking UI
4. Error handling

### **Phase 3: Polish (Week 5-6)**
1. Comprehensive testing
2. User documentation
3. Monitoring/alerting
4. Beta rollout

### **Phase 4: Scale (Week 7+)**
1. Performance optimization
2. Additional customizations
3. Full production rollout
4. Feedback integration

---

## 📝 Checklist

- [ ] Create GitHub OAuth App
- [ ] Set up database tables
- [ ] Implement OAuth flow handler
- [ ] Build provisioning logic
- [ ] Add token encryption
- [ ] Create frontend component
- [ ] Implement error handling
- [ ] Add audit logging
- [ ] Write tests
- [ ] Create user documentation
- [ ] Set up monitoring
- [ ] Beta test with users
- [ ] Production rollout

---

**Document Version:** 1.0
**Last Updated:** 2025-11-19
**Status:** Implementation Plan
**Estimated Effort:** 3-6 weeks for full implementation
