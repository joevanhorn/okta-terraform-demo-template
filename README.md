# Okta Identity Governance -- GitOps Template

A GitOps template for managing Okta Identity Governance using Terraform, GitHub Actions, and Python automation. Fork it to manage your Okta tenants as code -- from simple demos to production environments.

---

## Quick Start

### Path 1: AI-Assisted Deployment (Recommended)

The fastest way to get a complete environment running -- Okta resources **and** infrastructure.

1. Fill out the [Demo Deployment Worksheet](demo-builder/DEMO_WORKSHEET.md) (Okta users/groups/apps + AD, Generic DB, OPA, SCIM infrastructure)
2. Open Claude Code in this repository
3. Paste the completed worksheet with the [deployment prompt](ai-assisted/prompts/deploy_full_environment.md)
4. Claude deploys everything -- Terraform, infrastructure, verification -- pausing for your approval at each step

### Path 2: Demo Builder

Generate Terraform from a YAML config file.

1. Copy an example: `cp demo-builder/examples/healthcare-demo.yaml demo-builder/my-demo.yaml`
2. Customize the YAML
3. Generate: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`
4. Apply: `cd environments/myorg/terraform && terraform init && terraform apply`

### Path 3: Full GitOps Setup

Production-grade workflow with PRs, approval gates, and CI/CD.

1. See [Getting Started Guide](docs/getting-started/README.md)

---

## What's Included

| Capability | Description | Status |
|---|---|---|
| **Okta Identity Governance** | Users, groups, apps, entitlement bundles, access reviews, approval sequences, catalog entries | Core |
| **GitOps Workflows** | PR-based terraform plan/apply, drift detection, approval gates | Core |
| **Governance Automation** | Labels, resource owners, risk rules (SOD policies), entitlement management | Core |
| **Active Directory** | Deploy Windows AD DCs on AWS, manage OUs, health checks, Okta AD Agent installation | Infrastructure |
| **Generic DB Connector** | PostgreSQL RDS, OPC agents, SCIM server, JML lifecycle workflows | Infrastructure |
| **Okta Privileged Access** | OPA gateway, security policies, password checkout, server enrollment | Infrastructure |
| **SCIM Server** | Deploy, configure, and manage on-prem SCIM servers for provisioning | Infrastructure |
| **OAG (Access Gateway)** | Deploy and manage Okta Access Gateway applications | Infrastructure |
| **Lifecycle Management** | Joiner/Mover/Leaver automation, contractor workflows, OIG integration | Infrastructure |
| **SAML Federation** | Reusable SAML app module with attribute mapping and group assignments | Infrastructure |
| **Demo Builder** | Generate complete environments from YAML configs with industry templates | Tooling |
| **Backup and Restore** | Resource-based exports and S3 state-based rollback | Tooling |
| **Cross-Org Migration** | Copy groups, memberships, and entitlement grants between Okta tenants | Tooling |
| **AI-Assisted Generation** | Prompt-based and CLI-based Terraform code generation (Gemini, GPT, Claude) | Tooling |

---

## Repository Structure

```
.
├── environments/myorg/          # Your Okta tenant (one directory per org)
│   ├── terraform/               # Terraform resources (.tf files)
│   ├── config/                  # JSON configs (owners, labels, risk rules)
│   └── *-infrastructure/        # Optional: AD, Generic DB, OPC, OAG
├── modules/                     # Reusable Terraform modules
│   ├── ad-domain-controller/    # Windows AD DC on AWS
│   ├── generic-db-connector/    # PostgreSQL RDS + schema + stored procedures
│   ├── opc-agent/               # OPC Agent EC2 instances
│   ├── lifecycle-management/    # JML automation with OIG
│   └── saml-federation/         # SAML app with attribute mapping
├── .github/workflows/           # 40+ GitHub Actions workflows
├── scripts/                     # Python automation (45+ scripts)
├── demo-builder/                # YAML-based demo generation
│   └── examples/                # Industry templates (financial, healthcare, tech)
├── ai-assisted/                 # AI code generation tools
├── backup-restore/              # Backup and disaster recovery
│   ├── resource-based/          # Export resources to files
│   └── state-based/             # S3 state version rollback
└── docs/                        # Documentation (categorized)
    ├── getting-started/         # Setup guides, prerequisites, backend config
    ├── guides/                  # Demo building, migrations, lifecycle, rollback
    ├── infrastructure/          # AD, OPA, SCIM, OAG deployment
    ├── governance/              # Labels, entitlements, GitOps value
    ├── reference/               # Terraform basics, workflows, API, provider docs
    └── troubleshooting/         # Common issues, entitlement bundles, workflow fixes
```

---

## Architecture

This repository uses a three-layer resource management model:

- **Layer 1 -- Terraform** manages the core Okta resources: users, groups, apps, entitlement bundles, access reviews, approval sequences, and catalog entries. All configuration lives in `environments/{env}/terraform/*.tf` files.
- **Layer 2 -- Python API Scripts** handle governance features not yet in the Terraform provider: resource owners, governance labels, risk rules (SOD policies), and entitlement settings. Configuration lives in `environments/{env}/config/*.json` files.
- **Layer 3 -- Manual (Okta Admin UI)** covers entitlement bundle assignments (which users/groups have which bundles), access review decisions, and certain advanced OIG configurations.

**GitOps workflow:**

```
Branch --> PR (plan runs automatically) --> Review --> Merge --> Apply (with approval gate)
```

Each environment maintains independent Terraform state in S3 with DynamoDB locking. GitHub Actions authenticate to AWS via OIDC -- no long-lived credentials required.

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Okta tenant** | With API token (Super Admin or equivalent). OIG features require Identity Governance license. |
| **Terraform** | >= 1.9.0 with Okta provider >= 6.4.0 |
| **Python** | >= 3.8 with `requests`, `pyyaml`, `python-dotenv` (see `requirements.txt`) |
| **GitHub account** | For GitOps workflows (optional for local-only usage) |
| **AWS account** | Optional -- for S3/DynamoDB state backend and infrastructure modules |

---

## Documentation

All documentation has been organized into the `docs/` directory by topic:

| Section | Contents |
|---|---|
| [Getting Started](docs/getting-started/README.md) | Setup guides, prerequisites, backend configuration, directory structure |
| [Guides](docs/guides/demo-building.md) | Demo building, cross-org migration, lifecycle management, rollback procedures |
| [Infrastructure](docs/infrastructure/active-directory.md) | Active Directory, OPA, SCIM server, OAG deployment |
| [Governance](docs/governance/labels.md) | Labels, entitlements, label workflows, GitOps value proposition |
| [Reference](docs/reference/workflow-reference.md) | Terraform basics, workflow reference, API management, provider coverage |
| [Troubleshooting](docs/troubleshooting/general.md) | Common issues, entitlement bundle errors, workflow fixes |

---

## Contributing

See [Contributing Guide](docs/reference/contributing.md) for guidelines on submitting issues and pull requests.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
