# OPA (Okta Privileged Access)

This directory consolidates OPA-related examples, scripts, and documentation.

> **Note:** This is NOT a Terraform module — OPA resources are managed directly in your environment's `terraform/` directory using the `oktapam` provider. This directory collects the reference materials in one place.

## Contents

- `docs/` — Setup guide and architecture documentation
- `examples/` — Example Terraform configurations (`.tf.example`, `.tfvars.example`)
- `scripts/` — Import utility for OPA resources

## Quick Start

1. Copy example files to your environment:
   ```bash
   cp modules/opa/examples/opa_resources.tf.example environments/myorg/terraform/opa_resources.tf
   cp modules/opa/examples/opa_security_policies.tf.example environments/myorg/terraform/opa_security_policies.tf
   ```
2. Configure `oktapam` provider credentials in your GitHub Environment
3. Run `terraform plan` via workflow

See `docs/opa-privileged-access.md` for full setup instructions.
