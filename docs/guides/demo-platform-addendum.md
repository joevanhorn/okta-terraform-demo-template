# Demo Platform Integration - Implementation Plan Updates

**Based on:** Demo Engineering API Documentation (docs.demo.okta.com)
**Date:** 2025-11-19
**Status:** Revised Implementation Plan

---

## 🎉 Key Discovery: Component Hooks Architecture

After reviewing the Demo Engineering API Documentation, I discovered that the platform **already has a comprehensive webhook system** specifically designed for component integration. This significantly improves our implementation approach.

### **What Changed**

**Original Plan (OAuth App):**
- User authorizes GitHub access
- Platform creates repo on-demand
- Platform manages OAuth tokens

**New Recommended Plan (Component Hooks):**
- Register "Okta Terraform GitOps" as a Component
- Platform fires webhook when component added to demo
- Webhook handler provisions GitHub repo
- **Much cleaner integration with platform architecture**

---

## 📋 Updated Architecture

### **New Flow with Component Hooks**

```
1. One-Time Setup:
   └─ Register "Okta Terraform GitOps" Component
      └─ Define webhook endpoint URL
      └─ Configure component metadata

2. User Flow (Per Demo):
   User adds "Okta Terraform GitOps" to Demo
      ↓
   Platform fires "componentInstanceRequested" webhook
      ↓
   Webhook payload includes:
      - demo_id
      - user_id
      - component_id
      - okta_org_details (from demo)
      ↓
   Your webhook handler:
      ├─ Creates GitHub repo from template
      ├─ Configures environments & secrets
      ├─ Customizes for Okta org
      └─ Updates component instance state
      ↓
   User receives ready-to-use repo
```

### **Component Hooks API**

From the API documentation, these webhook events are available:

| Webhook Event | Description | Use Case |
|---------------|-------------|----------|
| **`componentInstanceRequested`** | Fired when demo with component is requested | **CREATE repo** |
| **`componentInstanceUpdated`** | Fired when component settings change | Update repo config |
| **`componentInstanceDeleted`** | Fired when component removed from demo | Archive/delete repo |
| **`applicationInstanceCreated`** | Fired when application instance created | Configure OIDC app |
| **`resourceInstanceRequested`** | Fired when resource instance requested | Provision resources |

**Most Important:** `componentInstanceRequested` - This is what triggers repo creation!

---

## 🆕 Updated Implementation Approach

### **Option 4: Component Hooks (NEW RECOMMENDED)**

#### **Pros vs OAuth App:**

| Factor | Component Hooks | OAuth App |
|--------|----------------|-----------|
| **User Experience** | ✅✅ Best - Zero user action | ✅ Good - One OAuth click |
| **Security** | ✅✅ Platform-controlled | ✅ User OAuth tokens |
| **Complexity** | ✅ Simpler - Just webhooks | ⚠️ OAuth flow + token management |
| **Platform Integration** | ✅✅ Native platform pattern | ⚠️ Custom integration |
| **Scalability** | ✅✅ Event-driven | ✅ Good |
| **Maintenance** | ✅✅ Minimal | ⚠️ Token management overhead |
| **GitHub Auth** | **Requires platform token** | User's personal token |
| **Control** | ✅✅ Platform has full control | ⚠️ Split between platform/user |

#### **Key Advantage:**

The Component Hooks approach is **native to the platform's architecture** and eliminates the need for individual user OAuth flows. The platform can use a **single GitHub account** (e.g., "demo-engineering-bot") to create repos on behalf of users.

---

## 🔧 Implementation Plan Update

### **Phase 1: Component Registration**

#### Step 1.1: Register Component with Demo Platform

**API Endpoint:** `POST /api/v1/components`

