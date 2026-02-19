# OAuth 2.0 Authentication Notes

This document covers important considerations when using OAuth 2.0 authentication with the Okta Terraform Provider.

## Recommendation: Use API Token

**For most use cases, we recommend using API token authentication** instead of OAuth 2.0 with private key authentication.

### Why API Token is Recommended

1. ✅ **Simpler setup** - No need to generate and manage RSA key pairs
2. ✅ **No permission limitations** - API tokens work without restrictions
3. ✅ **Easier troubleshooting** - No key format or signature validation issues
4. ✅ **Faster deployment** - Skip OAuth app configuration and key management

### When to Use OAuth 2.0

OAuth 2.0 authentication may be preferred in these scenarios:

- **Compliance requirements** mandate OAuth instead of long-lived API tokens
- **Audit trails** need to distinguish between different automation tools
- **Credential rotation** is easier with OAuth app keys than API tokens
- **Fine-grained scopes** are needed (though API tokens have equivalent permissions)

---

## OAuth Authentication Limitation Discovered

During implementation testing, we discovered a **permission limitation** with OAuth-authenticated service apps:

### Issue

**OAuth service apps cannot create other OAuth applications**, even when granted:
- ✅ `okta.apps.manage` scope
- ✅ `okta.apps.read` scope
- ✅ Super Administrator role

### Error Observed

```
Error: failed to create OAuth application: the API returned an error:
You do not have permission to perform the requested action
```

### Root Cause

This appears to be an Okta platform restriction where OAuth-authenticated service apps are prevented from creating other OAuth applications, regardless of granted scopes and admin roles.

### Workaround

**Use API token authentication instead:**

```hcl
provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}
```

API tokens do not have this limitation and can create OAuth applications successfully.

---

## OAuth Authentication Setup (If Required)

If you still need to use OAuth authentication, follow these steps:

### 1. Create OAuth Service App in Okta

1. **Applications** → **Applications** → **Create App Integration**
2. Choose **API Services** (OAuth 2.0 client credentials)
3. Give it a name like "Terraform Service App"
4. Click **Save**

### 2. Generate Key Pair

Use the automated workflow to generate a matching RSA key pair:

```bash
gh workflow run generate-oauth-keys.yml \
  --repo your-org/your-repo \
  -f environment=myorg
```

The workflow will:
- Generate an RSA-2048 key pair
- Convert private key to PKCS#1 format
- Create JWK format public key
- Display keys for you to copy

### 3. Upload Public Key to Okta

1. **Applications** → Your Terraform Service App → **General** tab
2. **Client Credentials** → **Edit**
3. **Turn OFF "Require DPoP"** ⚠️ (Terraform provider doesn't support DPoP)
4. **Public Keys** → **Add Key**
5. Paste the JWK from workflow output
6. **Save** and copy the **Key ID (kid)**

### 4. Grant OAuth Scopes

1. **Applications** → Your Terraform Service App
2. **Okta API Scopes** tab
3. **Grant** the following scopes:
   - `okta.apps.manage`
   - `okta.apps.read`
   - `okta.users.manage`
   - `okta.users.read`
   - `okta.groups.manage`
   - `okta.groups.read`
   - `okta.policies.manage`
   - `okta.policies.read`

### 5. Assign Admin Role

1. **Security** → **Administrators**
2. **Add Administrator** → **Grant administrator role to an app**
3. Select your Terraform Service App
4. Assign **Super Administrator** role
5. **Save**

### 6. Update GitHub Secrets

Add these secrets to your GitHub Environment:

- `OKTA_CLIENT_ID` - The client ID from your OAuth app
- `OKTA_PRIVATE_KEY` - The PKCS#1 private key from workflow
- `OKTA_PRIVATE_KEY_ID` - The Key ID (kid) from Okta

### 7. Update Provider Configuration

```hcl
provider "okta" {
  org_name = var.okta_org_name
  base_url = var.okta_base_url

  # OAuth 2.0 authentication
  client_id      = var.okta_client_id
  private_key    = var.okta_private_key
  private_key_id = var.okta_private_key_id
  scopes         = var.okta_scopes
}
```

---

## Key Format Requirements

### Private Key Format

The Terraform provider requires **PKCS#1 format** (not PKCS#8):

```
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

If you have a PKCS#8 key (starts with `-----BEGIN PRIVATE KEY-----`), convert it:

```bash
openssl rsa -in pkcs8.pem -traditional -out pkcs1.pem
```

Our workflows automatically handle this conversion.

### Public Key Format

Okta requires **JWK (JSON Web Key) format**:

```json
{
  "kty": "RSA",
  "kid": "terraform-key-abc123",
  "use": "sig",
  "alg": "RS256",
  "n": "...",
  "e": "AQAB"
}
```

Our `generate-oauth-keys.yml` workflow generates this automatically.

---

## Troubleshooting OAuth Authentication

### Error: "invalid private key"

**Causes:**
- Private key doesn't match public key in Okta
- Private key is in PKCS#8 format instead of PKCS#1
- Key corruption during copy/paste

**Solution:**
- Use `generate-oauth-keys.yml` workflow to generate fresh matching keys
- Verify keys with: `openssl rsa -in key.pem -check`

### Error: "client assertion invalid signature"

**Causes:**
- Private key doesn't match public key in Okta
- Wrong Key ID (kid) specified
- DPoP is enabled (not supported by provider)

**Solution:**
- Generate new matching key pair
- Verify Key ID matches between Okta and GitHub secret
- Disable DPoP in Okta OAuth app settings

### Error: "empty access token"

**Causes:**
- Missing OAuth scopes
- Missing admin role assignment
- Wrong key format
- Key pair mismatch

**Solution:**
- Verify all scopes are granted (not just "available")
- Verify Super Administrator role is assigned
- Check Okta System Log for detailed error message

### Error: "You do not have permission"

**Cause:**
- OAuth service app permission limitation (see above)

**Solution:**
- Switch to API token authentication

---

## Authentication Comparison

| Feature | API Token | OAuth 2.0 |
|---------|-----------|-----------|
| **Setup Complexity** | Simple | Complex |
| **Key Management** | None | RSA key pairs |
| **Permission Limitations** | None | Cannot create OAuth apps |
| **Credential Rotation** | Manual | Easier |
| **Audit Trail** | Generic | App-specific |
| **Recommended For** | Most use cases | Compliance requirements |

---

## Related Documentation

- [CLAUDE.md Gotcha #5](../CLAUDE.md#5-oauth-app-visibility-rules) - OAuth app visibility rules
- [Okta Provider Docs](https://registry.terraform.io/providers/okta/okta/latest/docs) - Official provider documentation
- [GitHub Workflow: generate-oauth-keys.yml](../.github/workflows/generate-oauth-keys.yml) - Automated key generation

---

## Summary

**Unless you have specific compliance requirements, use API token authentication.** It's simpler, has no permission limitations, and is the recommended approach for most Terraform automation.

If OAuth is required, be aware of the limitation preventing OAuth service apps from creating other OAuth apps, and plan accordingly (use API token for app creation, OAuth for other operations).
