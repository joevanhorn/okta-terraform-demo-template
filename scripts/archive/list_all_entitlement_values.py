#!/usr/bin/env python3
"""
List all entitlement values for a specific entitlement.

Usage:
    python3 scripts/list_all_entitlement_values.py --entitlement-id esp12pvbc9GsRkvu31d7
"""

import os
import sys
import argparse
import requests
import json

def list_entitlement_values(entitlement_id):
    """List all values for a given entitlement."""

    org_name = os.getenv('OKTA_ORG_NAME')
    base_url = os.getenv('OKTA_BASE_URL')
    token = os.getenv('OKTA_API_TOKEN')

    if not all([org_name, base_url, token]):
        print("Error: Missing required environment variables:")
        print("  OKTA_ORG_NAME, OKTA_BASE_URL, OKTA_API_TOKEN")
        return None

    # Get entitlement details first
    url = f'https://{org_name}.{base_url}/governance/api/v1/entitlements/{entitlement_id}'

    headers = {
        'Authorization': f'SSWS {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    print(f"Fetching entitlement: {entitlement_id}\n")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

    entitlement = response.json()

    print(f"Entitlement Name: {entitlement.get('name')}")
    print(f"Entitlement ID: {entitlement.get('id')}")
    print(f"External Value: {entitlement.get('externalValue')}")
    print(f"Multi-Value: {entitlement.get('multiValue')}")
    print(f"Data Type: {entitlement.get('dataType')}")
    print(f"Parent: {entitlement.get('parent', {}).get('type')} - {entitlement.get('parent', {}).get('externalId')}")
    print()

    # Get all values
    values = entitlement.get('values', [])

    print(f"Found {len(values)} entitlement values:\n")
    print("=" * 100)

    for idx, val in enumerate(values, 1):
        val_name = val.get('name', '')
        val_id = val.get('id', '')
        val_orn = val.get('orn', '')
        val_external = val.get('externalValue', '')

        print(f"\n#{idx}: {val_name}")
        print(f"  ID: {val_id}")
        print(f"  External Value: {val_external}")
        print(f"  ORN: {val_orn}")

    print("\n" + "=" * 100)

    return values

def main():
    parser = argparse.ArgumentParser(
        description='List all entitlement values for a given entitlement'
    )
    parser.add_argument(
        '--entitlement-id',
        required=True,
        help='Entitlement ID (e.g., esp12pvbc9GsRkvu31d7 for ServiceNow Roles)'
    )

    args = parser.parse_args()

    values = list_entitlement_values(args.entitlement_id)

    if values:
        print(f"\nTotal values: {len(values)}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
