#!/usr/bin/env python3
"""
Manage Entitlement Settings for Okta Applications.

This script uses the Entitlement Settings API (Beta - December 2025) to enable
or disable entitlement management on applications.

Actions:
- list: List all apps and their entitlement management status
- enable: Enable entitlement management for specified app(s)
- disable: Disable entitlement management for specified app(s)
- status: Check entitlement management status for specified app(s)

Usage:
    # List all apps with entitlement management status
    python scripts/manage_entitlement_settings.py --action list

    # Check status for a specific app
    python scripts/manage_entitlement_settings.py --action status --app-id 0oaXXXXX

    # Enable entitlement management (dry-run)
    python scripts/manage_entitlement_settings.py --action enable --app-id 0oaXXXXX --dry-run

    # Enable entitlement management (apply)
    python scripts/manage_entitlement_settings.py --action enable --app-id 0oaXXXXX

    # Enable for multiple apps by label pattern
    python scripts/manage_entitlement_settings.py --action enable --app-label "Salesforce*"

    # Disable entitlement management
    python scripts/manage_entitlement_settings.py --action disable --app-id 0oaXXXXX

Environment Variables:
    OKTA_ORG_NAME   - Okta org name (e.g., dev-12345)
    OKTA_BASE_URL   - Okta base URL (e.g., okta.com)
    OKTA_API_TOKEN  - Okta API token with governance permissions

API Reference:
    https://developer.okta.com/docs/api/iga/openapi/governance.api/tag/Entitlement-Settings/

Note: This API is in Beta as of December 2025 (release 2025.12.0).
"""

import argparse
import fnmatch
import json
import os
import sys
import time
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.okta_api_manager import OktaAPIManager
except ImportError:
    # Fallback if running directly
    import requests

    class OktaAPIManager:
        """Minimal API manager for standalone execution."""

        def __init__(self, org_name: str, base_url: str, api_token: str):
            self.org_name = org_name
            self.base_url = f"https://{org_name}.{base_url}"
            self.governance_url = f"{self.base_url}/governance/api/v1"
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"SSWS {api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            })

        def _handle_rate_limit(self, response) -> None:
            """Handle rate limiting by waiting if needed."""
            if response.status_code == 429:
                reset_time = int(response.headers.get('X-Rate-Limit-Reset', time.time() + 60))
                wait_time = max(reset_time - time.time() + 1, 1)
                print(f"  Rate limited. Waiting {wait_time:.0f}s...")
                time.sleep(wait_time)


