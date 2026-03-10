# Demo Builder

Generate and deploy complete Okta demo environments — users, groups, apps, governance, infrastructure, and more.

## Quick Start (Recommended)

The fastest way to build a demo is the **Worksheet + Claude Code** approach:

1. Fill out `DEMO_WORKSHEET.md` with your demo requirements
2. Open Claude Code in this repository root
3. Paste this prompt:

   ```
   I have a completed Demo Deployment Worksheet. Please deploy the full
   environment following the instructions in
   ai-assisted/prompts/deploy_full_environment.md.

   HERE IS MY COMPLETED WORKSHEET:
   [Paste your filled worksheet here]
   ```

4. Claude Code will generate Terraform, deploy via GitHub workflows, configure governance, and validate — prompting you before each apply

This approach handles **everything**: Okta resources, OIG governance, lifecycle management, AD infrastructure, database connectors, OPC agents, SCIM servers, OPA privileged access, ITP demos, and SAML federation.

## What Gets Deployed

The worksheet covers 14 sections across 6 categories:

| Category | Sections | What's Created |
|----------|----------|---------------|
| **Okta Basics** | 1-4 | Users, groups, apps, policies |
| **Governance** | 5-6 | Entitlement bundles, access reviews, lifecycle management |
| **Security** | 7-8 | Sign-on/password policies, ITP demo |
| **Infrastructure** | 9-12 | AD, database, OPC agents, SCIM, OPA |
| **Advanced** | 13 | SAML federation |
| **Deployment** | 14 | AWS backend, GitHub secrets |

Only Sections 1-4 are required. Everything else is opt-in.

## Alternative Approaches

### Pre-built Industry Examples

Browse `examples/` for industry-specific configurations to use as inspiration:

- `examples/financial-services-demo.yaml` — Bank/fintech with SOX compliance
- `examples/healthcare-demo.yaml` — Healthcare with HIPAA compliance
- `examples/technology-company-demo.yaml` — SaaS with SOC2 compliance

These YAML configs work with `build_demo.py` for basic Okta resource generation (users, groups, apps). For full environment deployment including infrastructure, use the worksheet approach above.

### Legacy: build_demo.py (Deprecated)

> **Note:** `build_demo.py` generates basic Okta resources only (users, groups, apps, OIG bundles). It does not deploy infrastructure, configure governance APIs, or set up ITP demos. Use the Worksheet + Claude Code approach for full deployments.

```bash
# Copy template
cp demo-builder/demo-config.yaml.template demo-builder/my-demo.yaml

# Edit configuration
vim demo-builder/my-demo.yaml

# Generate Terraform files
python scripts/build_demo.py --config demo-builder/my-demo.yaml

# Apply to Okta
cd environments/myorg/terraform
terraform init && terraform plan && terraform apply
```

## Configuration Reference

### Environment Settings

```yaml
environment:
  name: "myorg"                        # Directory name (environments/myorg/terraform)
  description: "My Demo"               # Human-readable description
  email_domain: "example.com"          # Domain for auto-generated emails
```

### Departments and Users

Define your organizational structure:

```yaml
departments:
  - name: "Engineering"
    manager:
      first_name: "Jane"
      last_name: "Smith"
      title: "VP of Engineering"
    employees:
      # Option A: Explicit list
      - first_name: "Alice"
        last_name: "Developer"
        title: "Senior Engineer"

  - name: "Sales"
    manager:
      first_name: "Pat"
      last_name: "Director"
      title: "Sales Director"
    employees:
      # Option B: Auto-generate (creates Sal01_Employee, Sal02_Employee, etc.)
      count: 5
      title_pattern: "Sales Representative"  # Becomes "Sales Representative 1", etc.
```

**Note:** At least one department with a manager is required.

### Additional Users

Users outside the department structure:

```yaml
additional_users:
  - first_name: "Sam"
    last_name: "Contractor"
    user_type: "contractor"
    department: "Engineering"
```

### Groups

Department groups are created automatically. Add custom groups:

```yaml
groups:
  additional:
    - name: "Leadership"
      description: "All managers"
      include_managers: true

    - name: "Contractors"
      include_user_types: ["contractor"]
```

### Applications

```yaml
applications:
  - name: "salesforce"
    type: "oauth_web"       # oauth_web, oauth_spa, oauth_service, oauth_native, saml
    label: "Salesforce CRM"
    assign_to_groups: ["Marketing", "Leadership"]
    settings:
      redirect_uris:
        - "https://login.salesforce.com/callback"
```

**Application Types:**

| Type | Use Case | Client Auth |
|------|----------|-------------|
| `oauth_web` | Server-side web apps | Client secret |
| `oauth_spa` | Single page apps (React, Vue) | PKCE, no secret |
| `oauth_service` | M2M, APIs | Client credentials |
| `oauth_native` | Mobile/desktop apps | PKCE, no secret |
| `saml` | Enterprise SSO | SAML assertion |

