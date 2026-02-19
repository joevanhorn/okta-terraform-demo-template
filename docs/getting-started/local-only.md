# Local Terraform Usage (No GitHub Required)

**Difficulty:** Beginner | **Time:** 15 minutes | **Prerequisites:** Terraform installed, Okta API token

Manage your Okta tenant using Terraform on your local machine. No GitHub, no CI/CD, no complexity.

---

## What You'll Achieve

- Create Okta resources (users, groups, apps) using code
- Make changes by editing files and running commands
- Version your configuration with local state

**What this guide does NOT cover:**
- GitHub setup (see [GITHUB-BASIC.md](./GITHUB-BASIC.md))
- Team collaboration (see [GITHUB-GITOPS.md](./GITHUB-GITOPS.md))
- AWS backend (see [docs/AWS_BACKEND_SETUP.md](./docs/AWS_BACKEND_SETUP.md))

---

## Prerequisites

### 1. Install Terraform

```bash
# Check if installed
terraform --version
# Need 1.9.0 or higher
```

**Not installed?**
- Mac: `brew install terraform`
- Windows: `choco install terraform`
- Linux: [Download from hashicorp.com](https://developer.hashicorp.com/terraform/downloads)

### 2. Get Okta API Token

1. Log into **Okta Admin Console**
2. Go to **Security → API → Tokens**
3. Click **Create Token**
4. Name it: `Terraform Local`
5. **Copy the token immediately** (you won't see it again!)

### 3. Note Your Okta Details

You'll need:
- **Org name**: From your URL (e.g., `dev-12345678` from `https://dev-12345678.okta.com`)
- **Base URL**: Usually `okta.com` or `oktapreview.com`

---

## Step 1: Create Project Directory

```bash
mkdir okta-terraform
cd okta-terraform
```

---

## Step 2: Create Provider Configuration

Create a file named `provider.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = "~> 6.4.0"
    }
  }
}

provider "okta" {
  org_name  = "YOUR-ORG-NAME"      # e.g., "dev-12345678"
  base_url  = "okta.com"           # or "oktapreview.com"
  api_token = "YOUR-API-TOKEN"     # from Step 2 above
}
```

**Replace** the placeholder values with your actual Okta details.

---

## Step 3: Create Your First Resource

Create a file named `main.tf`:

```hcl
# Create a test user
resource "okta_user" "test_user" {
  first_name = "Test"
  last_name  = "User"
  login      = "test.user@example.com"
  email      = "test.user@example.com"
}

# Create a group
resource "okta_group" "test_group" {
  name        = "Test Group"
  description = "Created by Terraform"
}

# Add user to group
resource "okta_group_memberships" "test_membership" {
  group_id = okta_group.test_group.id
  users    = [okta_user.test_user.id]
}
```

**Change** `test.user@example.com` to use your email domain.

---

## Step 4: Initialize Terraform

```bash
terraform init
```

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Installing okta/okta v6.4.0...

Terraform has been successfully initialized!
```

---

## Step 5: Preview Changes

```bash
terraform plan
```

**This shows what will be created without making changes.**

You'll see:
```
Plan: 3 to add, 0 to change, 0 to destroy.
```

**Review the output carefully** - make sure it's creating what you expect.

---

## Step 6: Apply Changes

```bash
terraform apply
```

When prompted:
```
Do you want to perform these actions?
  Enter a value: yes
```

Type `yes` and press Enter.

**Output:**
```
okta_user.test_user: Creating...
okta_user.test_user: Creation complete after 2s
okta_group.test_group: Creating...
okta_group.test_group: Creation complete after 1s
okta_group_memberships.test_membership: Creating...
okta_group_memberships.test_membership: Creation complete after 1s

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
```

---

## Step 7: Verify in Okta

1. Log into **Okta Admin Console**
2. Go to **Directory → People** - you should see "Test User"
3. Go to **Directory → Groups** - you should see "Test Group"
4. Click the group and verify the user is a member

**Congratulations!** You just managed Okta with Infrastructure as Code.

---

## Making Changes

### Add More Resources

Edit `main.tf` and add:

```hcl
resource "okta_user" "another_user" {
  first_name = "Another"
  last_name  = "User"
  login      = "another.user@example.com"
  email      = "another.user@example.com"
}
```

Then:
```bash
terraform plan   # See what will change
terraform apply  # Apply the changes
```

### Modify Existing Resources

Change attributes in `main.tf`:

```hcl
resource "okta_group" "test_group" {
  name        = "Test Group - Updated"  # Changed
  description = "Updated by Terraform"   # Changed
}
```

Then:
```bash
terraform plan   # Shows: 1 to change
terraform apply
```

### Remove Resources

Delete the resource block from `main.tf`, then:

```bash
terraform plan   # Shows: 1 to destroy
terraform apply
```

---

## Common Commands

| Command | What It Does |
|---------|-------------|
| `terraform init` | Initialize project (run once) |
| `terraform fmt` | Format code nicely |
| `terraform validate` | Check syntax |
| `terraform plan` | Preview changes (safe) |
| `terraform apply` | Apply changes to Okta |
| `terraform destroy` | Remove ALL resources |
| `terraform state list` | Show managed resources |

---

## Security: Don't Commit Your Token!

Your `provider.tf` contains your API token. **Never commit this to Git.**

### Better: Use Environment Variables

Update `provider.tf`:

```hcl
provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}

variable "okta_org_name" {
  type        = string
  description = "Okta organization name"
}

variable "okta_base_url" {
  type        = string
  description = "Okta base URL"
  default     = "okta.com"
}

variable "okta_api_token" {
  type        = string
  description = "Okta API token"
  sensitive   = true
}
```

Then set environment variables:

```bash
export TF_VAR_okta_org_name="dev-12345678"
export TF_VAR_okta_base_url="okta.com"
export TF_VAR_okta_api_token="your-token-here"
```

Now your token isn't in any file.

---

## Troubleshooting

### "Error: 401 Unauthorized"
- API token is invalid or expired
- Create a new token in Okta Admin Console

### "Error: 404 Not Found"
- Org name or base URL is wrong
- Check your Okta URL carefully

### "Error: resource already exists"
- Resource with that name/email exists in Okta
- Either delete it in Okta, or import it (see below)

### Import Existing Resource

If a resource already exists:

```bash
# Find the ID in Okta Admin Console
terraform import okta_user.test_user "00u1234567890"
```

---

## Understanding State

Terraform creates a file called `terraform.tfstate` in your directory. This tracks what resources Terraform manages.

**Important:**
- Don't delete this file (you'll lose track of resources)
- Don't edit it manually
- Back it up if you care about recovery

For team usage with shared state, see [GITHUB-GITOPS.md](./GITHUB-GITOPS.md).

---

## Next Steps

### More Resources
See [TERRAFORM-BASICS.md](./TERRAFORM-BASICS.md) for examples of:
- OAuth applications
- SAML apps
- Policies
- OIG features (entitlement bundles, access reviews)

### Version Control
Ready to back up your code in GitHub?
→ See [GITHUB-BASIC.md](./GITHUB-BASIC.md)

### Team Collaboration
Need automated validation and team workflows?
→ See [GITHUB-GITOPS.md](./GITHUB-GITOPS.md)

### OIG Features
Using Okta Identity Governance?
→ See [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md)

---

## Quick Reference

### Minimal provider.tf
```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    okta = {
      source  = "okta/okta"
      version = "~> 6.4.0"
    }
  }
}

provider "okta" {
  org_name  = "YOUR-ORG"
  base_url  = "okta.com"
  api_token = "YOUR-TOKEN"
}
```

### Workflow
```bash
terraform init      # Once per project
terraform plan      # Before every apply
terraform apply     # Make changes
```

### Getting Help
- Terraform Okta Provider: [registry.terraform.io/providers/okta/okta](https://registry.terraform.io/providers/okta/okta/latest/docs)
- This repository: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
