# Demo Builder Test Plan

End-to-end validation plan for the Demo Builder feature.

---

## Prerequisites

- [ ] Python 3.8+ installed
- [ ] Required packages: `pip install pyyaml jsonschema`
- [ ] Terraform 1.9.0+ installed
- [ ] Access to an Okta tenant (for full end-to-end test)
- [ ] GitHub CLI (`gh`) installed (for workflow tests)

---

## Test 1: Schema Validation

**Goal:** Verify the JSON Schema correctly validates config files.

### 1.1 Valid Config - Should Pass

```bash
cd /home/joevanhorn/projects/okta-terraform-demo-template

# Test with healthcare example
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --schema-check

# Expected: "Schema validation passed"
```

- [ ] Healthcare demo passes validation
- [ ] Financial services demo passes validation
- [ ] Technology company demo passes validation

```bash
python scripts/build_demo.py --config demo-builder/examples/financial-services-demo.yaml --schema-check
python scripts/build_demo.py --config demo-builder/examples/technology-company-demo.yaml --schema-check
```

### 1.2 Invalid Config - Should Fail

Create a test file with missing required field:

```bash
cat > /tmp/invalid-demo.yaml << 'EOF'
version: "1.0"
# Missing environment section - should fail
scenario:
  name: "Test"
  industry: "technology"
  company_size: "small"
departments: []
EOF

python scripts/build_demo.py --config /tmp/invalid-demo.yaml --schema-check
# Expected: Validation error about missing 'environment'
```

- [ ] Missing `environment` section fails validation
- [ ] Invalid `industry` value fails validation
- [ ] Invalid `company_size` value fails validation

---

## Test 2: Dry Run Mode

**Goal:** Verify dry run shows what would be generated without writing files.

```bash
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --dry-run
```

- [ ] Displays list of files that would be generated
- [ ] Shows user count, group count, app count
- [ ] Does NOT create any files
- [ ] No errors or exceptions

---

## Test 3: Terraform Generation

**Goal:** Verify Terraform files are generated correctly.

### 3.1 Generate from Healthcare Demo

```bash
# Create test output directory
mkdir -p /tmp/demo-test/terraform

# Generate Terraform
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --output /tmp/demo-test/terraform

# List generated files
ls -la /tmp/demo-test/terraform/
```

- [ ] `users.tf` created with user resources
- [ ] `groups.tf` created with group resources
- [ ] `group_memberships.tf` created
- [ ] `apps.tf` created with OAuth apps
- [ ] `app_assignments.tf` created
- [ ] `oig_entitlements.tf` created (if OIG enabled)

### 3.2 Validate Generated Terraform

```bash
cd /tmp/demo-test/terraform

# Format check
terraform fmt -check
# Expected: No output (files already formatted)

# Initialize (no backend)
terraform init -backend=false

# Validate syntax
terraform validate
# Expected: "Success! The configuration is valid."
```

- [ ] `terraform fmt` passes
- [ ] `terraform init` succeeds
- [ ] `terraform validate` succeeds

### 3.3 Inspect Generated Resources

```bash
# Count resources
grep -c "resource \"okta_user\"" /tmp/demo-test/terraform/users.tf
grep -c "resource \"okta_group\"" /tmp/demo-test/terraform/groups.tf
grep -c "resource \"okta_app_oauth\"" /tmp/demo-test/terraform/apps.tf
```

- [ ] User count matches config (healthcare has ~20 users)
- [ ] Group count matches config
- [ ] App count matches config (healthcare has 7 apps)

---

## Test 4: Technology Company Demo

**Goal:** Verify a different industry demo generates correctly.

```bash
rm -rf /tmp/demo-test/terraform/*

python scripts/build_demo.py \
  --config demo-builder/examples/technology-company-demo.yaml \
  --output /tmp/demo-test/terraform

cd /tmp/demo-test/terraform
terraform init -backend=false
terraform validate
```

- [ ] Generation succeeds
- [ ] `terraform validate` passes
- [ ] Contains expected departments (Engineering, DevOps, Security, etc.)

---

## Test 5: Financial Services Demo

**Goal:** Verify financial services demo with SOX compliance features.

```bash
rm -rf /tmp/demo-test/terraform/*

python scripts/build_demo.py \
  --config demo-builder/examples/financial-services-demo.yaml \
  --output /tmp/demo-test/terraform

cd /tmp/demo-test/terraform
terraform init -backend=false
terraform validate
```