class EntitlementSettingsManager:
    """Manages entitlement settings for Okta applications."""

    # System apps that should never have entitlement management enabled
    SYSTEM_APPS = [
        "okta-iga-reviewer",
        "okta-flow-sso",
        "okta-access-requests-resource-catalog",
        "flow",
        "okta-atspoke-sso",
        "okta-admin-console",
        "okta-dashboard",
        "okta-browser-plugin",
    ]

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.api = OktaAPIManager(org_name, base_url, api_token)
        self.base_url = f"https://{org_name}.{base_url}"
        self.governance_url = f"{self.base_url}/governance/api/v1"

    def get_all_apps(self) -> List[Dict]:
        """Get all applications from Okta."""
        url = f"{self.base_url}/api/v1/apps"
        params = {"limit": 200}
        apps = []

        while url:
            response = self.api.session.get(url, params=params)
            if response.status_code == 429:
                self.api._handle_rate_limit(response)
                continue
            response.raise_for_status()
            apps.extend(response.json())

            # Handle pagination
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        return apps

    def get_app_by_id(self, app_id: str) -> Optional[Dict]:
        """Get a specific application by ID."""
        url = f"{self.base_url}/api/v1/apps/{app_id}"
        response = self.api.session.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def filter_apps_by_label(self, apps: List[Dict], pattern: str) -> List[Dict]:
        """Filter apps by label pattern (supports wildcards)."""
        return [
            app for app in apps
            if fnmatch.fnmatch(app.get("label", ""), pattern)
        ]

    def is_system_app(self, app: Dict) -> bool:
        """Check if an app is a system app that shouldn't be modified."""
        label = app.get("label", "").lower()
        name = app.get("name", "").lower()
        return any(
            sys_app.lower() in label or sys_app.lower() in name
            for sys_app in self.SYSTEM_APPS
        )

    def get_entitlement_settings(self, app_id: str) -> Optional[Dict]:
        """
        Get entitlement settings for an application.

        Returns the entitlement management status and configuration.
        """
        url = f"{self.governance_url}/entitlement-settings/{app_id}"
        response = self.api.session.get(url)

        if response.status_code == 404:
            # App doesn't have entitlement management enabled or not supported
            return {"enabled": False, "status": "not_configured"}
        elif response.status_code == 400:
            # API might not be available or app not eligible
            return {"enabled": False, "status": "not_eligible", "error": response.text}
        elif response.status_code == 429:
            self.api._handle_rate_limit(response)
            return self.get_entitlement_settings(app_id)

        if response.ok:
            data = response.json()
            return {"enabled": True, "status": "enabled", "data": data}

        return {"enabled": False, "status": "error", "error": response.text}

    def enable_entitlement_management(self, app_id: str, dry_run: bool = False) -> Dict:
        """
        Enable entitlement management for an application.

        Args:
            app_id: The Okta application ID
            dry_run: If True, only simulate the action

        Returns:
            Result dictionary with status and any error messages
        """
        if dry_run:
            return {
                "status": "dry_run",
                "message": f"Would enable entitlement management for app {app_id}"
            }

        # The API endpoint and payload structure (based on release notes)
        # This may need adjustment once full API docs are available
        url = f"{self.governance_url}/entitlement-settings"

        # Try different payload formats based on common Okta API patterns
        payload = {
            "resourceId": app_id,
            "resourceType": "APPLICATION",
            "enabled": True
        }

        response = self.api.session.post(url, json=payload)

        if response.status_code == 429:
            self.api._handle_rate_limit(response)
            return self.enable_entitlement_management(app_id, dry_run)

        if response.ok:
            return {
                "status": "success",
                "message": f"Entitlement management enabled for app {app_id}",
                "data": response.json() if response.text else {}
            }
        elif response.status_code == 409:
            return {
                "status": "already_enabled",
                "message": f"Entitlement management already enabled for app {app_id}"
            }
        elif response.status_code == 400:
            # Try alternative endpoint format
            url_alt = f"{self.governance_url}/entitlement-settings/{app_id}"
            payload_alt = {"enabled": True}
            response_alt = self.api.session.put(url_alt, json=payload_alt)

            if response_alt.ok:
                return {
                    "status": "success",
                    "message": f"Entitlement management enabled for app {app_id}",
                    "data": response_alt.json() if response_alt.text else {}
                }

            return {
                "status": "error",
                "message": f"Failed to enable: {response.status_code}",
                "error": response.text
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to enable: {response.status_code}",
                "error": response.text
            }

    def disable_entitlement_management(self, app_id: str, dry_run: bool = False) -> Dict:
        """
        Disable entitlement management for an application.

        WARNING: Disabling entitlement management may cause data loss.
        See Okta documentation for implications.

        Args:
            app_id: The Okta application ID
            dry_run: If True, only simulate the action

        Returns:
            Result dictionary with status and any error messages
        """
        if dry_run:
            return {
                "status": "dry_run",
                "message": f"Would disable entitlement management for app {app_id}"
            }

        url = f"{self.governance_url}/entitlement-settings/{app_id}"

        # Try DELETE first
        response = self.api.session.delete(url)

        if response.status_code == 429:
            self.api._handle_rate_limit(response)
            return self.disable_entitlement_management(app_id, dry_run)

        if response.ok or response.status_code == 204:
            return {
                "status": "success",
                "message": f"Entitlement management disabled for app {app_id}"
            }
        elif response.status_code == 404:
            return {
                "status": "not_enabled",
                "message": f"Entitlement management was not enabled for app {app_id}"
            }
        elif response.status_code == 400:
            # Try PUT with enabled=false
            payload = {"enabled": False}
            response_put = self.api.session.put(url, json=payload)

            if response_put.ok:
                return {
                    "status": "success",
                    "message": f"Entitlement management disabled for app {app_id}"
                }

            return {
                "status": "error",
                "message": f"Failed to disable: {response.status_code}",
                "error": response.text
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to disable: {response.status_code}",
                "error": response.text
            }


def print_apps_table(apps: List[Dict], settings: Dict[str, Dict]):
    """Print apps in a formatted table with entitlement status."""
    print(f"\n{'ID':<25} {'Label':<40} {'Entitlement Mgmt':<20} {'Status':<10}")
    print("=" * 100)

    for app in apps:
        app_id = app.get('id', 'N/A')
        label = app.get('label', 'N/A')[:38]
        status = app.get('status', 'N/A')

        setting = settings.get(app_id, {})
        em_status = setting.get('status', 'unknown')

        # Color-code status
        if em_status == 'enabled':
            em_display = 'ENABLED'
        elif em_status == 'not_configured':
            em_display = 'Not Enabled'
        elif em_status == 'not_eligible':
            em_display = 'Not Eligible'
        else:
            em_display = em_status

        print(f"{app_id:<25} {label:<40} {em_display:<20} {status:<10}")

    print("=" * 100)


