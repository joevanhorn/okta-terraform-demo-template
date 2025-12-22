#!/usr/bin/env python3
"""
Export Okta users to CSV format for backup and restore.

This script exports all users from an Okta org to a CSV file that is
compatible with the users_from_csv.tf.example Terraform pattern.

Usage:
    # Export all active users
    python scripts/export_users_to_csv.py --output backups/users.csv

    # Include deprovisioned users
    python scripts/export_users_to_csv.py --output users.csv --include-deprovisioned

    # Export users from specific group
    python scripts/export_users_to_csv.py --output users.csv --group "Engineering"

Environment Variables:
    OKTA_ORG_NAME   - Okta org name
    OKTA_BASE_URL   - Okta base URL (default: okta.com)
    OKTA_API_TOKEN  - Okta API token
"""

import argparse
import csv
import json
import os
import sys
import time
from typing import Dict, List, Optional, Set

import requests


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

    def get_all_users(self, include_deprovisioned: bool = False) -> List[Dict]:
        """Get all users from the org."""
        print("Fetching users...")
        url = f"{self.api_url}/users"
        params = {"limit": 200}

        if not include_deprovisioned:
            # Exclude deprovisioned users
            params["filter"] = 'status ne "DEPROVISIONED"'

        users = []
        page = 1
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  Error: {response.status_code} - {response.text}")
                break

            batch = response.json()
            users.extend(batch)
            print(f"  Page {page}: fetched {len(batch)} users (total: {len(users)})")

            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]
            page += 1

        print(f"  Total users fetched: {len(users)}")
        return users

    def get_user_groups(self, user_id: str) -> List[str]:
        """Get group names for a user."""
        url = f"{self.api_url}/users/{user_id}/groups"
        response = self._make_request("GET", url)
        if not response.ok:
            return []

        groups = response.json()
        # Return group names, excluding system groups
        return [
            g.get('profile', {}).get('name', '')
            for g in groups
            if g.get('type') == 'OKTA_GROUP'
            and g.get('profile', {}).get('name') not in ('Everyone', 'Administrators')
        ]

    def get_group_members(self, group_name: str) -> Set[str]:
        """Get user IDs in a specific group."""
        # First find the group
        url = f"{self.api_url}/groups"
        params = {"q": group_name, "limit": 1}
        response = self._make_request("GET", url, params=params)

        if not response.ok:
            return set()

        groups = response.json()
        group = None
        for g in groups:
            if g.get('profile', {}).get('name') == group_name:
                group = g
                break

        if not group:
            print(f"  Warning: Group '{group_name}' not found")
            return set()

        # Get group members
        url = f"{self.api_url}/groups/{group['id']}/users"
        params = {"limit": 200}
        member_ids = set()

        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                break
            for user in response.json():
                member_ids.add(user.get('id'))
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        return member_ids

    def get_user_manager(self, user_id: str) -> Optional[str]:
        """Get manager email for a user."""
        url = f"{self.api_url}/users/{user_id}/linkedObjects/manager"
        response = self._make_request("GET", url)

        if not response.ok or response.status_code == 404:
            return None

        managers = response.json()
        if not managers:
            return None

        # Get the first manager's details
        manager_link = managers[0]
        manager_url = manager_link.get('_links', {}).get('self', {}).get('href')
        if manager_url:
            manager_response = self._make_request("GET", manager_url)
            if manager_response.ok:
                manager = manager_response.json()
                return manager.get('profile', {}).get('email')

        return None


def escape_csv_json(value: str) -> str:
    """Escape JSON string for CSV field."""
    if not value:
        return ""
    # Double up quotes for CSV
    return value.replace('"', '""')


def build_custom_attributes(profile: Dict, standard_fields: Set[str]) -> str:
    """Extract custom attributes as JSON string."""
    custom = {}
    for key, value in profile.items():
        if key not in standard_fields and value is not None:
            custom[key] = value

    if not custom:
        return ""

    # Convert to JSON with escaped quotes for CSV
    json_str = json.dumps(custom)
    return json_str


