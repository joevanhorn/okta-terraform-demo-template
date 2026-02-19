# GitHub Repository Structure

## 📁 Complete Directory Layout

```
okta-terraform-complete-demo/
├── .github/
│   ├── workflows/
│   │   ├── import-all-resources.yml
│   │   ├── export-oig.yml
│   │   ├── governance-setup.yml
│   │   ├── apply-owners.yml
│   │   ├── apply-labels.yml
│   │   ├── apply-labels-from-config.yml
│   │   └── admin-protection.yml
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       ├── feature_request.md
│       └── question.md
│
├── environments/
│   ├── myorg/           # Primary demo tenant
│   │   ├── terraform/           # Terraform configurations
│   │   │   ├── oig_entitlements.tf
│   │   │   ├── oig_reviews.tf
│   │   │   ├── app_oauth.tf
│   │   │   ├── user.tf
│   │   │   ├── group.tf
│   │   │   └── ...
│   │   ├── imports/             # Raw API import data
│   │   │   ├── entitlements.json
│   │   │   └── reviews.json
│   │   ├── config/              # API-only resource configs
│   │   │   ├── owner_mappings.json
│   │   │   └── label_mappings.json
│   │   └── README.md
│   ├── production/              # Production tenant
│   ├── staging/                 # Staging tenant
│   ├── development/             # Development tenant
│   └── README.md
│
├── scripts/
│   ├── import_oig_resources.py    # Import OIG resources from Okta
│   ├── sync_owner_mappings.py     # Sync resource owners
│   ├── sync_label_mappings.py     # Sync governance labels
│   └── apply_resource_owners.py   # Apply owner assignments
│
├── docs/
│   ├── API_MANAGEMENT.md
│   ├── COMPLETE_SOLUTION.md
│   ├── CONTRIBUTING.md
│   ├── ENVIRONMENT_SETUP_EXAMPLE.md    # MyOrg environment setup guide
│   ├── OIG_MANUAL_IMPORT.md
│   ├── PROJECT_STRUCTURE.md
│   ├── TERRAFORMER.md
│   ├── TERRAFORMER_OIG_FAQ.md
│   └── TESTING.md
│
├── .gitignore
├── .gitattributes
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── DIRECTORY_GUIDE.md            # Environment-based structure guide
├── LICENSE
├── OIG_PREREQUISITES.md          # Prerequisites for OIG features
├── README.md
└── SECURITY.md
```

## 📝 File Descriptions

### Root Directory
- **README.md** - Main project documentation and quick start guide
- **DIRECTORY_GUIDE.md** - Guide to environment-based structure
- **OIG_PREREQUISITES.md** - Prerequisites for using OIG features
- **LICENSE** - MIT license
- **CHANGELOG.md** - Version history
- **SECURITY.md** - Security policy
- **CODE_OF_CONDUCT.md** - Community guidelines
- **.gitignore** - Files to exclude from git
- **.gitattributes** - Git attributes for line endings

### .github/workflows/
GitHub Actions workflows for automation (environment-agnostic):
- **import-all-resources.yml** - Import all OIG resources from any tenant environment
- **export-oig.yml** - Export OIG resources (requires environment parameter)
- **governance-setup.yml** - Set up governance configurations (requires environment parameter)
- **apply-owners.yml** - Apply resource owner assignments (requires environment parameter)
- **apply-labels.yml** - Apply governance labels (requires environment parameter)
- **apply-labels-from-config.yml** - Deploy labels from config file (requires environment parameter)
- **admin-protection.yml** - Protect admin users from modifications

### environments/
Environment-specific Okta configurations organized by tenant:
- **myorg/** - Primary demo tenant (oktapreview.com)
  - `terraform/` - Terraform configurations for all resources
  - `imports/` - Raw API import data (JSON)
  - `config/` - Resource owners, labels, and API configs
- **production/** - Production tenant (placeholder)
- **staging/** - Staging tenant (placeholder)
- **development/** - Development tenant (placeholder)
- Each environment is self-contained with its own Terraform state and configs

### scripts/
Python automation scripts:
- **import_oig_resources.py** - Import OIG resources from Okta and generate Terraform
- **sync_owner_mappings.py** - Sync resource owner assignments from Okta
- **sync_label_mappings.py** - Sync governance label assignments from Okta
- **apply_resource_owners.py** - Apply resource owner assignments to Okta

### docs/
Comprehensive documentation:
- **ENVIRONMENT_SETUP_EXAMPLE.md** - Setup guide for MyOrg environment
- **API_MANAGEMENT.md** - API-based resource management guide
- **OIG_MANUAL_IMPORT.md** - Manual OIG import procedures
- **TERRAFORMER.md** - Terraformer usage guide
- **TERRAFORMER_OIG_FAQ.md** - FAQ for OIG resources and Terraformer
- **COMPLETE_SOLUTION.md** - Complete solution overview
- **TESTING.md** - Testing guide
- **PROJECT_STRUCTURE.md** - This file

## 🔑 Key Files for GitHub

### Branch Protection
- `main` - Protected, requires PR approval
- `develop` - Integration branch
- `feature/*` - Feature branches

### Required Files
- ✅ README.md with badges
- ✅ LICENSE file
- ✅ Contributing guidelines
- ✅ Security policy
- ✅ Issue templates
- ✅ PR template
- ✅ GitHub Actions workflows

### Recommended Files
- ✅ CHANGELOG.md
- ✅ CODE_OF_CONDUCT.md
- ✅ CODEOWNERS
- ✅ SECURITY.md
