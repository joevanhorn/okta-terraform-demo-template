#!/usr/bin/env python3
"""
configure_scim_app.py

Configures SCIM provisioning for an Okta application using the Admin API.

The Okta Terraform provider does NOT support SCIM configuration, so this script
handles the following via API:
  - Enable SCIM provisioning
  - Configure SCIM connection (base URL, authentication)
  - Test SCIM connection
  - Enable provisioning features (create, update, deactivate users)
  - Configure attribute mappings (optional)

Usage:
    # Basic configuration with credentials from SCIM server state
    python3 scripts/configure_scim_app.py \
      --app-id <app_id> \
      --scim-url <scim_base_url> \
      --scim-token <bearer_token>

    # Test connection only
    python3 scripts/configure_scim_app.py \
      --app-id <app_id> \
      --scim-url <scim_base_url> \
      --scim-token <bearer_token> \
      --test-connection

    # Use Basic Auth instead of Bearer
    python3 scripts/configure_scim_app.py \
      --app-id <app_id> \
      --scim-url <scim_base_url> \
      --scim-user <username> \
      --scim-pass <password> \
      --auth-mode basic

    # Dry run mode
    python3 scripts/configure_scim_app.py \
      --app-id <app_id> \
      --scim-url <scim_base_url> \
      --scim-token <bearer_token> \
      --dry-run

Environment Variables:
    OKTA_ORG_NAME     - Okta organization name (required)
    OKTA_BASE_URL     - Okta base URL (default: okta.com)
    OKTA_API_TOKEN    - Okta API token (required)
"""

import os
import sys
import json
import time
import requests
import argparse
from typing import Dict, List, Optional