- [ ] Generation succeeds
- [ ] `terraform validate` passes
- [ ] OIG access reviews generated (SOX compliance)

---

## Test 6: Custom Config Creation

**Goal:** Verify creating a custom config from template works.

### 6.1 Create Minimal Config

```bash
cat > /tmp/minimal-demo.yaml << 'EOF'
version: "1.0"

environment:
  name: "test-minimal"
  description: "Minimal test demo"
  email_domain: "test.example.com"

scenario:
  name: "Test Company"
  industry: "technology"
  company_size: "small"

departments:
  - name: "Engineering"
    manager:
      first_name: "Jane"
      last_name: "Smith"
      title: "VP Engineering"
    employees:
      - first_name: "Bob"
        last_name: "Dev"
        title: "Developer"

applications:
  - name: "test_app"
    type: "oauth_web"
    label: "Test Application"
    description: "A test OAuth app"
    assign_to_groups: ["Engineering"]
    settings:
      redirect_uris:
        - "https://test.example.com/callback"

output:
  separate_files: true
  include_comments: true
EOF

python scripts/build_demo.py --config /tmp/minimal-demo.yaml --schema-check
python scripts/build_demo.py --config /tmp/minimal-demo.yaml --output /tmp/demo-test/terraform --no-backup

cd /tmp/demo-test/terraform
terraform init -backend=false
terraform validate
```

- [ ] Schema validation passes
- [ ] Generation succeeds
- [ ] Terraform validation passes
- [ ] 2 users created (manager + 1 employee)
- [ ] 1 group created (Engineering department)
- [ ] 1 app created

---

## Test 7: Employee Count Generation

**Goal:** Verify auto-generated employees with count work correctly.

```bash
cat > /tmp/count-demo.yaml << 'EOF'
version: "1.0"

environment:
  name: "test-count"
  description: "Employee count test"
  email_domain: "count.example.com"

scenario:
  name: "Count Test"
  industry: "technology"
  company_size: "medium"

departments:
  - name: "Sales"
    manager:
      first_name: "Pat"
      last_name: "Sales"
      title: "Sales Director"
    employees:
      count: 5
      title_pattern: "Sales Representative"

output:
  separate_files: true
EOF

python scripts/build_demo.py --config /tmp/count-demo.yaml --output /tmp/demo-test/terraform --no-backup

grep -c "resource \"okta_user\"" /tmp/demo-test/terraform/users.tf
# Expected: 6 (1 manager + 5 employees)
```

- [ ] 6 users generated (1 manager + 5 auto-generated employees)
- [ ] Auto-generated employees have sequential names (Sales_Employee_1, etc.)
- [ ] All have correct title "Sales Representative"

---

## Test 8: OIG Features

**Goal:** Verify OIG entitlement bundles and access reviews generate correctly.

```bash
# Healthcare demo has OIG enabled
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --output /tmp/demo-test/terraform \
  --no-backup

# Check OIG resources
cat /tmp/demo-test/terraform/oig_entitlements.tf
```

- [ ] `oig_entitlements.tf` file created
- [ ] Entitlement bundle resources present
- [ ] Access review resources present (if defined in config)

---

## Test 9: Backup Behavior

**Goal:** Verify backup files are created when overwriting.

```bash
# First generation
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --output /tmp/demo-test/terraform

# Second generation (should create backups)
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --output /tmp/demo-test/terraform

# Check for backup files
ls /tmp/demo-test/terraform/*.backup 2>/dev/null | head -5
```

- [ ] Backup files created on second run
- [ ] Backup files have `.backup` extension

### 9.1 Test --no-backup Flag

```bash
rm -rf /tmp/demo-test/terraform/*

# First generation
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --output /tmp/demo-test/terraform

# Second generation with --no-backup
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --output /tmp/demo-test/terraform \
  --no-backup

# Should have no backup files
ls /tmp/demo-test/terraform/*.backup 2>/dev/null | wc -l
# Expected: 0
```

- [ ] No backup files created with `--no-backup` flag

---

## Test 10: Error Handling

**Goal:** Verify graceful error handling.

### 10.1 Non-existent Config File

