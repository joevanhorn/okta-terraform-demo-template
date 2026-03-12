#!/usr/bin/env python3
"""
Find an entitlement value by name or ID and display its ORN.

Usage:
    python3 scripts/find_entitlement_value.py --app-id 0oar0edy8iuBrRn6t1d7 --search certification_admin
"""

import os
import sys
import argparse
import requests
from urllib.parse import quote

def find_entitlement_value(app_id, search_term):
    """Find an entitlement value by searching app entitlements."""

    org_name = os.getenv('OKTA_ORG_NAME')
    base_url = os.getenv('OKTA_BASE_URL')
    token = os.getenv('OKTA_API_TOKEN')

    if not all([org_name, base_url, token]):
        print("Error: Missing required environment variables:")
        print("  OKTA_ORG_NAME, OKTA_BASE_URL, OKTA_API_TOKEN")
        return None

    # Build the filter query
    filter_query = f'parent.externalId eq "{app_id}" AND parent.type eq "APPLICATION"'
    encoded_filter = quote(filter_query)

    url = f'https://{org_name}.{base_url}/governance/api/v1/entitlements?filter={encoded_filter}&limit=200'

    headers = {
        'Authorization': f'SSWS {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    print(f"Searching entitlements for app: {app_id}")
    print(f"Search term: {search_term}\n")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    entitlements = data.get('data', [])

    print(f"Found {len(entitlements)} entitlements for this app\n")

    results = []
    search_lower = search_term.lower()

    # Search through all entitlements and their values
    for ent in entitlements:
        ent_name = ent.get('name', '')
        ent_id = ent.get('id', '')

        for val in ent.get('values', []):
            val_name = val.get('name', '')
            val_id = val.get('id', '')
            val_orn = val.get('orn', '')
            val_external = val.get('externalValue', '')

            # Check if search term matches
            if (search_lower in val_name.lower() or
                search_lower in val_external.lower() or
                search_lower in val_id.lower()):

                results.append({
                    'entitlement_name': ent_name,
                    'entitlement_id': ent_id,
                    'value_name': val_name,
                    'value_id': val_id,
                    'value_external': val_external,
                    'value_orn': val_orn
                })

    if results:
        print(f"Found {len(results)} matching entitlement value(s):\n")
        for idx, result in enumerate(results, 1):
            print(f"Result #{idx}:")
            print(f"  Entitlement: {result['entitlement_name']} (ID: {result['entitlement_id']})")
            print(f"  Value Name: {result['value_name']}")
            print(f"  Value ID: {result['value_id']}")
            print(f"  Value External: {result['value_external']}")
            print(f"  Value ORN: {result['value_orn']}")
            print()

        return results[0]['value_orn']  # Return first match
    else:
        print(f"No entitlement values found matching '{search_term}'")
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Find entitlement value ORN by searching app entitlements'
    )
    parser.add_argument(
        '--app-id',
        required=True,
        help='Application ID (e.g., 0oar0edy8iuBrRn6t1d7)'
    )
    parser.add_argument(
        '--search',
        required=True,
        help='Search term (entitlement value name, ID, or external value)'
    )

    args = parser.parse_args()

    orn = find_entitlement_value(args.app_id, args.search)

    if orn:
        print("=" * 80)
        print(f"ORN to use in label_mappings.json:")
        print(f"  {orn}")
        print("=" * 80)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
