#!/usr/bin/env python3
"""
Copy entitlement bundle grants between Okta orgs.

This script:
1. Exports grants from a source org
2. Maps bundle names and group names to the target org
3. Creates matching grants in the target org

Usage:
    # Export grants from source org
    python scripts/copy_grants_between_orgs.py export \
        --output grants_export.json

    # Import grants to target org (dry run)
    python scripts/copy_grants_between_orgs.py import \
        --input grants_export.json \
        --exclude-apps "Money Movement" \
        --dry-run

    # Import grants to target org (apply)
    python scripts/copy_grants_between_orgs.py import \
        --input grants_export.json \
        --exclude-apps "Money Movement"

Environment Variables:
    OKTA_ORG_NAME   - Okta org name
    OKTA_BASE_URL   - Okta base URL (default: oktapreview.com)
    OKTA_API_TOKEN  - Okta API token with governance permissions
"""

import argparse
import json
import os
import sys
import requests
import time
from typing import Dict, List, Optional, Set


class OktaGovernanceClient:
    """Client for Okta Governance API operations."""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.governance_url = f"{self.base_url}/governance/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"SSWS {api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limiting by waiting if needed."""
        if response.status_code == 429:
            reset_time = int(response.headers.get('X-Rate-Limit-Reset', time.time() + 60))
            wait_time = max(reset_time - time.time() + 1, 1)
            print(f"  ⏳ Rate limited. Waiting {wait_time:.0f}s...")
            time.sleep(wait_time)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make API request with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 429:
                self._handle_rate_limit(response)
                continue
            return response
        return response

    def get_entitlement_bundles(self) -> List[Dict]:
        """Get all entitlement bundles."""
        print("Fetching entitlement bundles...")
        url = f"{self.governance_url}/entitlement-bundles"
        params = {"limit": 200}

        bundles = []
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  ❌ Error: {response.status_code} - {response.text}")
                break

            data = response.json()
            page_bundles = data if isinstance(data, list) else data.get("data", [])
            bundles.extend(page_bundles)

            # Handle pagination
            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  ✅ Found {len(bundles)} bundles")
        return bundles

    def get_all_grants(self) -> List[Dict]:
        """Get all grants from the org."""
        print("Fetching all grants...")
        url = f"{self.governance_url}/grants"
        params = {"limit": 200}

        grants = []
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                if response.status_code == 404:
                    print("  ⚠️ No grants found (404)")
                    return []
                print(f"  ❌ Error getting grants: {response.status_code} - {response.text[:200]}")
                break

            data = response.json()
            page_grants = data if isinstance(data, list) else data.get("data", [])
            grants.extend(page_grants)

            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  ✅ Found {len(grants)} grants")
        return grants

    def get_apps(self) -> Dict[str, Dict]:
        """Get all apps, indexed by ID."""
        print("Fetching applications...")
        url = f"{self.base_url}/api/v1/apps"
        params = {"limit": 200}

        apps = {}
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  ❌ Error: {response.status_code}")
                break

            for app in response.json():
                apps[app["id"]] = app

            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  ✅ Found {len(apps)} applications")
        return apps

    def get_groups(self) -> Dict[str, Dict]:
        """Get all groups, indexed by ID."""
        print("Fetching groups...")
        url = f"{self.base_url}/api/v1/groups"
        params = {"limit": 200}

        groups = {}
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  ❌ Error: {response.status_code}")
                break

            for group in response.json():
                groups[group["id"]] = group

            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  ✅ Found {len(groups)} groups")
        return groups

    def get_users(self) -> Dict[str, Dict]:
        """Get all users, indexed by ID."""
        print("Fetching users...")
        url = f"{self.base_url}/api/v1/users"
        params = {"limit": 200}

        users = {}
        while url:
            response = self._make_request("GET", url, params=params)
            if not response.ok:
                print(f"  ❌ Error: {response.status_code}")
                break

            for user in response.json():
                users[user["id"]] = user

            url = None
            params = {}
            if "next" in response.links:
                url = response.links["next"]["url"]

        print(f"  ✅ Found {len(users)} users")
        return users

    def create_grant(self, bundle_id: str, principal_id: str, principal_type: str = "GROUP",
                     dry_run: bool = False) -> Dict:
        """Create a grant (assign bundle to principal)."""
        url = f"{self.governance_url}/grants"

        payload = {
            "principal": {
                "id": principal_id,
                "type": principal_type
            },
            "bundle": {
                "id": bundle_id
            },
            "grantType": "ENTITLEMENT-BUNDLE"
        }

        if dry_run:
            return {"status": "dry_run", "payload": payload}

        response = self._make_request("POST", url, json=payload)
        if response.ok:
            return {"status": "created", "data": response.json()}
        elif response.status_code == 409:
            return {"status": "exists", "message": "Grant already exists"}
        else:
            return {"status": "error", "code": response.status_code, "message": response.text}


def export_grants(args):
    """Export grants from source org."""
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "oktapreview.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN environment variables required")
        sys.exit(1)

    client = OktaGovernanceClient(org_name, base_url, api_token)

    # Get all bundles
    bundles = client.get_entitlement_bundles()
    if not bundles:
        print("No bundles found")
        sys.exit(1)

    # Get groups and users for name resolution
    groups = client.get_groups()
    users = client.get_users()
    apps = client.get_apps()

    # Build bundle lookup
    bundle_lookup = {}
    for bundle in bundles:
        bundle_id = bundle.get("id")
        bundle_name = bundle.get("name", "Unknown")

        # Get target app info
        target_app_id = None
        target_app_name = None
        targets = bundle.get("target", [])
        if targets and len(targets) > 0:
            target = targets[0] if isinstance(targets, list) else targets
            target_app_id = target.get("externalId")
            if target_app_id and target_app_id in apps:
                target_app_name = apps[target_app_id].get("label", "Unknown")

        bundle_lookup[bundle_id] = {
            "id": bundle_id,
            "name": bundle_name,
            "target_app_id": target_app_id,
            "target_app_name": target_app_name,
            "status": bundle.get("status")
        }

    # Get all grants
    all_grants = client.get_all_grants()

    # Build export data
    export_data = {
        "source_org": org_name,
        "export_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bundles": list(bundle_lookup.values()),
        "grants": []
    }

    print("\nProcessing grants...")
    print("=" * 70)

    for grant in all_grants:
        # Get bundle info from grant
        bundle_info = grant.get("bundle", {})
        bundle_id = bundle_info.get("id")

        if bundle_id not in bundle_lookup:
            continue  # Skip grants for unknown bundles

        bundle_data = bundle_lookup[bundle_id]
        bundle_name = bundle_data["name"]
        target_app_id = bundle_data["target_app_id"]
        target_app_name = bundle_data["target_app_name"]

        # Get principal info
        principal = grant.get("principal", {})
        principal_id = principal.get("id")
        principal_type = principal.get("type", "UNKNOWN")

        # Resolve principal name
        principal_name = "Unknown"
        if principal_type == "GROUP" and principal_id in groups:
            principal_name = groups[principal_id].get("profile", {}).get("name", "Unknown")
        elif principal_type == "USER" and principal_id in users:
            profile = users[principal_id].get("profile", {})
            principal_name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
            if not principal_name:
                principal_name = profile.get("login", "Unknown")

        grant_info = {
            "bundle_id": bundle_id,
            "bundle_name": bundle_name,
            "target_app_id": target_app_id,
            "target_app_name": target_app_name,
            "principal_id": principal_id,
            "principal_type": principal_type,
            "principal_name": principal_name,
            "grant_id": grant.get("id")
        }
        export_data["grants"].append(grant_info)

    # Print summary by bundle
    grants_by_bundle = {}
    for g in export_data["grants"]:
        bn = g["bundle_name"]
        if bn not in grants_by_bundle:
            grants_by_bundle[bn] = []
        grants_by_bundle[bn].append(g)

    for bundle_name, bundle_grants in sorted(grants_by_bundle.items()):
        print(f"\n{bundle_name} ({len(bundle_grants)} grants)")
        target_app = bundle_grants[0].get("target_app_name") if bundle_grants else None
        if target_app:
            print(f"  Target app: {target_app}")
        for g in bundle_grants:
            print(f"    - {g['principal_type']}: {g['principal_name']}")

    # Write export file
    output_file = args.output
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Exported {len(export_data['grants'])} grants from {len(export_data['bundles'])} bundles")
    print(f"Output written to: {output_file}")

    return 0


def import_grants(args):
    """Import grants to target org."""
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "oktapreview.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN environment variables required")
        sys.exit(1)

    # Load export file
    with open(args.input, 'r') as f:
        export_data = json.load(f)

    print(f"Loaded {len(export_data['grants'])} grants from {export_data['source_org']}")
    print(f"Target org: {org_name}")

    # Build exclusion lists
    excluded_apps: Set[str] = set()
    if args.exclude_apps:
        excluded_apps.update(args.exclude_apps)
        print(f"Excluding apps: {', '.join(excluded_apps)}")

    client = OktaGovernanceClient(org_name, base_url, api_token)

    # Get target org resources for mapping
    bundles = client.get_entitlement_bundles()
    groups = client.get_groups()
    users = client.get_users()
    apps = client.get_apps()

    # Build name -> ID mappings for target org
    bundle_name_to_id = {b["name"]: b["id"] for b in bundles}
    group_name_to_id = {g["profile"]["name"]: g["id"] for g in groups.values()}

    # User mapping by email/login
    user_login_to_id = {}
    for uid, user in users.items():
        login = user.get("profile", {}).get("login", "")
        email = user.get("profile", {}).get("email", "")
        if login:
            user_login_to_id[login.lower()] = uid
        if email and email.lower() != login.lower():
            user_login_to_id[email.lower()] = uid

    # Also map by name (first last)
    user_name_to_id = {}
    for uid, user in users.items():
        profile = user.get("profile", {})
        name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
        if name:
            user_name_to_id[name.lower()] = uid

    print("\nProcessing grants...")
    print("=" * 70)

    results = {"created": 0, "exists": 0, "skipped": 0, "errors": 0, "excluded": 0}

    for grant in export_data["grants"]:
        bundle_name = grant["bundle_name"]
        target_app_name = grant.get("target_app_name", "")
        principal_name = grant["principal_name"]
        principal_type = grant["principal_type"]

        # Check exclusions
        if target_app_name in excluded_apps:
            if args.verbose:
                print(f"  ⏭️  Excluded (app): {bundle_name} -> {principal_name}")
            results["excluded"] += 1
            continue

        # Find bundle in target org
        target_bundle_id = bundle_name_to_id.get(bundle_name)
        if not target_bundle_id:
            print(f"  ⚠️  Bundle not found in target: {bundle_name}")
            results["skipped"] += 1
            continue

        # Find principal in target org
        target_principal_id = None
        if principal_type == "GROUP":
            target_principal_id = group_name_to_id.get(principal_name)
        elif principal_type == "USER":
            # Try by name first, then by login
            target_principal_id = user_name_to_id.get(principal_name.lower())
            if not target_principal_id:
                # Try original login if stored
                target_principal_id = user_login_to_id.get(principal_name.lower())

        if not target_principal_id:
            print(f"  ⚠️  {principal_type} not found in target: {principal_name}")
            results["skipped"] += 1
            continue

        # Create grant
        print(f"\n{bundle_name}")
        print(f"  {principal_type}: {principal_name}")

        result = client.create_grant(
            target_bundle_id,
            target_principal_id,
            principal_type,
            dry_run=args.dry_run
        )

        status = result.get("status")
        if status == "created":
            print(f"  ✅ Created grant")
            results["created"] += 1
        elif status == "exists":
            print(f"  ⏭️  Grant already exists")
            results["exists"] += 1
        elif status == "dry_run":
            print(f"  🔍 [DRY RUN] Would create grant")
            results["created"] += 1
        else:
            print(f"  ❌ Error: {result.get('message', 'Unknown error')}")
            results["errors"] += 1

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Grants created: {results['created']}")
    print(f"Already existed: {results['exists']}")
    print(f"Excluded (by filter): {results['excluded']}")
    print(f"Skipped (not found): {results['skipped']}")
    print(f"Errors: {results['errors']}")

    if args.dry_run:
        print("\n[DRY RUN] No changes were made. Remove --dry-run to apply.")

    return 0 if results["errors"] == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Copy entitlement bundle grants between Okta orgs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export grants from source org")
    export_parser.add_argument(
        "--output", "-o",
        default="grants_export.json",
        help="Output file path (default: grants_export.json)"
    )
    export_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import grants to target org")
    import_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input file from export"
    )
    import_parser.add_argument(
        "--exclude-apps",
        nargs="+",
        help="App names to exclude (e.g., 'Money Movement')"
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    import_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    if args.command == "export":
        return export_grants(args)
    elif args.command == "import":
        return import_grants(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