```json
{
  "name": "Okta Terraform GitOps",
  "description": "Manage Okta configuration as Infrastructure as Code with GitOps workflows",
  "category": "Infrastructure",
  "version": "1.0.0",
  "icon_url": "https://your-cdn.com/okta-terraform-icon.png",
  "documentation_url": "https://github.com/joevanhorn/okta-terraform-demo-template",
  "support_email": "demo-engineering@okta.com",

  "webhooks": {
    "component_instance_requested": {
      "url": "https://your-service.com/webhooks/component-requested",
      "method": "POST",
      "headers": {
        "X-Component-Secret": "shared-secret-value"
      }
    },
    "component_instance_updated": {
      "url": "https://your-service.com/webhooks/component-updated",
      "method": "POST"
    },
    "component_instance_deleted": {
      "url": "https://your-service.com/webhooks/component-deleted",
      "method": "POST"
    }
  },

  "configuration_schema": {
    "type": "object",
    "properties": {
      "repo_visibility": {
        "type": "string",
        "enum": ["private", "public"],
        "default": "private",
        "description": "GitHub repository visibility"
      },
      "enable_aws_backend": {
        "type": "boolean",
        "default": false,
        "description": "Configure S3 backend for Terraform state"
      },
      "auto_import": {
        "type": "boolean",
        "default": true,
        "description": "Automatically import Okta resources on creation"
      }
    }
  },

  "requirements": {
    "okta_org": true,
    "github_integration": true,
    "estimated_setup_time": "60 seconds"
  },

  "tags": ["terraform", "gitops", "infrastructure", "automation", "oig"]
}
```

#### Step 1.2: Configure GitHub Bot Account

**One-time setup:**

```bash
# Create GitHub bot account (or use org account)
# Username: demo-engineering-bot

# Generate Personal Access Token with scopes:
- repo (full control)
- workflow
- admin:org (if creating in org)

# Store token in platform's secure credential store
```

**Alternative:** Use GitHub App instead of PAT for better security and rate limits.

### **Phase 2: Webhook Handler Implementation**

#### Step 2.1: Webhook Endpoint (Node.js/Express)

