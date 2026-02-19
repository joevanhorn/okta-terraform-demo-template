# Prompt: Deploy Full Environment with Claude Code

Use this prompt with **Claude Code** (running inside this repository) to deploy a complete Okta + infrastructure environment from a filled-out Demo Deployment Worksheet.

---

## How to Use

1. Fill out the [Demo Deployment Worksheet](../../demo-builder/DEMO_WORKSHEET.md) (all sections)
2. Open Claude Code in this repository root
3. Paste the following prompt along with your completed worksheet:

---

## Prompt Template

```
I have a completed Demo Deployment Worksheet for this Okta GitOps template repository.
Please deploy the full environment following these steps in order:

DEPLOYMENT ORDER:
1. Create the environment directory structure
2. Set up Terraform backend and provider configuration
3. Generate Okta Terraform resources (users, groups, apps, policies, OIG)
4. Deploy infrastructure (in this order, skipping any not selected):
   a. Active Directory Domain Controller(s)
   b. Generic Database Connector (RDS + schema)
   c. OPC Agents for the database connector
   d. SCIM Server
   e. OPA Gateway and security policies
5. Run terraform init and terraform plan for each stack
6. Pause for my approval before each terraform apply
7. Run diagnostic workflows to verify each component

IMPORTANT RULES:
- Use the modules in modules/ (ad-domain-controller, generic-db-connector, opc-agent)
- Put Okta resources in environments/{env}/terraform/
- Put infrastructure in environments/{env}/*-infrastructure/
- Use S3 backend with the bucket name from the worksheet
- Generate terraform.tfvars files with worksheet values
- Use GitHub Environment secrets pattern for sensitive values
- Follow all patterns documented in CLAUDE.md (especially $$ escaping)
- Create GitHub Environment if it doesn't exist

HERE IS MY COMPLETED WORKSHEET:

[Paste your filled-out worksheet here]
```

---

## What Claude Code Will Do

### Phase 1: Environment Setup
- Create `environments/{name}/terraform/` directory
- Create `environments/{name}/config/` directory
- Generate `provider.tf` with S3 backend
- Generate `variables.tf` and `terraform.tfvars`

### Phase 2: Okta Resources
Based on worksheet sections 1-6:
- `users.tf` or `users_from_csv.tf` — Users with departments, titles, managers
- `groups.tf` — Department groups + custom groups
- `group_memberships.tf` — Group membership rules
- `apps.tf` — Applications (OAuth, SAML, etc.)
- `app_assignments.tf` — App-to-group assignments
- `policies.tf` — Sign-on policies, password policies
- `oig_entitlements.tf` — Entitlement bundles (if OIG enabled)
- `oig_reviews.tf` — Access review campaigns (if OIG enabled)

### Phase 3: Infrastructure (if selected)
Based on worksheet sections 7-11:

**Active Directory:**
- Creates `environments/{name}/ad-infrastructure/`
- Uses `modules/ad-domain-controller`
- Configures domain name, NetBIOS, sample users
- Triggers `ad-deploy.yml` workflow

**Generic Database Connector:**
- Creates `environments/{name}/generic-db-infrastructure/`
- Uses `modules/generic-db-connector`
- Configures RDS instance, schema, stored procedures
- Triggers `generic-db-deploy.yml` and `generic-db-schema-init.yml`

**OPC Agents:**
- Creates `environments/{name}/opc-infrastructure/`
- Uses `modules/opc-agent`
- Configures agent count, instance types
- Triggers `opc-deploy.yml` and `opc-install-agent.yml`

**SCIM Server:**
- Creates `environments/{name}/infrastructure/scim-server/`
- Configures domain name, auth token
- Triggers `deploy-scim-server.yml`

**OPA (Privileged Access):**
- Adds `opa_resources.tf` and `opa_security_policies.tf` to terraform dir
- Configures security policy tiers based on worksheet
- Triggers `opa-plan.yml` and `opa-apply.yml`

### Phase 4: Verification
- Runs `terraform validate` on each stack
- Suggests diagnostic workflows to run
- Provides a deployment summary

---

## Key Workflows Used

| Component | Deploy Workflow | Verify Workflow |
|-----------|----------------|-----------------|
| Okta resources | `tf-apply.yml` | `tf-plan.yml` |
| Active Directory | `ad-deploy.yml` | `ad-health-check.yml` |
| Generic DB | `generic-db-deploy.yml` | `generic-db-schema-init.yml` |
| OPC Agents | `opc-deploy.yml` | `opc-install-agent.yml` |
| SCIM Server | `deploy-scim-server.yml` | `scim-check-status.yml` |
| OPA | `opa-apply.yml` | `opa-test.yml` |
| Network issues | — | `diagnose-connectivity.yml` |
| Instance issues | — | `diagnose-instance.yml` |

---

## Tips

- **Start with Okta resources first** — infrastructure can be added later
- **Use `terraform plan` before `apply`** — always review changes
- **Check diagnostic workflows** after infrastructure deploys
- **OPA is optional** — only enable if you have OPA license
- **Generic DB needs OPC agents** — deploy both or neither
- **AD Agent requires manual install** — the workflow deploys the DC, but the Okta AD Agent needs interactive browser-based activation