### OIG Features

```yaml
oig:
  enabled: true

  entitlement_bundles:
    - name: "Basic Employee Access"
      description: "Standard access package"

  access_reviews:
    - name: "Q1 2025 Review"
      start_date: "2025-01-15T00:00:00Z"
      end_date: "2025-02-15T23:59:59Z"
      reviewer_type: "MANAGER"
```

### Output Options

```yaml
output:
  directory: "environments/{{ environment.name }}/terraform"
  separate_files: true      # users.tf, groups.tf, etc.
  include_comments: true    # Add explanatory comments
  validate_on_generate: true
```

## CLI Reference (build_demo.py)

```bash
# Basic generation
python scripts/build_demo.py --config demo-builder/my-demo.yaml

# Dry run (preview without writing)
python scripts/build_demo.py --config my-demo.yaml --dry-run

# Custom output directory
python scripts/build_demo.py --config my-demo.yaml --output /tmp/test

# Validate after generation
python scripts/build_demo.py --config my-demo.yaml --validate

# Schema check only
python scripts/build_demo.py --config my-demo.yaml --schema-check

# Skip backup of existing files
python scripts/build_demo.py --config my-demo.yaml --no-backup
```

## Generated Files

When `separate_files: true`:

```
environments/myorg/terraform/
├── users.tf              # okta_user resources
├── groups.tf             # okta_group resources
├── group_memberships.tf  # okta_group_memberships resources
├── apps.tf               # okta_app_oauth resources
├── app_assignments.tf    # okta_app_group_assignment resources
└── oig.tf                # okta_entitlement_bundle, okta_reviews
```

## Examples

### Simple Demo (5 users, 1 app)

```yaml
version: "1.0"

environment:
  name: "demo"
  email_domain: "example.com"

departments:
  - name: "Engineering"
    manager:
      first_name: "Jane"
      last_name: "Smith"
      title: "Engineering Manager"
    employees:
      count: 4
      title_pattern: "Software Engineer"

applications:
  - name: "github"
    type: "oauth_web"
    label: "GitHub Enterprise"
    assign_to_groups: ["Engineering"]
    settings:
      redirect_uris:
        - "https://github.example.com/callback"
```

### Multi-Department Demo

See `examples/financial-services-demo.yaml` for a complete example with:
- 3 departments (Engineering, Marketing, Finance)
- Contractors and executives
- Multiple OAuth applications
- OIG entitlement bundles
- Access review campaigns

## Troubleshooting

### "Configuration file not found"

Ensure the path is correct relative to your current directory:

```bash
# From repo root
python scripts/build_demo.py --config demo-builder/my-demo.yaml

# Or use absolute path
python scripts/build_demo.py --config /path/to/my-demo.yaml
```

### "Validation error: 'departments' is too short"

You must have at least one department with a manager. Empty departments arrays are not allowed:

```yaml
# Invalid
departments: []

# Valid - at least one department required
departments:
  - name: "General"
    manager:
      first_name: "Admin"
      last_name: "User"
      title: "Administrator"
    employees: []  # Empty employees is OK
```

### "Validation error" for YAML syntax

Check your YAML syntax. Common issues:
- Indentation must be consistent (2 spaces recommended)
- Strings with special characters need quotes
- Dates must be ISO 8601 format: `2025-01-15T00:00:00Z`

### "Invalid application type"

Application type must be one of: `oauth_web`, `oauth_spa`, `oauth_service`, `oauth_native`, `saml`

### "Group not found for app"

Ensure the group name in `assign_to_groups` matches either:
- A department name (creates `{Department} Team` group)
- An additional group name in `groups.additional`

## File Structure

```
demo-builder/
├── README.md                      # This file
├── demo-config.yaml.template      # YAML template (for build_demo.py)
├── demo-config.schema.json        # JSON schema for validation
├── DEMO_WORKSHEET.md              # Deployment worksheet (for Claude Code)
└── examples/
    ├── healthcare-demo.yaml
    ├── financial-services-demo.yaml
    ├── technology-company-demo.yaml
    └── retail-demo.yaml
```

## Related Documentation

- [deploy_full_environment.md](../ai-assisted/prompts/deploy_full_environment.md) - Full deployment prompt for Claude Code
- [TERRAFORM-BASICS.md](../TERRAFORM-BASICS.md) - Terraform patterns and examples
- [DEMO_GUIDE.md](../DEMO_GUIDE.md) - Demo building strategies
- [ai-assisted/](../ai-assisted/) - AI-assisted code generation
- [RESOURCE_EXAMPLES.tf](../environments/myorg/terraform/RESOURCE_EXAMPLES.tf) - All resource examples