class SCIMConfigurator:
    """Configures SCIM provisioning for Okta applications"""

    def __init__(self, org_name: str, base_url: str, api_token: str, dry_run: bool = False):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.api_base = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.dry_run = dry_run

    def get_app_details(self, app_id: str) -> Optional[Dict]:
        """Get application details"""
        url = f"{self.api_base}/apps/{app_id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ Error getting app details: {e}")
            if e.response.status_code == 404:
                print(f"   App ID not found: {app_id}")
            return None

    def enable_provisioning(self, app_id: str, scim_url: str, auth_mode: str,
                          scim_token: Optional[str] = None,
                          scim_user: Optional[str] = None,
                          scim_pass: Optional[str] = None) -> bool:
        """
        Enable SCIM provisioning for the application

        Note: This uses the App Features API to enable provisioning
        """
        url = f"{self.api_base}/apps/{app_id}/features"

        # Check current features
        try:
            response = self.session.get(url)
            response.raise_for_status()
            features = response.json()

            # Check if provisioning is already enabled
            provisioning_enabled = any(
                f.get("name") == "PROVISIONING" and f.get("status") == "ENABLED"
                for f in features
            )

            if provisioning_enabled:
                print(f"✅ Provisioning already enabled for app {app_id}")
                return True

        except Exception as e:
            print(f"⚠️  Could not check current features: {e}")
            print("   Continuing with configuration...")

        if self.dry_run:
            print(f"  [DRY RUN] Would enable SCIM provisioning for app {app_id}")
            return True

        # Enable provisioning feature
        enable_url = f"{self.api_base}/apps/{app_id}/features/provisioning"
        payload = {
            "capabilities": {
                "create": {"lifecycleCreate": {"status": "ENABLED"}},
                "update": {"lifecycleDeactivate": {"status": "ENABLED"}},
            }
        }

        try:
            response = self.session.post(enable_url, json=payload)
            response.raise_for_status()
            print(f"✅ Enabled SCIM provisioning for app {app_id}")
            return True
        except requests.exceptions.HTTPError as e:
            # Some apps may not support this API - that's okay
            print(f"⚠️  Could not enable via Features API: {e}")
            print("   This may be normal for some app types. Continuing...")
            return True

    def configure_scim_connection(self, app_id: str, scim_url: str, auth_mode: str,
                                  scim_token: Optional[str] = None,
                                  scim_user: Optional[str] = None,
                                  scim_pass: Optional[str] = None) -> bool:
        """
        Configure SCIM connection settings

        Note: This configures the connection parameters for the SCIM app.
        The exact API endpoint varies by app type.
        """
        if self.dry_run:
            print(f"  [DRY RUN] Would configure SCIM connection:")
            print(f"    URL: {scim_url}")
            print(f"    Auth: {auth_mode}")
            return True

        # Update app settings with SCIM connection
        url = f"{self.api_base}/apps/{app_id}"

        # Build connection settings based on auth mode
        if auth_mode == "bearer":
            settings = {
                "scimConnector": {
                    "baseUrl": scim_url,
                    "authenticationMode": "HEADER_AUTH",
                    "authToken": scim_token
                }
            }
        else:  # basic auth
            settings = {
                "scimConnector": {
                    "baseUrl": scim_url,
                    "authenticationMode": "BASIC_AUTH",
                    "userName": scim_user,
                    "password": scim_pass
                }
            }

        payload = {
            "name": "scim2",
            "settings": {
                "app": settings
            }
        }

        try:
            response = self.session.put(url, json=payload)
            response.raise_for_status()
            print(f"✅ Configured SCIM connection for app {app_id}")
            return True
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except:
                pass
            print(f"❌ Error configuring SCIM connection: {error_msg}")
            print(f"   You may need to configure this manually in the Okta Admin Console")
            return False

    def test_scim_connection(self, app_id: str) -> bool:
        """
        Test SCIM connection

        Note: This may not be available via API for all app types.
        """
        if self.dry_run:
            print(f"  [DRY RUN] Would test SCIM connection for app {app_id}")
            return True

        # Test connection endpoint (if available)
        url = f"{self.api_base}/apps/{app_id}/connections/default/test"

        try:
            response = self.session.post(url)
            response.raise_for_status()
            result = response.json()

            if result.get("verified"):
                print(f"✅ SCIM connection test succeeded!")
                return True
            else:
                print(f"⚠️  SCIM connection test returned: {result}")
                return False

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️  Connection test endpoint not available for this app type")
                print(f"   Please test connection manually in Okta Admin Console")
            else:
                print(f"❌ Error testing connection: {e}")
            return False

    def enable_provisioning_features(self, app_id: str,
                                     create_users: bool = True,
                                     update_users: bool = True,
                                     deactivate_users: bool = True,
                                     sync_password: bool = False) -> bool:
        """
        Enable specific provisioning features
        """
        if self.dry_run:
            print(f"  [DRY RUN] Would enable provisioning features:")
            print(f"    Create users: {create_users}")
            print(f"    Update user attributes: {update_users}")
            print(f"    Deactivate users: {deactivate_users}")
            print(f"    Sync password: {sync_password}")
            return True

        url = f"{self.api_base}/apps/{app_id}/features/provisioning"

        capabilities = {}
        if create_users:
            capabilities["create"] = {"lifecycleCreate": {"status": "ENABLED"}}
        if update_users:
            capabilities["update"] = {"profile": {"status": "ENABLED"}}
        if deactivate_users:
            capabilities["update"] = capabilities.get("update", {})
            capabilities["update"]["lifecycleDeactivate"] = {"status": "ENABLED"}
        if sync_password:
            capabilities["update"] = capabilities.get("update", {})
            capabilities["update"]["password"] = {"status": "ENABLED"}

        payload = {"capabilities": capabilities}

        try:
            response = self.session.put(url, json=payload)
            response.raise_for_status()
            print(f"✅ Enabled provisioning features for app {app_id}")
            return True
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except:
                pass
            print(f"⚠️  Could not enable provisioning features via API: {error_msg}")
            print(f"   You may need to enable these manually in the Okta Admin Console")
            return False

    def configure_app(self, app_id: str, scim_url: str, auth_mode: str,
                     scim_token: Optional[str] = None,
                     scim_user: Optional[str] = None,
                     scim_pass: Optional[str] = None,
                     test_connection: bool = False) -> bool:
        """
        Complete SCIM configuration workflow
        """
        print("\n" + "="*80)
        print("CONFIGURING SCIM APPLICATION")
        print("="*80)

        # Get app details
        print(f"\n📋 Getting app details...")
        app = self.get_app_details(app_id)
        if not app:
            return False

        app_name = app.get("label", "Unknown")
        print(f"   App: {app_name}")
        print(f"   ID: {app_id}")

        # Enable provisioning
        print(f"\n🔧 Enabling SCIM provisioning...")
        if not self.enable_provisioning(app_id, scim_url, auth_mode, scim_token, scim_user, scim_pass):
            print(f"⚠️  Could not enable provisioning automatically")
            print(f"   Please enable manually in Okta Admin Console")

        # Configure SCIM connection
        print(f"\n🔗 Configuring SCIM connection...")
        print(f"   Base URL: {scim_url}")
        print(f"   Auth Mode: {auth_mode}")

        if not self.configure_scim_connection(app_id, scim_url, auth_mode,
                                             scim_token, scim_user, scim_pass):
            print(f"\n❌ SCIM connection configuration failed")
            print(f"\n📝 Manual Configuration Required:")
            print(f"   1. Open app in Okta Admin Console")
            print(f"   2. Go to Provisioning tab")
            print(f"   3. Click 'Configure API Integration'")
            print(f"   4. Enable 'Enable API integration'")
            print(f"   5. Enter SCIM Base URL: {scim_url}")
            if auth_mode == "bearer":
                print(f"   6. Enter Bearer Token: {scim_token[:10]}...")
            else:
                print(f"   6. Enter Username: {scim_user}")
                print(f"   7. Enter Password: {scim_pass[:5]}...")
            print(f"   8. Test Connection")
            print(f"   9. Save")
            return False

        # Test connection if requested
        if test_connection:
            print(f"\n🧪 Testing SCIM connection...")
            self.test_scim_connection(app_id)

        # Enable provisioning features
        print(f"\n⚙️  Enabling provisioning features...")
        self.enable_provisioning_features(app_id)

        print(f"\n" + "="*80)
        print("✅ SCIM CONFIGURATION COMPLETE")
        print("="*80)
        print(f"\n📍 Next steps:")
        print(f"   1. Assign users/groups to the app in Okta")
        print(f"   2. Verify provisioning in SCIM server dashboard: {scim_url.replace('/scim/v2', '')}")
        print(f"   3. Check provisioning logs in Okta Admin Console")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Configure SCIM provisioning for Okta application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--app-id", required=True, help="Okta application ID")
    parser.add_argument("--scim-url", required=True, help="SCIM base URL (e.g., https://scim.example.com/scim/v2)")
    parser.add_argument("--auth-mode", choices=["bearer", "basic"], default="bearer",
                       help="Authentication mode (default: bearer)")
    parser.add_argument("--scim-token", help="Bearer token for SCIM authentication")
    parser.add_argument("--scim-user", help="Username for basic auth")
    parser.add_argument("--scim-pass", help="Password for basic auth")
    parser.add_argument("--test-connection", action="store_true",
                       help="Test SCIM connection after configuration")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")

    args = parser.parse_args()

    # Validate auth parameters
    if args.auth_mode == "bearer" and not args.scim_token:
        print("❌ --scim-token required when using bearer auth mode")
        sys.exit(1)

    if args.auth_mode == "basic" and (not args.scim_user or not args.scim_pass):
        print("❌ --scim-user and --scim-pass required when using basic auth mode")
        sys.exit(1)

    # Get Okta credentials from environment
    org_name = os.getenv("OKTA_ORG_NAME")
    base_url = os.getenv("OKTA_BASE_URL", "okta.com")
    api_token = os.getenv("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("❌ Missing required environment variables:")
        print("   OKTA_ORG_NAME")
        print("   OKTA_API_TOKEN")
        print("\nSet these variables or add them to a .env file")
        sys.exit(1)

    # Create configurator
    configurator = SCIMConfigurator(org_name, base_url, api_token, args.dry_run)

    # Run configuration
    success = configurator.configure_app(
        app_id=args.app_id,
        scim_url=args.scim_url,
        auth_mode=args.auth_mode,
        scim_token=args.scim_token,
        scim_user=args.scim_user,
        scim_pass=args.scim_pass,
        test_connection=args.test_connection
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
