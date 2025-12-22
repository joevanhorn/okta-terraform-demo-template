#!/usr/bin/env python3
"""
Copy group memberships between Okta organizations.

This script exports group memberships from a source org and imports them
to a target org. Users are matched by email address.

Usage:
    # Export memberships from source org
    python scripts/copy_group_memberships.py export \
        --output memberships.json

    # Import memberships to target org
    python scripts/copy_group_memberships.py import \
        --input memberships.json \
        --dry-run

    # Full copy in one step (requires both org credentials)
    python scripts/copy_group_memberships.py copy \
        --source-org SOURCE_ORG \
        --source-token SOURCE_TOKEN \
        --dry-run

Environment Variables:
    OKTA_ORG_NAME   - Okta org name
    OKTA_BASE_URL   - Okta base URL (default: oktapreview.com)
    OKTA_API_TOKEN  - Okta API token
"""

import argparse
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
        # Rate limit tracking
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = 0

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Update rate limit state and wait if needed."""
        if 'X-Rate-Limit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-Rate-Limit-Remaining'])
        if 'X-Rate-Limit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-Rate-Limit-Reset'])

        if response.status_code == 429:
            wait_time = max(self.rate_limit_reset - time.time() + 1, 1)
            print(f"  Rate limited. Waiting {wait_time:.0f}s...")
            time.sleep(wait_time)
        elif self.rate_limit_remaining < 10:
            # Preemptive slowdown
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

    def get_groups(self, group_type: str = "OKTA_GROUP") -> List[Dict]:
        """Get all groups of specified type."""
        print(f"Fetching {group_type} groups...")
        url = f"{self.api_url}/groups"
        params = {"limit": 200, "filter": f'type eq "{group_type}"'}

        groups = []
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  Error: {response.status_code} - {response.text}")
                break
            groups.extend(response.json())
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  Found {len(groups)} groups")
        return groups

    def get_group_by_name(self, name: str) -> Optional[Dict]:
        """Get a group by name."""
        url = f"{self.api_url}/groups"
        params = {"q": name, "limit": 1}
        response = self._make_request("GET", url, params=params)
        if response.ok:
            groups = response.json()
            for g in groups:
                if g.get('profile', {}).get('name') == name:
                    return g
        return None

    def get_group_members(self, group_id: str) -> List[Dict]:
        """Get all members of a group."""
        url = f"{self.api_url}/groups/{group_id}/users"
        params = {"limit": 200}

        members = []
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  Error getting members: {response.status_code}")
                break
            members.extend(response.json())
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        return members

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get a user by email."""
        url = f"{self.api_url}/users/{email}"
        response = self._make_request("GET", url)
        if response.ok:
            return response.json()
        return None

    def add_user_to_group(self, group_id: str, user_id: str) -> bool:
        """Add a user to a group."""
        url = f"{self.api_url}/groups/{group_id}/users/{user_id}"
        response = self._make_request("PUT", url)
        return response.status_code == 204

    def get_all_users(self) -> Dict[str, Dict]:
        """Get all users indexed by email."""
        print("Fetching all users...")
        url = f"{self.api_url}/users"
        params = {"limit": 200}

        users = {}
        count = 0
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  Error: {response.status_code}")
                break
            for user in response.json():
                email = user.get('profile', {}).get('email', '').lower()
                if email:
                    users[email] = user
                count += 1
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  Found {len(users)} users")
        return users


def export_memberships(client: OktaClient, output_file: str, exclude_system: bool = True):
    """Export group memberships to JSON file."""
    system_groups = {"Everyone", "Administrators"}

    groups = client.get_groups("OKTA_GROUP")

    memberships = {}
    total_members = 0

    for group in groups:
        name = group.get('profile', {}).get('name', '')
        group_id = group.get('id')

        if exclude_system and name in system_groups:
            print(f"  Skipping system group: {name}")
            continue

        members = client.get_group_members(group_id)
        if members:
            # Store emails for matching
            member_emails = []
            for member in members:
                email = member.get('profile', {}).get('email', '').lower()
                if email:
                    member_emails.append(email)

            if member_emails:
                memberships[name] = {
                    'source_group_id': group_id,
                    'member_count': len(member_emails),
                    'member_emails': member_emails
                }
                total_members += len(member_emails)
                print(f"  {name}: {len(member_emails)} members")

    # Write output
    output = {
        'source_org': client.org_name,
        'exported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'group_count': len(memberships),
        'total_members': total_members,
        'memberships': memberships
    }

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nExported {len(memberships)} groups with {total_members} total member assignments")
    print(f"Output written to: {output_file}")

    return memberships