```javascript
// webhooks/component-requested.js
const express = require('express');
const router = express.Router();
const { Octokit } = require('@octokit/rest');
const crypto = require('crypto');

// Verify webhook signature
function verifyWebhookSignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(JSON.stringify(payload));
  const calculated = hmac.digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(calculated)
  );
}

/**
 * Webhook: Component Instance Requested
 *
 * Fired when user adds "Okta Terraform GitOps" to their demo
 */
router.post('/webhooks/component-requested', async (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  const payload = req.body;

  // Verify signature
  if (!verifyWebhookSignature(payload, signature, process.env.COMPONENT_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Expected payload structure from Demo Platform
  const {
    demo_id,               // Unique demo identifier
    user_id,               // Platform user ID
    user_email,            // User's email
    component_id,          // Our component ID
    component_instance_id, // Unique instance ID
    configuration,         // User's selected config options
    okta_org: {
      id: okta_org_id,
      name: okta_org_name,
      base_url: okta_base_url,
      api_token: okta_api_token  // Platform provides this!
    }
  } = payload;

  console.log(`Provisioning Okta Terraform GitOps for demo ${demo_id}`);

  // Respond immediately to webhook (don't make platform wait)
  res.status(202).json({
    status: 'accepted',
    message: 'Provisioning started',
    component_instance_id
  });

  // Provision asynchronously
  provisionRepository({
    demo_id,
    user_id,
    user_email,
    component_instance_id,
    okta_org_id,
    okta_org_name,
    okta_base_url,
    okta_api_token,
    configuration
  }).catch(err => {
    console.error('Provisioning failed:', err);

    // Update component instance with error
    updateComponentInstanceState(component_instance_id, {
      state: 'error',
      error_message: err.message
    });
  });
});

/**
 * Provision GitHub repository
 */
async function provisionRepository(params) {
  const {
    demo_id,
    user_email,
    component_instance_id,
    okta_org_name,
    okta_base_url,
    okta_api_token,
    configuration
  } = params;

  // GitHub bot account token
  const githubToken = process.env.GITHUB_BOT_TOKEN;
  const octokit = new Octokit({ auth: githubToken });

  // Update state: provisioning
  await updateComponentInstanceState(component_instance_id, {
    state: 'provisioning',
    progress: 0,
    message: 'Creating GitHub repository...'
  });

  try {
    // Get bot user info
    const { data: botUser } = await octokit.users.getAuthenticated();

    // Create repo name
    const repoName = `okta-terraform-${sanitize(okta_org_name)}`;

    // STEP 1: Create repo from template
    await updateProgress(component_instance_id, 20, 'Creating repository from template...');

    const { data: newRepo } = await octokit.repos.createUsingTemplate({
      template_owner: 'joevanhorn',
      template_repo: 'okta-terraform-demo-template',
      owner: botUser.login,  // Bot account owns repo
      name: repoName,
      description: `Okta Terraform GitOps for ${okta_org_name} (Demo ${demo_id})`,
      private: configuration.repo_visibility === 'private',
      include_all_branches: false
    });

    // Wait for GitHub to finish template creation
    await sleep(5000);

    // STEP 2: Create environments
    await updateProgress(component_instance_id, 40, 'Creating GitHub Environments...');

    const environments = ['myorg', 'production', 'staging', 'development'];
    for (const env of environments) {
      await octokit.repos.createOrUpdateEnvironment({
        owner: botUser.login,
        repo: repoName,
        environment_name: env
      });
    }

    // STEP 3: Add secrets
    await updateProgress(component_instance_id, 60, 'Configuring Okta secrets...');

    // Add repository secrets
    await addRepoSecret(octokit, botUser.login, repoName, 'AWS_ROLE_ARN',
                       'arn:aws:iam::ACCOUNT:role/PLACEHOLDER');

    // Add environment secrets for myorg
    await addEnvironmentSecret(octokit, newRepo.id, 'myorg', 'OKTA_API_TOKEN', okta_api_token);
    await addEnvironmentSecret(octokit, newRepo.id, 'myorg', 'OKTA_ORG_NAME', okta_org_name);
    await addEnvironmentSecret(octokit, newRepo.id, 'myorg', 'OKTA_BASE_URL', okta_base_url);

    // STEP 4: Customize repository
    await updateProgress(component_instance_id, 80, 'Customizing repository...');

    await customizeReadme(octokit, botUser.login, repoName, okta_org_name, user_email);

    // STEP 5: Create setup issue
    await createSetupIssue(octokit, botUser.login, repoName, {
      okta_org_name,
      demo_id,
      user_email,
      repo_url: newRepo.html_url
    });

    // STEP 6: Optionally trigger import
    if (configuration.auto_import) {
      await updateProgress(component_instance_id, 90, 'Triggering initial import...');

      try {
        await octokit.actions.createWorkflowDispatch({
          owner: botUser.login,
          repo: repoName,
          workflow_id: 'import-all-resources.yml',
          ref: 'main',
          inputs: {
            tenant_environment: 'myorg',
            update_terraform: 'true',
            commit_changes: 'true'
          }
        });
      } catch (err) {
        // Non-fatal if workflow not ready yet
        console.warn('Could not trigger import workflow:', err.message);
      }
    }

    // STEP 7: Add collaborator (optional - invite user)
    if (user_email) {
      try {
        // Invite user as collaborator
        await octokit.repos.addCollaborator({
          owner: botUser.login,
          repo: repoName,
          username: user_email.split('@')[0], // Attempt username from email
          permission: 'admin'
        });
      } catch (err) {
        // Non-fatal if user doesn't have GitHub account
        console.warn('Could not add collaborator:', err.message);
      }
    }

    // Mark complete
    await updateComponentInstanceState(component_instance_id, {
      state: 'ready',
      progress: 100,
      message: 'Repository configured successfully',
      metadata: {
        repo_url: newRepo.html_url,
        repo_name: repoName,
        repo_id: newRepo.id,
        owner: botUser.login,
        created_at: new Date().toISOString()
      }
    });

    console.log(`✅ Provisioning complete: ${newRepo.html_url}`);

    return {
      success: true,
      repo_url: newRepo.html_url,
      repo_name: repoName
    };

  } catch (error) {
    console.error('Provisioning error:', error);

    await updateComponentInstanceState(component_instance_id, {
      state: 'error',
      progress: 0,
      error_message: error.message,
      error_details: error.stack
    });

    throw error;
  }
}

/**
 * Update component instance state in Demo Platform
 */
async function updateComponentInstanceState(instanceId, state) {
  const platformApiUrl = process.env.DEMO_PLATFORM_API_URL;
  const platformApiToken = process.env.DEMO_PLATFORM_API_TOKEN;

  await fetch(`${platformApiUrl}/api/v1/component-instances/${instanceId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${platformApiToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(state)
  });
}

/**
 * Update progress
 */
async function updateProgress(instanceId, progress, message) {
  await updateComponentInstanceState(instanceId, {
    state: 'provisioning',
    progress,
    message
  });
}

// Helper functions (same as before)
async function addRepoSecret(octokit, owner, repo, name, value) {
  const sodium = require('libsodium-wrappers');
  await sodium.ready;

  const { data: publicKey } = await octokit.actions.getRepoPublicKey({
    owner, repo
  });

  const messageBytes = Buffer.from(value);
  const keyBytes = Buffer.from(publicKey.key, 'base64');
  const encryptedBytes = sodium.crypto_box_seal(messageBytes, keyBytes);

  await octokit.actions.createOrUpdateRepoSecret({
    owner, repo,
    secret_name: name,
    encrypted_value: Buffer.from(encryptedBytes).toString('base64'),
    key_id: publicKey.key_id
  });
}

