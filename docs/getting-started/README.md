# Getting Started

Choose your path based on how you want to work:

## Path 1: AI-Assisted Deployment (Recommended)

**Best for:** Getting a complete environment running quickly with minimal manual work.

1. Fill out the [Demo Deployment Worksheet](../../demo-builder/DEMO_WORKSHEET.md)
2. Open Claude Code in this repository
3. Paste or reference the completed worksheet
4. Claude Code will generate Terraform, deploy infrastructure, and configure everything

**Time:** ~30 minutes (mostly waiting for deployments)

## Path 2: Demo Builder

**Best for:** Technical users who want to customize a YAML config and generate Terraform.

1. Copy an industry example: `cp demo-builder/examples/healthcare-demo.yaml demo-builder/my-demo.yaml`
2. Edit the YAML to match your requirements
3. Generate Terraform: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`
4. Apply: `cd environments/myorg/terraform && terraform init && terraform apply`

See [demo-builder/README.md](../../demo-builder/README.md) for full details.

**Time:** ~1 hour

## Path 3: Full GitOps Setup

**Best for:** Production use with PR-based workflows, approval gates, and CI/CD.

1. [Prerequisites](prerequisites.md) — What you need before starting
2. [AWS Backend Setup](aws-backend.md) — Deploy S3 state bucket and OIDC roles
3. [GitHub GitOps Setup](github-gitops.md) — Configure environments, secrets, branch protection
4. Write Terraform and manage via PRs

See also: [GitHub Basic Setup](github-basic.md) (minimal, no CI/CD) | [Local Only](local-only.md) (no GitHub Actions)

**Time:** ~2-3 hours

## Path 4: Manual / Local Only

**Best for:** Learning Terraform with Okta, quick prototyping.

1. [Prerequisites](prerequisites.md)
2. [Local Only Setup](local-only.md)
3. Write `.tf` files and run `terraform apply` directly

**Time:** ~30 minutes to first resource

---

## Documentation Map

| Topic | Location |
|-------|----------|
| **Guides** | [Demo Building](../guides/demo-building.md), [Cross-Org Migration](../guides/cross-org-migration.md), [Backup & Restore](../guides/backup-restore.md) |
| **Infrastructure** | [Active Directory](../infrastructure/active-directory.md), [Generic DB Connector](../infrastructure/generic-db-connector.md), [OPA](../infrastructure/opa-privileged-access.md), [OAG](../infrastructure/oag-deployment.md), [SCIM](../infrastructure/scim-server.md) |
| **Governance** | [Labels](../governance/labels.md), [Entitlements](../governance/entitlements.md), [Risk Rules](../governance/labels.md) |
| **Reference** | [Terraform Basics](../reference/terraform-basics.md), [Workflow Reference](../reference/workflow-reference.md), [API/Scripts](../reference/api-management.md) |
| **Troubleshooting** | [General](../troubleshooting/general.md), [Entitlement Bundles](../troubleshooting/entitlement-bundles.md), [Lessons Learned](../troubleshooting/lessons-learned.md) |
