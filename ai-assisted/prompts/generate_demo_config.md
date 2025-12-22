# Generate Demo Config Prompt Template

Use this prompt with any AI assistant (ChatGPT, Claude, Gemini) to generate a demo-config.yaml file from natural language requirements.

---

## How to Use

1. Copy the prompt below
2. Add your specific requirements after "MY REQUIREMENTS:"
3. Paste to your AI assistant
4. Save the generated YAML as `demo-builder/my-demo.yaml`
5. Run: `python scripts/build_demo.py --config demo-builder/my-demo.yaml`

---

## Prompt Template

```
You are an expert at generating Okta Terraform demo configurations. Generate a valid YAML configuration file for the Okta Demo Builder.

The configuration follows this structure:
- version: "1.0"
- environment: name, description, email_domain
- scenario: name, industry, company_size
- departments: list of departments with managers and employees
- additional_users: users outside department structure
- groups: additional groups beyond department groups
- applications: OAuth and SAML applications
- oig: entitlement bundles and access reviews (optional)
- policies: sign-on and password policies (optional)
- output: generation options

Key rules:
1. Use snake_case for application names (e.g., "salesforce_crm")
2. Email domain should be example.com or similar test domain
3. Dates must be ISO 8601 format: "2025-01-15T00:00:00Z"
4. Application types: oauth_web, oauth_spa, oauth_service, oauth_native, saml
5. Department groups are created automatically - only define additional groups
6. OIG requires license - set enabled: false if unsure
7. User types: employee, contractor, intern, vendor

MY REQUIREMENTS:
[Paste your requirements here - use the DEMO_WORKSHEET.md or describe in natural language]

OUTPUT:
Generate ONLY the complete YAML configuration. No explanations, just valid YAML.
```

---

## Example Usage

### Example 1: Simple Request

```
MY REQUIREMENTS:
Create a demo for a small tech startup with:
- Engineering team (5 developers)
- Sales team (3 people)
- GitHub for engineering
- Salesforce for sales
```

### Example 2: Using Worksheet

```
MY REQUIREMENTS:
[Paste filled-out DEMO_WORKSHEET.md here]
```

### Example 3: Detailed Request

```
MY REQUIREMENTS:
I need a healthcare demo environment for a hospital system called "Metro Health":

Departments:
- Clinical (1 CMO, 3 physicians, 5 nurses)
- Pharmacy (1 head pharmacist, 2 staff)
- IT (1 CIO, 2 admins)
- Administration (1 COO, 2 staff)

Applications:
- Epic EHR for clinical and pharmacy staff
- Lab system for clinical only
- Admin portal for IT and administration

Groups:
- Clinical Staff (all patient-facing)
- PHI Access (needs MFA)

OIG:
- Enable entitlement bundles
- Quarterly HIPAA access reviews

Policies:
- Require MFA for PHI access
- Strong password policy
```

---

## Validation

After receiving the generated YAML:

1. Save as `demo-builder/my-demo.yaml`

2. Validate:
   ```bash
   python scripts/build_demo.py --config demo-builder/my-demo.yaml --schema-check
   ```

3. Preview generation:
   ```bash
   python scripts/build_demo.py --config demo-builder/my-demo.yaml --dry-run
   ```

4. Generate Terraform:
   ```bash
   python scripts/build_demo.py --config demo-builder/my-demo.yaml
   ```

---

## Common Fixes

If validation fails, ask the AI to fix:

```
The configuration had this error: [paste error]
Please fix the YAML and output the complete corrected configuration.
```

### Common Issues

| Error | Fix |
|-------|-----|
| Invalid application type | Use: oauth_web, oauth_spa, oauth_service, oauth_native, saml |
| Date format error | Use ISO 8601: "2025-01-15T00:00:00Z" |
| Invalid resource name | Use snake_case, start with letter |
| Group not found | Ensure group is in departments or groups.additional |

---

## Tips for Better Results

1. **Be specific about numbers** - "5 engineers" not "some engineers"
2. **Name your apps** - "Salesforce for CRM" not just "a CRM"
3. **Specify industries** - helps generate appropriate apps and policies
4. **Mention compliance** - SOC2, HIPAA, SOX trigger appropriate reviews
5. **List group memberships** - who needs access to what

---

## Related Files

- [DEMO_WORKSHEET.md](../../demo-builder/DEMO_WORKSHEET.md) - Fill-in-the-blanks questionnaire
- [demo-config.yaml.template](../../demo-builder/demo-config.yaml.template) - Full template with all options
- [examples/](../../demo-builder/examples/) - Pre-built industry demos
