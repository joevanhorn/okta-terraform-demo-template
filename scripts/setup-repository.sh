#!/bin/bash
set -e

# Repository Setup Script
# Configures GitHub repository settings for the Okta Terraform template

echo "🚀 Okta Terraform Template - Repository Setup"
echo "=============================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is not installed"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "📦 Repository: $REPO"
echo ""

# Step 1: Enable workflow permissions
echo "⚙️  Step 1: Enabling workflow permissions..."
gh api repos/$REPO/actions/permissions \
  --method PUT \
  -f default_workflow_permissions=write \
  -f can_approve_pull_request_reviews=true \
  > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Workflow permissions: Read and write"
    echo "   ✅ Allow PR creation: Enabled"
else
    echo "   ⚠️  Failed to update permissions (may require admin access)"
fi
echo ""

# Step 2: Create labels
echo "🏷️  Step 2: Creating repository labels..."

# Create template-sync label
if gh label create template-sync \
    --description "Automated template sync pull request" \
    --color "0366d6" \
    > /dev/null 2>&1; then
    echo "   ✅ Created label: template-sync (blue)"
else
    echo "   ℹ️  Label 'template-sync' already exists"
fi

# Create maintenance label
if gh label create maintenance \
    --description "Repository maintenance" \
    --color "fbca04" \
    > /dev/null 2>&1; then
    echo "   ✅ Created label: maintenance (yellow)"
else
    echo "   ℹ️  Label 'maintenance' already exists"
fi
echo ""

# Step 3: Summary
echo "✨ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Set up AWS backend (if not already done): cd aws-backend && terraform apply"
echo "2. Create GitHub Environment: Settings → Environments → New environment"
echo "3. Add Okta secrets: OKTA_API_TOKEN, OKTA_ORG_NAME, OKTA_BASE_URL"
echo "4. Create your first environment: mkdir -p environments/mycompany/{terraform,imports,config}"
echo ""
echo "📚 See TEMPLATE_SETUP.md for detailed instructions"
