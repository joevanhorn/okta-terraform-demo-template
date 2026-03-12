#!/usr/bin/env python3
"""
Get correct ORNs for applications by querying their sign-on mode.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.okta_api_manager import OktaAPIManager

def get_app_orn(manager: OktaAPIManager, app_id: str) -> str:
    """
    Get the correct ORN for an application.

    ORN format: orn:okta:idp:{orgId}:apps:{appType}:{appId}
    where appType is based on signOnMode (saml2, oidc, etc.)
    """
    # Get app details
    url = f"{manager.base_url}/api/v1/apps/{app_id}"
    response = manager.session.get(url)
    response.raise_for_status()
    app_data = response.json()

    sign_on_mode = app_data.get('signOnMode', '').lower()
    app_label = app_data.get('label', 'Unknown')
    app_name = app_data.get('name', '')

    # Get org ID from the /api/v1/org endpoint
    org_url = f"{manager.base_url}/api/v1/org"
    org_response = manager.session.get(org_url)
    org_response.raise_for_status()
    org_data = org_response.json()
    org_numeric_id = org_data.get('id')

    # Determine partition from base_url domain
    # okta.com -> okta
    # oktapreview.com -> oktapreview
    # okta-emea.com -> okta-emea
    if 'oktapreview.com' in manager.base_url:
        partition = 'oktapreview'
    elif 'okta-emea.com' in manager.base_url:
        partition = 'okta-emea'
    elif 'trexcloud.com' in manager.base_url:
        partition = 'trexcloud'
    else:
        partition = 'okta'

    # ORN format: orn:{partition}:idp:{orgId}:apps:{appName}:{appId}
    # The appName is from the 'name' field, not the label
    # Normalize app name: lowercase and replace spaces/special chars with underscores
    normalized_app_name = app_name.lower().replace(' ', '_').replace('.', '_').replace('-', '_')

    orn = f"orn:{partition}:idp:{org_numeric_id}:apps:{normalized_app_name}:{app_id}"

    return orn, app_label, sign_on_mode, app_name

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
        '0oamxiwg4zsrWaeJF1d7',  # Salesforce.com
        '0oaq4iodcifSLp30Q1d7',  # Workday
        '0oan4ssz4lmqTnQry1d7',  # SuccessFactors
        '0oamxc34dudXXjGJT1d7',  # SalesDar
    ]

    print("Getting correct ORNs for applications...\n")
    print("="*80)

    orns = []
    for app_id in app_ids:
        try:
            orn, label, sign_on_mode, app_name = get_app_orn(manager, app_id)
            orns.append(orn)
            print(f"{label} ({app_id})")
            print(f"  App Name: {app_name}")
            print(f"  Sign-On Mode: {sign_on_mode}")
            print(f"  ORN: {orn}")
            print()
        except Exception as e:
            print(f"Error for {app_id}: {e}\n")

    print("="*80)
    print("\nJSON array for label_mappings.json:")
    print(json.dumps(orns, indent=2))

if __name__ == "__main__":
    main()
