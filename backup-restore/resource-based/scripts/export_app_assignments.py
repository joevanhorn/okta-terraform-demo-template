#!/usr/bin/env python3
"""
Export Okta application assignments for backup and restore.

This script exports user and group assignments to applications from an Okta org.

Usage:
    # Export all app assignments
    python scripts/export_app_assignments.py --output backups/app_assignments.json

    # Exclude system apps
    python scripts/export_app_assignments.py --output assignments.json --exclude-system

    # Export assignments for specific app
    python scripts/export_app_assignments.py --output assignments.json --app-label "Salesforce"

Environment Variables:
    OKTA_ORG_NAME   - Okta org name
    OKTA_BASE_URL   - Okta base URL (default: okta.com)
    OKTA_API_TOKEN  - Okta API token
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests


# System apps to exclude by default
SYSTEM_APPS = [
    'okta-iga-reviewer',
    'okta-flow-sso',
    'okta-access-requests-resource-catalog',
    'flow',
    'okta-atspoke-sso',
    'Okta Admin Console',
    'Okta Browser Plugin',
    'Okta Dashboard',
]


class OktaClient:
    """Client for Okta API operations."""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.api_url = f"{self.base_url}/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"SSWS {api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.rate_limit_remaining = 1000

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limiting."""
        if 'X-Rate-Limit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-Rate-Limit-Remaining'])

        if response.status_code == 429:
            reset_time = int(response.headers.get('X-Rate-Limit-Reset', time.time() + 60))
            wait_time = max(reset_time - time.time() + 1, 1)
            print(f"  Rate limited. Waiting {wait_time:.0f}s...")
            time.sleep(wait_time)
        elif self.rate_limit_remaining < 10:
            time.sleep(0.5)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make request with rate limit handling."""
        max_retries = 3
        for attempt in range(max_retries):
            response = self.session.request(method, url, **kwargs)
            self._handle_rate_limit(response)
            if response.status_code == 429:
                continue
            return response
        return response

    def get_all_apps(self) -> List[Dict]:
        """Get all applications from the org."""
        print("Fetching applications...")
        url = f"{self.api_url}/apps"
        params = {"limit": 200}

        apps = []
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  Error: {response.status_code} - {response.text}")
                break

            apps.extend(response.json())
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  Found {len(apps)} applications")
        return apps

    def get_app_users(self, app_id: str) -> List[Dict]:
        """Get user assignments for an application."""
        url = f"{self.api_url}/apps/{app_id}/users"
        params = {"limit": 200}

        users = []
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                break
            users.extend(response.json())
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        return users

    def get_app_groups(self, app_id: str) -> List[Dict]:
        """Get group assignments for an application."""
        url = f"{self.api_url}/apps/{app_id}/groups"
        params = {"limit": 200}

        groups = []
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                break
            groups.extend(response.json())
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        return groups

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by ID."""
        url = f"{self.api_url}/users/{user_id}"
        response = self._make_request("GET", url)
        if response.ok:
            return response.json().get('profile', {})
        return None

    def get_group_profile(self, group_id: str) -> Optional[Dict]:
        """Get group profile by ID."""
        url = f"{self.api_url}/groups/{group_id}"
        response = self._make_request("GET", url)
        if response.ok:
            return response.json().get('profile', {})
        return None


def is_system_app(app: Dict) -> bool:
    """Check if app is a system app."""
    label = app.get('label', '')
    name = app.get('name', '')

    # Check against known system apps
    for system_app in SYSTEM_APPS:
        if system_app.lower() in label.lower() or system_app.lower() in name.lower():
            return True

    # Check for Okta internal apps
    if app.get('name', '').startswith('okta_'):
        return True

    return False


