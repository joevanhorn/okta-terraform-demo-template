# Documentation Hub

Central index for all documentation in this repository. Start here to find what you need.

---

## I'm New -- Where Do I Start?

| Your Goal | Guide | Time |
|-----------|-------|------|
| Get running fast with AI help | [AI-Assisted Deployment](../demo-builder/DEMO_WORKSHEET.md) | ~30 min |
| Generate a demo from YAML | [Demo Builder](../demo-builder/README.md) | ~1 hour |
| Set up full GitOps with CI/CD | [Full GitOps Setup](getting-started/github-gitops.md) | ~2-3 hours |
| Learn Terraform with Okta locally | [Local Only Setup](getting-started/local-only.md) | ~30 min |

All paths start with [Prerequisites](getting-started/prerequisites.md). See [Getting Started](getting-started/README.md) for the full decision guide.

---

## Okta Identity Governance (OIG)

Manage entitlements, labels, risk rules, and resource owners as code.

| Topic | Doc | Description |
|-------|-----|-------------|
| Entitlements | [entitlements.md](governance/entitlements.md) | Entitlement Settings API, enable/disable on apps, auto-detection |
| Labels | [labels.md](governance/labels.md) | Governance labels -- creation, assignment, API patterns |
| Label Workflow | [label-workflow.md](governance/label-workflow.md) | Two-phase GitOps workflow for labels (validate then apply) |
| Labels API | [labels-api-validation.md](governance/labels-api-validation.md) | API validation details and endpoint reference |
| Risk Rules | [gitops-value.md](governance/gitops-value.md) | GitOps value proposition for governance features |
| SCIM Entitlements | [scim-entitlement-discovery.md](../modules/scim-server/docs/scim-entitlement-discovery.md) | Surface app entitlements via SCIM 2.0 server |

---

## Infrastructure

Deploy and manage supporting infrastructure for Okta integrations.

| Topic | Doc | Description |
|-------|-----|-------------|
| Active Directory | [active-directory.md](../modules/ad-domain-controller/docs/active-directory.md) | Deploy Windows AD DCs on AWS, Okta AD Agent |
| Generic DB Connector | [generic-db-connector.md](../modules/generic-db-connector/docs/generic-db-connector.md) | PostgreSQL RDS, OPC agents, JML lifecycle |
| OPA (Privileged Access) | [opa-privileged-access.md](../modules/opa/docs/opa-privileged-access.md) | OPA gateway, security policies, server enrollment |
| OPC Agents | [opc-agents.md](../modules/opc-agent/docs/opc-agents.md) | On-premises connector agent deployment |
| SCIM Server | [scim-server.md](../modules/scim-server/docs/scim-server.md) | On-prem SCIM server setup and configuration |
| OAG Deployment | [oag-deployment.md](../modules/oag/docs/oag-deployment.md) | Okta Access Gateway deployment |
| OAG API | [oag-api.md](../modules/oag/docs/oag-api.md) | OAG application management API |
| ITP Demo | [itp-demo.md](../modules/itp-demo/docs/itp-demo.md) | Identity Threat Protection demo automation |
| ITP AWS Requirements | [itp-aws-requirements.md](../modules/itp-demo/docs/itp-aws-requirements.md) | AWS infrastructure for ITP demo |

---

## Guides

Step-by-step guides for common tasks.

| Topic | Doc | Description |
|-------|-----|-------------|
| Demo Building | [demo-building.md](guides/demo-building.md) | Build demos from YAML configs with AI assistance |
| Lifecycle Management | [lifecycle-management.md](../modules/lifecycle-management/docs/lifecycle-management.md) | Joiner/Mover/Leaver automation |
| SAML Federation | [saml-federation.md](../modules/saml-federation/docs/saml-federation.md) | Reusable SAML app module |
| Cross-Org Migration | [cross-org-migration.md](guides/cross-org-migration.md) | Copy groups, memberships, grants between tenants |
| Rollback | [rollback.md](guides/rollback.md) | Backup and restore procedures |
| Demo Platform | [demo-platform-integration.md](guides/demo-platform-integration.md) | Integration with Okta demo platform |
| ITP Demo | [itp-demo.md](../modules/itp-demo/docs/itp-demo.md) | Session hijacking simulation, SSF signals, risk policies |

---

## Automation & CI/CD

Workflows, scripts, and automation tools.

| Topic | Doc | Description |
|-------|-----|-------------|
| Workflow Reference | [workflow-reference.md](reference/workflow-reference.md) | All 48 GitHub Actions workflows categorized |
| API & Scripts | [api-management.md](reference/api-management.md) | Python script reference for OIG operations |
| Contributing | [contributing.md](reference/contributing.md) | Guidelines for submitting issues and PRs |

---

## Reference

Foundational concepts and technical details.

| Topic | Doc | Description |
|-------|-----|-------------|
| Terraform Basics | [terraform-basics.md](reference/terraform-basics.md) | Resource examples, HCL syntax, patterns |
| Provider Coverage | [provider-coverage.md](reference/provider-coverage.md) | What's in the Terraform provider vs API vs manual |
| OAuth Auth | [oauth-authentication.md](reference/oauth-authentication.md) | OAuth authentication setup and limitations |
| Terraformer | [terraformer.md](reference/terraformer.md) | Importing existing Okta resources |
| Project Structure | [getting-started/project-structure.md](getting-started/project-structure.md) | Repository layout and conventions |

---

## AI-Assisted Tools

| Topic | Doc | Description |
|-------|-----|-------------|
| AI Prompts | [ai-assisted/README.md](../ai-assisted/README.md) | Prompt templates for Claude, Gemini, GPT |
| Demo Worksheet | [DEMO_WORKSHEET.md](../demo-builder/DEMO_WORKSHEET.md) | Fill-in worksheet for full environment deployment |
| Demo Builder | [demo-builder/README.md](../demo-builder/README.md) | YAML-based demo generation with industry templates |

---

## Troubleshooting

| Topic | Doc | Description |
|-------|-----|-------------|
| General | [general.md](troubleshooting/general.md) | Common errors by category with solutions |
| Entitlement Bundles | [entitlement-bundles.md](troubleshooting/entitlement-bundles.md) | Bundle-specific errors and fixes |
| Lessons Learned | [lessons-learned.md](troubleshooting/lessons-learned.md) | Deep troubleshooting insights |
| Workflow Fixes | [workflow-fixes.md](troubleshooting/workflow-fixes.md) | GitHub Actions workflow issues |
| Diagnostics | [diagnostics.md](troubleshooting/diagnostics.md) | EC2, network, and connectivity diagnostics |

---

**Quick Reference:** See [QUICK-REFERENCE.md](QUICK-REFERENCE.md) for a single-page cheat sheet.

**Looking for older docs?** See [docs/archive/](archive/README.md) for superseded documentation kept for historical reference.
