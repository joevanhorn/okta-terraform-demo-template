#!/bin/bash
# import_okta_resources.sh
# Automated script to import existing Okta resources using Terraformer

set -e

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
IMPORT_DIR="imported/${TIMESTAMP}"
GENERATED_DIR="generated"
BACKUP_DIR="backups/${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v terraformer &> /dev/null; then
        print_error "Terraformer not found. Please install it first."
        exit 1
    fi
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install it first."
        exit 1
    fi
    
    if [ -z "$OKTA_API_TOKEN" ] || [ -z "$OKTA_ORG_NAME" ]; then
        print_error "OKTA_API_TOKEN and OKTA_ORG_NAME environment variables must be set."
        exit 1
    fi
    
    print_info "Prerequisites check passed ✓"
}

# Backup existing generated directory
backup_existing() {
    if [ -d "$GENERATED_DIR" ]; then
        print_info "Backing up existing generated directory..."
        mkdir -p "$BACKUP_DIR"
        mv "$GENERATED_DIR" "$BACKUP_DIR/"
        print_info "Backup created at $BACKUP_DIR"
    fi
}

# Import specific resource type
import_resource() {
    local resource_type=$1
    local description=$2
    
    print_info "Importing $description..."
    
    if terraformer import okta --resources="$resource_type" 2>&1 | tee -a import.log; then
        print_info "$description imported successfully ✓"
        return 0
    else
        print_warn "$description import failed or no resources found"
        return 1
    fi
}

# Clean up generated files
cleanup_generated() {
    print_info "Cleaning up generated files..."

    # Check if generated directory exists
    if [ ! -d "$GENERATED_DIR" ]; then
        print_warn "No generated directory found. Terraformer may not have created any files."
        return 0
    fi

    # Remove empty directories
    find "$GENERATED_DIR" -type d -empty -delete 2>/dev/null || true

    # Count imported resources
    local resource_count=$(find "$GENERATED_DIR" -name "*.tf" 2>/dev/null | wc -l)
    print_info "Total .tf files generated: $resource_count"
}

# Organize imported resources
organize_resources() {
    print_info "Organizing imported resources..."

    # Check if generated directory exists
    if [ ! -d "$GENERATED_DIR" ]; then
        print_warn "No generated directory found. Skipping organization."
        return 0
    fi

    mkdir -p "$IMPORT_DIR"/{users,groups,apps,policies,auth_servers,network,idps}

    # Move resources to organized structure
    [ -d "$GENERATED_DIR/okta/okta_user" ] && cp -r "$GENERATED_DIR/okta/okta_user"/* "$IMPORT_DIR/users/" 2>/dev/null || true
    [ -d "$GENERATED_DIR/okta/okta_group" ] && cp -r "$GENERATED_DIR/okta/okta_group"/* "$IMPORT_DIR/groups/" 2>/dev/null || true
    [ -d "$GENERATED_DIR/okta/okta_app_oauth" ] && cp -r "$GENERATED_DIR/okta/okta_app_oauth"/* "$IMPORT_DIR/apps/" 2>/dev/null || true
    [ -d "$GENERATED_DIR/okta/okta_app_saml" ] && cp -r "$GENERATED_DIR/okta/okta_app_saml"/* "$IMPORT_DIR/apps/" 2>/dev/null || true
    [ -d "$GENERATED_DIR/okta/okta_auth_server" ] && cp -r "$GENERATED_DIR/okta/okta_auth_server"/* "$IMPORT_DIR/auth_servers/" 2>/dev/null || true
    [ -d "$GENERATED_DIR/okta/okta_policy_mfa" ] && cp -r "$GENERATED_DIR/okta/okta_policy_mfa"/* "$IMPORT_DIR/policies/" 2>/dev/null || true
    [ -d "$GENERATED_DIR/okta/okta_network_zone" ] && cp -r "$GENERATED_DIR/okta/okta_network_zone"/* "$IMPORT_DIR/network/" 2>/dev/null || true

    print_info "Resources organized in $IMPORT_DIR"
}

# Generate summary report
generate_report() {
    local report_file="$IMPORT_DIR/import_report_${TIMESTAMP}.md"
    
    print_info "Generating import report..."
    
    cat > "$report_file" <<EOF
# Okta Terraformer Import Report
**Date:** $(date)
**Okta Org:** ${OKTA_ORG_NAME}

## Import Summary

| Resource Type | Count | Location |
|---------------|-------|----------|
EOF
    
    # Count resources by type
    for dir in "$IMPORT_DIR"/*; do
        if [ -d "$dir" ]; then
            local dir_name=$(basename "$dir")
            local tf_count=$(find "$dir" -name "*.tf" -type f 2>/dev/null | wc -l)
            if [ "$tf_count" -gt 0 ]; then
                echo "| $dir_name | $tf_count | $dir |" >> "$report_file"
            fi
        fi
    done
    
    cat >> "$report_file" <<EOF

## Next Steps

1. Review generated Terraform files in \`$IMPORT_DIR\`
2. Clean up unnecessary null values and defaults
3. Rename resources from \`tfer--\` prefix to meaningful names
4. Add variable definitions where appropriate
5. Organize into modules if needed
6. Test with \`terraform plan\` before applying

## Files Generated

\`\`\`
$(tree "$IMPORT_DIR" || find "$IMPORT_DIR" -type f)
\`\`\`

## Import Log

See \`import.log\` for detailed import output.
EOF
    
    print_info "Report generated: $report_file"
    cat "$report_file"
}

# Main execution
main() {
    echo "========================================="
    echo "  Okta Terraformer Import Script"
    echo "========================================="
    echo ""
    
    check_prerequisites
    
    # Create import log
    echo "Import started at $(date)" > import.log
    
    # Backup existing
    backup_existing

    # Create provider configuration for Terraformer
    print_info "Creating Okta provider configuration..."
    cat > provider.tf <<EOF
terraform {
  required_providers {
    okta = {
      source  = "okta/okta"
      version = ">= 7.0.0, < 8.0.0"
    }
  }
}

provider "okta" {
  org_name  = "${OKTA_ORG_NAME}"
  base_url  = "${OKTA_BASE_URL}"
  api_token = "${OKTA_API_TOKEN}"
}
EOF

    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Import resources
    print_info "Starting resource import..."
    echo ""
    
    import_resource "okta_user" "Users"
    import_resource "okta_group" "Groups"
    import_resource "okta_group_rule" "Group Rules"
    import_resource "okta_app_oauth" "OAuth/OIDC Applications"
    import_resource "okta_app_saml" "SAML Applications"
    import_resource "okta_auth_server" "Authorization Servers"
    import_resource "okta_auth_server_policy" "Auth Server Policies"
    import_resource "okta_auth_server_claim" "Auth Server Claims"
    import_resource "okta_auth_server_scope" "Auth Server Scopes"
    import_resource "okta_policy_mfa" "MFA Policies"
    import_resource "okta_policy_password" "Password Policies"
    import_resource "okta_policy_signon" "Sign-On Policies"
    import_resource "okta_network_zone" "Network Zones"
    import_resource "okta_trusted_origin" "Trusted Origins"
    import_resource "okta_idp_saml" "SAML Identity Providers"
    import_resource "okta_user_schema" "User Schema"
    
    echo ""
    cleanup_generated
    organize_resources
    generate_report
    
    echo ""
    print_info "Import completed successfully! ✓"
    print_info "Review the files in: $IMPORT_DIR"
    print_info "Import log saved to: import.log"
    
    echo ""
    echo "========================================="
}

# Run main function
main "$@"