def export_users_to_csv(
    client: OktaClient,
    output_file: str,
    include_deprovisioned: bool = False,
    include_groups: bool = True,
    include_manager: bool = True,
    filter_group: Optional[str] = None,
    verbose: bool = False
):
    """Export users to CSV file."""
    # Standard profile fields (not custom attributes)
    standard_fields = {
        'login', 'email', 'firstName', 'lastName', 'middleName', 'honorificPrefix',
        'honorificSuffix', 'title', 'displayName', 'nickName', 'profileUrl',
        'secondEmail', 'mobilePhone', 'primaryPhone', 'streetAddress', 'city',
        'state', 'zipCode', 'countryCode', 'postalAddress', 'preferredLanguage',
        'locale', 'timezone', 'userType', 'employeeNumber', 'costCenter',
        'organization', 'division', 'department', 'managerId', 'manager'
    }

    # Get users
    users = client.get_all_users(include_deprovisioned)

    # Filter by group if specified
    if filter_group:
        print(f"\nFiltering to users in group: {filter_group}")
        group_member_ids = client.get_group_members(filter_group)
        users = [u for u in users if u.get('id') in group_member_ids]
        print(f"  Filtered to {len(users)} users")

    if not users:
        print("No users to export.")
        return 0

    # Build user data with groups and manager
    print("\nProcessing user details...")
    user_data = []
    user_id_to_email = {u.get('id'): u.get('profile', {}).get('email', '') for u in users}

    for i, user in enumerate(users, 1):
        profile = user.get('profile', {})
        user_id = user.get('id')

        row = {
            'email': profile.get('email', ''),
            'first_name': profile.get('firstName', ''),
            'last_name': profile.get('lastName', ''),
            'login': profile.get('login', ''),
            'status': user.get('status', 'ACTIVE'),
            'department': profile.get('department', ''),
            'title': profile.get('title', ''),
            'manager_email': '',
            'groups': '',
            'custom_profile_attributes': '',
        }

        # Get manager email
        if include_manager:
            manager_id = profile.get('managerId')
            if manager_id and manager_id in user_id_to_email:
                row['manager_email'] = user_id_to_email[manager_id]
            else:
                # Try linked objects API
                manager_email = client.get_user_manager(user_id)
                if manager_email:
                    row['manager_email'] = manager_email

        # Get groups
        if include_groups:
            groups = client.get_user_groups(user_id)
            row['groups'] = ','.join(sorted(groups))

        # Get custom attributes
        custom_attrs = build_custom_attributes(profile, standard_fields)
        row['custom_profile_attributes'] = custom_attrs

        user_data.append(row)

        if verbose or i % 50 == 0:
            print(f"  Processed {i}/{len(users)} users")

    # Write CSV
    print(f"\nWriting to {output_file}...")
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    fieldnames = [
        'email', 'first_name', 'last_name', 'login', 'status',
        'department', 'title', 'manager_email', 'groups', 'custom_profile_attributes'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        # Write header comment
        f.write('# Exported from Okta org: ' + client.org_name + '\n')
        f.write('# Export date: ' + time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + '\n')
        f.write('# Total users: ' + str(len(user_data)) + '\n')

        for row in user_data:
            writer.writerow(row)

    # Summary
    print(f"\nExport complete!")
    print(f"  Total users: {len(user_data)}")
    print(f"  Output file: {output_file}")

    # Count statistics
    with_manager = sum(1 for u in user_data if u['manager_email'])
    with_groups = sum(1 for u in user_data if u['groups'])
    with_custom = sum(1 for u in user_data if u['custom_profile_attributes'])

    print(f"  Users with manager: {with_manager}")
    print(f"  Users with groups: {with_groups}")
    print(f"  Users with custom attributes: {with_custom}")

    return len(user_data)


def main():
    parser = argparse.ArgumentParser(
        description="Export Okta users to CSV for backup/restore"
    )
    parser.add_argument("--output", "-o", required=True,
                        help="Output CSV file path")
    parser.add_argument("--include-deprovisioned", action="store_true",
                        help="Include deprovisioned users")
    parser.add_argument("--no-groups", action="store_true",
                        help="Skip fetching group memberships (faster)")
    parser.add_argument("--no-manager", action="store_true",
                        help="Skip fetching manager relationships (faster)")
    parser.add_argument("--group", type=str,
                        help="Only export users from this group")
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

    print(f"Exporting users from: {org_name}.{base_url}")

    client = OktaClient(org_name, base_url, api_token)

    count = export_users_to_csv(
        client,
        args.output,
        include_deprovisioned=args.include_deprovisioned,
        include_groups=not args.no_groups,
        include_manager=not args.no_manager,
        filter_group=args.group,
        verbose=args.verbose
    )

    if count > 0:
        print("\nNext steps:")
        print("  1. Review the exported CSV")
        print("  2. Use with users_from_csv.tf.example for restore")
        print("  3. Run: terraform plan to preview changes")

    return 0 if count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
