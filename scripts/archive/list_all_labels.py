#!/usr/bin/env python3
"""
List all labels in Okta using the governance API.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.okta_api_manager import OktaAPIManager

def main():
    # Get credentials from environment
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "okta.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    manager = OktaAPIManager(
        org_name=org_name,
        base_url=base_url,
        api_token=api_token
    )

    # List all labels
    url = f"{manager.base_url}/governance/api/v1/labels"
    print(f"Fetching labels from: {url}")
    print()

    try:
        response = manager.session.get(url)
        response.raise_for_status()
        labels_data = response.json()

        print(f"Raw API Response:")
        print(json.dumps(labels_data, indent=2))
        print()
        print("=" * 80)
        print()

        # Parse and display labels
        if 'data' in labels_data:
            labels = labels_data.get('data', [])
            print(f"Found {len(labels)} labels:")
            print()

            for label in labels:
                print(f"Label: {label.get('name')}")
                print(f"  ID: {label.get('labelId')}")
                print(f"  Description: {label.get('description', 'N/A')}")
                print(f"  Values:")
                for value in label.get('values', []):
                    print(f"    - {value.get('name')}: {value.get('labelValueId')}")
                print()
        else:
            print("No 'data' field in response")

    except Exception as e:
        print(f"Error fetching labels: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")

if __name__ == "__main__":
    main()
