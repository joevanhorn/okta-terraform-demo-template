#!/usr/bin/env python3
"""
Check if apps are eligible for label assignment by querying the governance API.
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

    app_ids = [
        ('0oamxiwg4zsrWaeJF1d7', 'Salesforce.com'),
        ('0oaq4iodcifSLp30Q1d7', 'Workday'),
        ('0oan4ssz4lmqTnQry1d7', 'SuccessFactors'),
        ('0oamxc34dudXXjGJT1d7', 'Salesday'),
    ]

    print("Checking label eligibility for apps...")
    print("=" * 80)

    for app_id, app_name in app_ids:
        print(f"\n{app_name} ({app_id}):")

        # Check app details
        app_url = f"{manager.base_url}/api/v1/apps/{app_id}"
        try:
            app_response = manager.session.get(app_url)
            app_response.raise_for_status()
            app_data = app_response.json()

            print(f"  ✅ App exists")
            print(f"  Sign-on mode: {app_data.get('signOnMode')}")
            print(f"  Status: {app_data.get('status')}")
            print(f"  Name: {app_data.get('name')}")

            # Check if it's a template app
            if 'settings' in app_data:
                settings = app_data.get('settings', {})
                if 'app' in settings:
                    print(f"  App settings: {json.dumps(settings.get('app', {}), indent=4)}")

        except Exception as e:
            print(f"  ❌ Error fetching app: {e}")
            continue

        # Try to get existing labels for this app
        # The ORN format for querying
        org_url = f"{manager.base_url}/api/v1/org"
        org_response = manager.session.get(org_url)
        org_data = org_response.json()
        org_id = org_data.get('id')

        app_type_map = {
            'saml_2_0': 'saml',
            'saml2': 'saml',
            'openid_connect': 'oidc',
            'oidc': 'oidc',
            'browser_plugin': 'browser_plugin',
            'ws_federation': 'ws-federation',
            'auto': 'auto'
        }

        sign_on_mode = app_data.get('signOnMode', '').lower()
        app_type = app_type_map.get(sign_on_mode, sign_on_mode)
        orn = f"orn:okta:idp:{org_id}:apps:{app_type}:{app_id}"

        print(f"  ORN: {orn}")

        # Try to query labels for this resource
        labels_url = f"{manager.base_url}/governance/api/v1/resource-labels"
        params = {"resourceOrn": orn}

        try:
            labels_response = manager.session.get(labels_url, params=params)
            labels_response.raise_for_status()
            labels_data = labels_response.json()
            print(f"  ✅ Resource is accessible via governance API")
            print(f"  Current labels: {len(labels_data.get('data', []))} labels assigned")
            if labels_data.get('data'):
                for label in labels_data.get('data', []):
                    print(f"    - {label.get('label', {}).get('name')}: {label.get('value', {}).get('name')}")
        except Exception as e:
            print(f"  ❌ Error querying labels: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response status: {e.response.status_code}")
                print(f"  Response body: {e.response.text}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
