# Demo Builder

Generate complete Okta demo environments from a simple YAML configuration file.

## Quick Start

```bash
# 1. Copy the template
cp demo-builder/demo-config.yaml.template demo-builder/my-demo.yaml

# 2. Edit your configuration
vim demo-builder/my-demo.yaml

# 3. Generate Terraform files
python scripts/build_demo.py --config demo-builder/my-demo.yaml

# 4. Apply to Okta
cd environments/myorg/terraform
terraform init && terraform plan && terraform apply
```

## Three Ways to Build a Demo

### Option 1: Edit Config Directly

Best for: Technical users comfortable with YAML

1. Copy `demo-config.yaml.template` to your own config file
2. Edit the YAML to define your users, groups, and apps
3. Run `build_demo.py` to generate Terraform

### Option 2: Use the Worksheet + AI

Best for: Non-technical users, complex demos

1. Fill out `DEMO_WORKSHEET.md` with your requirements
2. Paste to AI (ChatGPT, Claude, Gemini) with the prompt from `ai-assisted/prompts/generate_demo_config.md`
3. Save the generated YAML config
4. Run `build_demo.py` to generate Terraform

### Option 3: Use Pre-built Examples

Best for: Quick demos, industry-specific scenarios

1. Browse `examples/` for pre-built configurations
2. Copy one as your starting point
3. Customize as needed
4. Run `build_demo.py` to generate Terraform

## Configuration Reference

### Environment Settings

```yaml
environment:
  name: "myorg"                        # Directory name (environments/myorg/terraform)
  description: "My Demo"               # Human-readable description
  email_domain: "example.com"          # Domain for auto-generated emails
  # email_domain: "dept.company.com"   # Subdomains are supported
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

## CLI Reference

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

### Backup Behavior

When overwriting existing files, the generator creates backups with timestamps:

```
users.tf                        # Current file
users.tf.bak.20251222190443     # Backup from Dec 22, 2024 at 19:04:43
```

Use `--no-backup` to skip creating backup files.

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

When `separate_files: false`:

```
environments/myorg/terraform/
└── demo.tf               # All resources in one file
```

## Validation

The generator validates your config against a JSON schema:

- Required fields present
- Valid email formats
- Valid application types
- Valid date formats for access reviews
- Group references exist

To validate without generating:

```bash
python scripts/build_demo.py --config my-demo.yaml --schema-check
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
# ❌ Invalid
departments: []

# ✅ Valid - at least one department required
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

Application type must be one of:
- `oauth_web` - Server-side web applications
- `oauth_spa` - Single page applications
- `oauth_service` - Machine-to-machine / API
- `oauth_native` - Mobile / desktop apps
- `saml` - SAML enterprise SSO

### "Group not found for app"

Ensure the group name in `assign_to_groups` matches either:
- A department name (creates `{Department} Team` group)
- An additional group name in `groups.additional`

### Generated code has syntax errors

Run with `--validate` to check:

```bash
python scripts/build_demo.py --config my-demo.yaml --validate
```

## Integration with GitOps

The demo builder integrates with the GitOps workflow:

1. **Generate locally:**
   ```bash
   python scripts/build_demo.py --config demo-builder/my-demo.yaml
   ```

2. **Create a PR:**
   ```bash
   git checkout -b feature/new-demo
   git add environments/myorg/terraform/
   git commit -m "feat: Add new demo environment"
   git push -u origin feature/new-demo
   gh pr create
   ```

3. **Automated validation:**
   - PR triggers `terraform plan`
   - Review the plan in PR comments

4. **Apply after merge:**
   - Merge PR to main
   - Trigger `tf-apply.yml` workflow

## File Structure

```
demo-builder/
├── README.md                      # This file
├── demo-config.yaml.template      # Full template with all options
├── demo-config.schema.json        # JSON schema for validation
├── DEMO_WORKSHEET.md              # Fill-in-the-blanks questionnaire
└── examples/
    ├── healthcare-demo.yaml
    ├── financial-services-demo.yaml
    ├── technology-company-demo.yaml
    └── retail-demo.yaml
```

## Related Documentation

- [TERRAFORM-BASICS.md](../TERRAFORM-BASICS.md) - Terraform patterns and examples
- [DEMO_GUIDE.md](../DEMO_GUIDE.md) - Demo building strategies
- [ai-assisted/](../ai-assisted/) - AI-assisted code generation
- [RESOURCE_EXAMPLES.tf](../environments/myorg/terraform/RESOURCE_EXAMPLES.tf) - All resource examples