async function addEnvironmentSecret(octokit, repoId, envName, name, value) {
  // Same as before...
}

async function customizeReadme(octokit, owner, repo, orgName, userEmail) {
  // Same as before...
}

async function createSetupIssue(octokit, owner, repo, details) {
  // Same as before...
}

function sanitize(name) {
  return name.toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = router;
```

#### Step 2.2: Component Lifecycle Webhooks

```javascript
/**
 * Webhook: Component Instance Updated
 *
 * Fired when user changes component settings
 */
router.post('/webhooks/component-updated', async (req, res) => {
  const { component_instance_id, configuration, metadata } = req.body;

  res.status(202).json({ status: 'accepted' });

  // Update repo based on new configuration
  // e.g., change visibility, enable/disable features

  const { repo_name, owner } = metadata;

  // Example: Update repo visibility
  if (configuration.repo_visibility) {
    await octokit.repos.update({
      owner,
      repo: repo_name,
      private: configuration.repo_visibility === 'private'
    });
  }
});

/**
 * Webhook: Component Instance Deleted
 *
 * Fired when component removed from demo or demo deleted
 */
router.post('/webhooks/component-deleted', async (req, res) => {
  const { component_instance_id, metadata } = req.body;

  res.status(202).json({ status: 'accepted' });

  // Cleanup: Archive or delete the GitHub repo
  const { repo_name, owner } = metadata;

  // Option 1: Archive repo (recommended - preserves history)
  await octokit.repos.update({
    owner,
    repo: repo_name,
    archived: true
  });

  // Option 2: Delete repo (destructive)
  // await octokit.repos.delete({ owner, repo: repo_name });

  // Update platform
  await updateComponentInstanceState(component_instance_id, {
    state: 'deleted',
    message: 'Repository archived'
  });
});
```

---

## 📊 Comparison Matrix

### **Updated Decision Matrix**

| Factor | Component Hooks | OAuth App | GitHub App | Manual |
|--------|----------------|-----------|------------|--------|
| **User Experience** | ✅✅ Zero-click | ✅ One OAuth click | ✅ App install | ❌ Manual |
| **Implementation Time** | ✅✅ 1-2 weeks | ⚠️ 3-4 weeks | ⚠️ 4-6 weeks | ✅ 0 |
| **Maintenance** | ✅✅ Minimal | ⚠️ Token mgmt | ⚠️ App mgmt | ✅ None |
| **Platform Integration** | ✅✅ Native | ⚠️ Custom | ⚠️ Custom | ❌ None |
| **Security** | ✅✅ Platform-controlled | ✅ User tokens | ✅✅ Installation tokens | ✅ N/A |
| **Scalability** | ✅✅ Event-driven | ✅ Good | ✅✅ Best | ❌ Manual |
| **GitHub Auth** | ⚠️ Single bot account | ✅ User's account | ✅ Installation | ✅ User's |
| **Rate Limits** | ⚠️ Shared bot limits | ✅ Per-user limits | ✅✅ Per-installation | ✅ N/A |
| **Control** | ✅✅ Platform | ⚠️ Split | ✅ Platform | ❌ User |
| **Repo Ownership** | ⚠️ Bot account | ✅ User account | ✅ Org/User | ✅ User |
| **Cost** | ✅ Low | ✅ Low | ✅ Low | ✅ $0 |

**NEW RECOMMENDATION: Component Hooks** ⭐⭐⭐

---

## 🎯 Updated Implementation Timeline

### **Phase 1: Setup (Week 1)**
- [x] Review Demo Platform API documentation ✅
- [ ] Create GitHub bot account
- [ ] Generate GitHub PAT or App
- [ ] Register component with Demo Platform
- [ ] Test webhook delivery

### **Phase 2: Core Implementation (Week 2)**
- [ ] Build webhook handler
- [ ] Implement repo provisioning logic
- [ ] Add secret management
- [ ] Test end-to-end flow

### **Phase 3: Enhancement (Week 3)**
- [ ] Add progress tracking
- [ ] Implement lifecycle webhooks
- [ ] Add error handling & retry
- [ ] Create monitoring/alerting

### **Phase 4: Polish (Week 4)**
- [ ] User documentation
- [ ] Platform team training
- [ ] Beta testing with users
- [ ] Production rollout

**Total Time: 3-4 weeks** (vs 3-6 weeks for OAuth App)

---

## ⚠️ New Considerations with Component Hooks

### **Pros:**

1. ✅ **Simpler User Experience** - Zero user action required
2. ✅ **Native Platform Integration** - Uses platform's component architecture
3. ✅ **No OAuth Flow** - No user authorization needed
4. ✅ **Faster Implementation** - Fewer moving parts than OAuth
5. ✅ **Event-Driven** - Platform pushes events, no polling
6. ✅ **Platform Provides Okta Credentials** - No need to ask user

### **Cons:**

1. ⚠️ **Bot Account Rate Limits** - Shared GitHub bot account has 5,000 req/hr
   - **Mitigation:** Use GitHub App instead (better rate limits per installation)
   - **Mitigation:** Implement request queuing

2. ⚠️ **Repo Ownership** - Repos owned by bot, not user
   - **Impact:** User doesn't see repo in their personal account
   - **Mitigation:** Add user as collaborator with admin access
   - **Mitigation:** Transfer ownership to user (requires user to accept)
   - **Alternative:** Use GitHub App with user installation

3. ⚠️ **Bot Account Security** - Single point of failure
   - **Risk:** If bot token compromised, all repos at risk
   - **Mitigation:** Use GitHub App (more secure token model)
   - **Mitigation:** Rotate tokens regularly
   - **Mitigation:** Limit bot permissions
   - **Mitigation:** Audit log all bot activities

4. ⚠️ **No User GitHub Account Validation** - Can't verify user has GitHub
   - **Impact:** User might not have GitHub account
   - **Mitigation:** Document GitHub account requirement
   - **Mitigation:** Show clear instructions in platform UI

5. ⚠️ **Platform Dependency** - Relies on platform webhook reliability
   - **Risk:** If webhook fails, repo not created
   - **Mitigation:** Implement retry mechanism
   - **Mitigation:** Provide manual trigger option
   - **Mitigation:** Monitor webhook delivery

### **Hybrid Approach (Best of Both Worlds):**

```
Component Hooks + Optional OAuth:

1. Default: Bot creates repo, user added as collaborator
2. Optional: User can authorize OAuth to transfer ownership
3. Fallback: Manual repo creation instructions if all else fails

This gives flexibility for different user preferences.
```

---

## 🔄 Migration Path from OAuth App Plan

If you've already started implementing OAuth App approach, here's how to migrate:

### **Keep from OAuth App Plan:**
- ✅ GitHub API integration code (Octokit)
- ✅ Repo provisioning logic
- ✅ Secret encryption helpers
- ✅ Customization functions

### **Remove from OAuth App Plan:**
- ❌ OAuth flow handler
- ❌ Token storage/encryption
- ❌ User token database tables
- ❌ OAuth state management

### **Add for Component Hooks:**
- ✅ Component registration
- ✅ Webhook endpoints
- ✅ Webhook signature verification
- ✅ Component state updates

**Time to Migrate: 2-3 days**

---

## 📝 Action Items

### **Immediate (This Week):**
1. [ ] Get Demo Platform API credentials
2. [ ] Create GitHub bot account or App
3. [ ] Set up webhook handler endpoint
4. [ ] Register component with platform
5. [ ] Test webhook delivery

### **Short-Term (Next 2 Weeks):**
6. [ ] Implement provisioning logic
7. [ ] Add progress tracking
8. [ ] Test with real demos
9. [ ] Documentation

### **Long-Term (Month 2):**
10. [ ] Monitor usage and errors
11. [ ] Optimize provisioning speed
12. [ ] Add advanced features
13. [ ] Scale to production

---

## 🎯 Recommendation

**Switch to Component Hooks approach** for these reasons:

1. ✅ **Faster to implement** (3-4 weeks vs 5-6 weeks)
2. ✅ **Better user experience** (zero-click vs one-click OAuth)
3. ✅ **Simpler architecture** (webhooks vs OAuth + tokens)
4. ✅ **Native platform integration** (designed for this pattern)
5. ✅ **Lower maintenance burden** (no token rotation, simpler security)

**Only stick with OAuth App if:**
- Need repos in user's personal account (not bot's)
- Want per-user rate limits instead of shared
- Platform doesn't support component webhooks reliably
- Security policy forbids shared bot accounts

---

**Document Version:** 2.0
**Last Updated:** 2025-11-19
**Status:** Revised Recommendation - Component Hooks Preferred
**Related:** DEMO_PLATFORM_INTEGRATION.md (original plan)