def main():
    parser = argparse.ArgumentParser(
        description="Manage Entitlement Settings for Okta Applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--action",
        choices=["list", "status", "enable", "disable"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--app-id",
        help="Okta application ID (for status/enable/disable)"
    )
    parser.add_argument(
        "--app-label",
        help="Application label pattern (supports wildcards like 'Sales*')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--include-system-apps",
        action="store_true",
        help="Include system apps in operations (not recommended)"
    )

    args = parser.parse_args()

    # Get credentials from environment
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "okta.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN environment variables required")
        sys.exit(1)

    manager = EntitlementSettingsManager(org_name, base_url, api_token)

    # Handle actions
    if args.action == "list":
        print(f"Fetching applications from {org_name}...")
        apps = manager.get_all_apps()

        # Filter out system apps unless specifically included
        if not args.include_system_apps:
            apps = [app for app in apps if not manager.is_system_app(app)]

        print(f"Checking entitlement settings for {len(apps)} apps...")
        settings = {}
        for app in apps:
            settings[app['id']] = manager.get_entitlement_settings(app['id'])

        if args.json:
            output = [
                {
                    "id": app['id'],
                    "label": app.get('label'),
                    "signOnMode": app.get('signOnMode'),
                    "status": app.get('status'),
                    "entitlementSettings": settings.get(app['id'], {})
                }
                for app in apps
            ]
            print(json.dumps(output, indent=2))
        else:
            print_apps_table(apps, settings)
            enabled_count = sum(1 for s in settings.values() if s.get('status') == 'enabled')
            print(f"\nTotal: {len(apps)} apps, {enabled_count} with entitlement management enabled")

    elif args.action == "status":
        if not args.app_id and not args.app_label:
            print("Error: --app-id or --app-label required for status action")
            sys.exit(1)

        target_apps = []
        if args.app_id:
            app = manager.get_app_by_id(args.app_id)
            if app:
                target_apps = [app]
            else:
                print(f"Error: App with ID {args.app_id} not found")
                sys.exit(1)
        elif args.app_label:
            all_apps = manager.get_all_apps()
            target_apps = manager.filter_apps_by_label(all_apps, args.app_label)
            if not target_apps:
                print(f"No apps found matching pattern: {args.app_label}")
                sys.exit(1)

        for app in target_apps:
            settings = manager.get_entitlement_settings(app['id'])
            if args.json:
                print(json.dumps({
                    "app_id": app['id'],
                    "label": app.get('label'),
                    "entitlementSettings": settings
                }, indent=2))
            else:
                print(f"\nApp: {app.get('label')} ({app['id']})")
                print(f"  Status: {settings.get('status')}")
                if settings.get('data'):
                    print(f"  Settings: {json.dumps(settings['data'], indent=4)}")
                if settings.get('error'):
                    print(f"  Error: {settings['error']}")

    elif args.action in ["enable", "disable"]:
        if not args.app_id and not args.app_label:
            print("Error: --app-id or --app-label required for enable/disable action")
            sys.exit(1)

        target_apps = []
        if args.app_id:
            app = manager.get_app_by_id(args.app_id)
            if app:
                target_apps = [app]
            else:
                print(f"Error: App with ID {args.app_id} not found")
                sys.exit(1)
        elif args.app_label:
            all_apps = manager.get_all_apps()
            target_apps = manager.filter_apps_by_label(all_apps, args.app_label)
            if not target_apps:
                print(f"No apps found matching pattern: {args.app_label}")
                sys.exit(1)

        # Filter system apps
        if not args.include_system_apps:
            filtered_apps = [app for app in target_apps if not manager.is_system_app(app)]
            skipped = len(target_apps) - len(filtered_apps)
            if skipped > 0:
                print(f"Skipping {skipped} system app(s)")
            target_apps = filtered_apps

        if args.dry_run:
            print(f"\n[DRY RUN] Would {args.action} entitlement management for:")

        results = {"success": 0, "errors": 0, "skipped": 0}

        for app in target_apps:
            app_label = app.get('label', app['id'])

            if args.action == "enable":
                result = manager.enable_entitlement_management(app['id'], dry_run=args.dry_run)
            else:
                result = manager.disable_entitlement_management(app['id'], dry_run=args.dry_run)

            status = result.get('status')
            if status in ['success', 'dry_run', 'already_enabled', 'not_enabled']:
                print(f"  {'[DRY RUN] ' if args.dry_run else ''}{'Enabled' if args.action == 'enable' else 'Disabled'}: {app_label}")
                results["success"] += 1
            else:
                print(f"  ERROR: {app_label} - {result.get('message', 'Unknown error')}")
                if result.get('error'):
                    print(f"    Details: {result['error'][:200]}")
                results["errors"] += 1

        # Summary
        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary:")
        print(f"  Success: {results['success']}")
        print(f"  Errors: {results['errors']}")

        if args.dry_run:
            print("\n[DRY RUN] No changes were made. Remove --dry-run to apply.")

        sys.exit(0 if results["errors"] == 0 else 1)


if __name__ == "__main__":
    main()