def export_app_assignments(
    client: OktaClient,
    output_file: str,
    exclude_system: bool = True,
    app_filter: Optional[str] = None,
    verbose: bool = False
) -> Dict:
    """Export application assignments to JSON file."""
    apps = client.get_all_apps()

    # Filter apps
    if exclude_system:
        original_count = len(apps)
        apps = [a for a in apps if not is_system_app(a)]
        print(f"  Excluded {original_count - len(apps)} system apps")

    if app_filter:
        apps = [a for a in apps if app_filter.lower() in a.get('label', '').lower()]
        print(f"  Filtered to {len(apps)} apps matching '{app_filter}'")

    if not apps:
        print("No applications to export.")
        return {}

    # Build assignment data
    print(f"\nExporting assignments for {len(apps)} applications...")
    assignments = {
        'metadata': {
            'org_name': client.org_name,
            'exported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'app_count': len(apps),
        },
        'applications': []
    }

    total_user_assignments = 0
    total_group_assignments = 0

    for i, app in enumerate(apps, 1):
        app_id = app.get('id')
        app_label = app.get('label', '')

        if verbose:
            print(f"  [{i}/{len(apps)}] {app_label}")

        app_data = {
            'id': app_id,
            'label': app_label,
            'name': app.get('name', ''),
            'status': app.get('status', ''),
            'sign_on_mode': app.get('signOnMode', ''),
            'user_assignments': [],
            'group_assignments': [],
        }

        # Get user assignments
        users = client.get_app_users(app_id)
        for user in users:
            user_id = user.get('id')
            profile = user.get('profile', {})
            credentials = user.get('credentials', {})

            # Get user's email from profile or fetch it
            email = profile.get('email') or credentials.get('userName', '')
            if not email:
                user_profile = client.get_user_profile(user_id)
                if user_profile:
                    email = user_profile.get('email', '')

            app_data['user_assignments'].append({
                'user_id': user_id,
                'email': email,
                'status': user.get('status', ''),
                'scope': user.get('scope', ''),
                'profile': profile if profile else None,
            })

        # Get group assignments
        groups = client.get_app_groups(app_id)
        for group in groups:
            group_id = group.get('id')
            group_profile = client.get_group_profile(group_id)
            group_name = group_profile.get('name', '') if group_profile else ''

            app_data['group_assignments'].append({
                'group_id': group_id,
                'group_name': group_name,
                'priority': group.get('priority'),
                'profile': group.get('profile') if group.get('profile') else None,
            })

        total_user_assignments += len(app_data['user_assignments'])
        total_group_assignments += len(app_data['group_assignments'])

        if app_data['user_assignments'] or app_data['group_assignments']:
            assignments['applications'].append(app_data)

        if not verbose and i % 10 == 0:
            print(f"  Processed {i}/{len(apps)} apps")

    # Update metadata
    assignments['metadata']['total_user_assignments'] = total_user_assignments
    assignments['metadata']['total_group_assignments'] = total_group_assignments
    assignments['metadata']['apps_with_assignments'] = len(assignments['applications'])

    # Write output
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(assignments, f, indent=2)

    # Summary
    print(f"\nExport complete!")
    print(f"  Applications processed: {len(apps)}")
    print(f"  Apps with assignments: {len(assignments['applications'])}")
    print(f"  Total user assignments: {total_user_assignments}")
    print(f"  Total group assignments: {total_group_assignments}")
    print(f"  Output file: {output_file}")

    return assignments


def main():
    parser = argparse.ArgumentParser(
        description="Export Okta application assignments for backup"
    )
    parser.add_argument("--output", "-o", required=True,
                        help="Output JSON file path")
    parser.add_argument("--exclude-system", action="store_true", default=True,
                        help="Exclude system applications (default: True)")
    parser.add_argument("--include-system", action="store_true",
                        help="Include system applications")
    parser.add_argument("--app-label", type=str,
                        help="Filter to apps matching this label")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Get Okta credentials
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "okta.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN environment variables required")
        sys.exit(1)

    print(f"Exporting app assignments from: {org_name}.{base_url}")

    client = OktaClient(org_name, base_url, api_token)

    exclude_system = not args.include_system

    assignments = export_app_assignments(
        client,
        args.output,
        exclude_system=exclude_system,
        app_filter=args.app_label,
        verbose=args.verbose
    )

    return 0 if assignments else 1


if __name__ == "__main__":
    sys.exit(main())