```bash
python scripts/build_demo.py --config /tmp/nonexistent.yaml
# Expected: Clear error message about file not found
```

- [ ] Clear error message
- [ ] Non-zero exit code

### 10.2 Invalid YAML Syntax

```bash
cat > /tmp/bad-yaml.yaml << 'EOF'
version: "1.0"
environment:
  name: test
  bad indentation here
EOF

python scripts/build_demo.py --config /tmp/bad-yaml.yaml
# Expected: YAML parse error
```

- [ ] YAML parse error displayed
- [ ] Non-zero exit code

### 10.3 Invalid Application Type

```bash
cat > /tmp/bad-app.yaml << 'EOF'
version: "1.0"
environment:
  name: "test"
  email_domain: "test.example.com"
scenario:
  name: "Test"
  industry: "technology"
  company_size: "small"
departments: []
applications:
  - name: "bad_app"
    type: "invalid_type"
    label: "Bad App"
EOF

python scripts/build_demo.py --config /tmp/bad-app.yaml --schema-check
# Expected: Schema validation error about invalid type
```

- [ ] Schema validation fails with clear message

---

## Test 11: GitHub Workflow (Optional)

**Goal:** Test the GitHub workflow if repository access available.

### 11.1 Dry Run via Workflow

```bash
# Commit a test config to the repo first
cp demo-builder/examples/healthcare-demo.yaml demo-builder/test-demo.yaml
git add demo-builder/test-demo.yaml
git commit -m "test: Add test config for workflow validation"
git push

# Run workflow in dry-run mode
gh workflow run build-demo.yml \
  -f config_file=demo-builder/test-demo.yaml \
  -f environment=test \
  -f dry_run=true \
  -f validate=true

# Watch the run
gh run watch
```

- [ ] Workflow triggers successfully
- [ ] Config validation passes
- [ ] Terraform validation passes
- [ ] Dry run output shown in summary
- [ ] No PR created (dry run mode)

---

## Test 12: Full End-to-End (Optional - Requires Okta Tenant)

**Goal:** Apply generated Terraform to an actual Okta tenant.

⚠️ **Warning:** This will create real resources in your Okta tenant!

```bash
# Use a test/development Okta tenant
export OKTA_ORG_NAME="your-test-org"
export OKTA_BASE_URL="okta.com"
export OKTA_API_TOKEN="your-api-token"

# Generate to real environment directory
python scripts/build_demo.py \
  --config demo-builder/examples/healthcare-demo.yaml \
  --output environments/test-healthcare/terraform

cd environments/test-healthcare/terraform

# Initialize with backend
terraform init

# Plan
terraform plan -out=tfplan

# Review plan carefully!
# Apply only if plan looks correct
terraform apply tfplan
```

- [ ] Terraform plan shows expected resources
- [ ] Resources created in Okta without errors
- [ ] Users visible in Okta Admin Console
- [ ] Groups created correctly
- [ ] Apps created with correct settings
- [ ] (Cleanup) `terraform destroy` removes all resources

---

## Cleanup

```bash
# Remove test files
rm -rf /tmp/demo-test
rm -f /tmp/minimal-demo.yaml
rm -f /tmp/count-demo.yaml
rm -f /tmp/invalid-demo.yaml
rm -f /tmp/bad-yaml.yaml
rm -f /tmp/bad-app.yaml

# If you added test-demo.yaml to repo
git rm demo-builder/test-demo.yaml
git commit -m "chore: Remove test config"
git push
```

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| 1. Schema Validation | ⬜ | |
| 2. Dry Run Mode | ⬜ | |
| 3. Terraform Generation | ⬜ | |
| 4. Technology Demo | ⬜ | |
| 5. Financial Services Demo | ⬜ | |
| 6. Custom Config | ⬜ | |
| 7. Employee Count | ⬜ | |
| 8. OIG Features | ⬜ | |
| 9. Backup Behavior | ⬜ | |
| 10. Error Handling | ⬜ | |
| 11. GitHub Workflow | ⬜ | Optional |
| 12. Full End-to-End | ⬜ | Optional |

**Legend:** ⬜ Not tested | ✅ Passed | ❌ Failed

---

## Known Issues

Document any issues found during testing:

1. _[Issue description]_
2. _[Issue description]_

---

**Test Date:** ________________

**Tester:** ________________

**Build Demo Script Version:** 1.0