def import_memberships(client: OktaClient, input_file: str, dry_run: bool = True):
    """Import group memberships from JSON file."""
    with open(input_file, 'r') as f:
        data = json.load(f)

    memberships = data.get('memberships', {})
    print(f"\nImporting memberships from {data.get('source_org', 'unknown')}")
    print(f"Groups: {data.get('group_count', 0)}, Members: {data.get('total_members', 0)}")

    if dry_run:
        print("\n*** DRY RUN - No changes will be made ***\n")

    # Get all users in target org for matching
    target_users = client.get_all_users()

    # Get all groups in target org
    target_groups = {g.get('profile', {}).get('name'): g for g in client.get_groups("OKTA_GROUP")}

    stats = {
        'groups_found': 0,
        'groups_missing': 0,
        'users_matched': 0,
        'users_missing': 0,
        'assignments_made': 0,
        'assignments_failed': 0,
    }

    missing_groups = []
    missing_users = set()

    for group_name, membership_data in memberships.items():
        target_group = target_groups.get(group_name)

        if not target_group:
            print(f"  ❌ Group not found in target: {group_name}")
            missing_groups.append(group_name)
            stats['groups_missing'] += 1
            continue

        stats['groups_found'] += 1
        target_group_id = target_group['id']
        member_emails = membership_data.get('member_emails', [])

        matched = 0
        for email in member_emails:
            email_lower = email.lower()
            target_user = target_users.get(email_lower)

            if not target_user:
                missing_users.add(email)
                stats['users_missing'] += 1
                continue

            stats['users_matched'] += 1
            matched += 1

            if not dry_run:
                success = client.add_user_to_group(target_group_id, target_user['id'])
                if success:
                    stats['assignments_made'] += 1
                else:
                    stats['assignments_failed'] += 1

        if matched > 0:
            action = "Would assign" if dry_run else "Assigned"
            print(f"  ✅ {group_name}: {action} {matched}/{len(member_emails)} users")
        else:
            print(f"  ⚠️  {group_name}: No matching users found")

    # Summary
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Groups found in target:    {stats['groups_found']}")
    print(f"Groups missing in target:  {stats['groups_missing']}")
    print(f"Users matched by email:    {stats['users_matched']}")
    print(f"Users not found in target: {stats['users_missing']}")

    if not dry_run:
        print(f"Assignments made:          {stats['assignments_made']}")
        print(f"Assignments failed:        {stats['assignments_failed']}")

    if missing_groups:
        print(f"\nMissing groups ({len(missing_groups)}):")
        for g in missing_groups[:10]:
            print(f"  - {g}")
        if len(missing_groups) > 10:
            print(f"  ... and {len(missing_groups) - 10} more")

    if missing_users:
        print(f"\nMissing users ({len(missing_users)}):")
        for u in list(missing_users)[:10]:
            print(f"  - {u}")
        if len(missing_users) > 10:
            print(f"  ... and {len(missing_users) - 10} more")

    if dry_run:
        print(f"\n*** DRY RUN COMPLETE - Run without --dry-run to apply changes ***")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Copy group memberships between Okta organizations"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export memberships from source org')
    export_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    export_parser.add_argument('--exclude-system', action='store_true', default=True,
                               help='Exclude system groups')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import memberships to target org')
    import_parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    import_parser.add_argument('--dry-run', action='store_true', default=False,
                               help='Preview changes without applying')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get Okta credentials
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "oktapreview.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN environment variables required")
        sys.exit(1)

    client = OktaClient(org_name, base_url, api_token)
    print(f"Connected to: {org_name}.{base_url}")

    if args.command == 'export':
        export_memberships(client, args.output, args.exclude_system)
    elif args.command == 'import':
        import_memberships(client, args.input, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
