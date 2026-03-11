#!/usr/bin/env python3
"""
investigate_labels_api.py

Deep investigation of Okta Labels API to understand the 405 error
and find the correct way to query resources by label.

Usage:
    python3 scripts/investigate_labels_api.py
"""

import os
import sys
import json
import requests
from typing import Dict, Optional


class LabelsAPIInvestigator:
    """Investigate Labels API endpoints and methods"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.governance_base = f"{self.base_url}/governance/api/v1"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def print_section(self, title: str):
        """Print a formatted section header"""
        print("\n" + "="*80)
        print(title)
        print("="*80)

    def list_labels_detailed(self) -> Dict:
        """Get labels and examine response structure in detail"""
        self.print_section("STEP 1: List Labels - Detailed Response Analysis")

        url = f"{self.governance_base}/labels"
        print(f"URL: {url}")
        print(f"Method: GET")
        print(f"Headers: {json.dumps(dict(self.session.headers), indent=2)}")

        try:
            response = self.session.get(url)
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response Headers:")
            for key, value in response.headers.items():
                if key.lower() in ['content-type', 'allow', 'access-control-allow-methods']:
                    print(f"  {key}: {value}")

            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ SUCCESS")
                print(f"\nFull Response Structure:")
                print(json.dumps(data, indent=2))

                # Analyze structure
                print(f"\nResponse Keys: {list(data.keys())}")

                if 'data' in data:
                    print(f"Number of labels: {len(data.get('data', []))}")
                    if data['data']:
                        print(f"\nFirst label structure:")
                        print(json.dumps(data['data'][0], indent=2))
                        print(f"\nFirst label keys: {list(data['data'][0].keys())}")

                return data
            else:
                print(f"❌ Failed: {response.text}")
                return {}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {}

    def try_get_label_by_name(self, label_name: str) -> Optional[Dict]:
        """Try GET /labels/{name} and analyze response"""
        self.print_section(f"STEP 2: Try GET /labels/{label_name}")

        url = f"{self.governance_base}/labels/{label_name}"
        print(f"URL: {url}")
        print(f"Method: GET")

        try:
            response = self.session.get(url)
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response Headers:")
            for key, value in response.headers.items():
                if key.lower() in ['content-type', 'allow', 'access-control-allow-methods']:
                    print(f"  {key}: {value}")

            if response.status_code == 200:
                print(f"✅ SUCCESS")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
                return response.json()
            elif response.status_code == 404:
                print(f"❌ 404 Not Found")
                print(f"Response: {response.text}")
            else:
                print(f"❌ Status {response.status_code}")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"❌ Error: {e}")

        return None

    def try_all_methods_on_resources(self, label_name: str):
        """Try different HTTP methods on /labels/{name}/resources"""
        self.print_section(f"STEP 3: Try All HTTP Methods on /labels/{label_name}/resources")

        url = f"{self.governance_base}/labels/{label_name}/resources"
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']

        print(f"Base URL: {url}\n")

        for method in methods:
            print(f"\n--- Testing {method} ---")
            try:
                if method == 'OPTIONS':
                    response = self.session.options(url)
                elif method == 'GET':
                    response = self.session.get(url)
                elif method == 'POST':
                    response = self.session.post(url, json={})
                elif method == 'PUT':
                    response = self.session.put(url, json={"resourceOrns": []})
                elif method == 'DELETE':
                    response = self.session.delete(url, json={"resourceOrns": []})
                elif method == 'PATCH':
                    response = self.session.patch(url, json={})

                print(f"Status Code: {response.status_code}")

                # Check for Allow header
                if 'Allow' in response.headers or 'allow' in response.headers:
                    allow = response.headers.get('Allow') or response.headers.get('allow')
                    print(f"✅ Allow Header: {allow}")

                if response.status_code == 200:
                    print(f"✅ SUCCESS!")
                    print(f"Response: {response.text[:500]}")
                elif response.status_code == 405:
                    print(f"❌ 405 Method Not Allowed")
                    print(f"Response: {response.text[:200]}")
                elif response.status_code == 404:
                    print(f"❌ 404 Not Found")
                else:
                    print(f"Response: {response.text[:200]}")

            except Exception as e:
                print(f"❌ Error: {e}")

    def check_if_resources_in_label_response(self, labels_data: Dict):
        """Check if resource info is already included in label list response"""
        self.print_section("STEP 4: Check if Resources Are Included in Label List")

        if not labels_data or 'data' not in labels_data:
            print("No labels data available")
            return

        print("Examining label objects for resource information...")

        for label in labels_data.get('data', []):
            label_name = label.get('name', 'unknown')
            print(f"\nLabel: {label_name}")
            print(f"Keys: {list(label.keys())}")

            # Look for any keys that might contain resources
            for key, value in label.items():
                if any(keyword in key.lower() for keyword in ['resource', 'assignment', 'count', 'item']):
                    print(f"  ⭐ Found: {key} = {value}")

    def try_alternative_endpoints(self, label_name: str):
        """Try alternative endpoint patterns"""
        self.print_section(f"STEP 5: Try Alternative Endpoint Patterns for '{label_name}'")

        alternatives = [
            f"/labels/{label_name}/assignments",
            f"/labels/{label_name}/items",
            f"/resources?label={label_name}",
            f"/resources?labelName={label_name}",
            f"/catalog/resources?label={label_name}",
            f"/label-assignments?label={label_name}",
        ]

        for alt_path in alternatives:
            print(f"\n--- Trying: {alt_path} ---")
            url = f"{self.governance_base}{alt_path}"

            try:
                response = self.session.get(url)
                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    print(f"✅ SUCCESS! Found working endpoint!")
                    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}")
                elif response.status_code == 404:
                    print(f"404 Not Found")
                elif response.status_code == 405:
                    print(f"405 Method Not Allowed")
                else:
                    print(f"Response: {response.text[:200]}")

            except Exception as e:
                print(f"Error: {str(e)[:100]}")

    def check_catalog_api_for_labels(self):
        """Check if catalog API exposes label information"""
        self.print_section("STEP 6: Check Catalog API for Label Information")

        endpoints = [
            "/catalog/resources",
            "/catalog/entries",
            "/resource-sets",
        ]

        for endpoint in endpoints:
            print(f"\n--- Trying: {endpoint} ---")
            url = f"{self.governance_base}{endpoint}"

            try:
                response = self.session.get(url)
                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Endpoint exists")
                    print(f"Response keys: {list(data.keys())}")

                    # Check first item for label fields
                    if 'data' in data and data['data']:
                        first_item = data['data'][0]
                        print(f"First item keys: {list(first_item.keys())}")

                        for key, value in first_item.items():
                            if 'label' in key.lower():
                                print(f"  ⭐ Found label field: {key} = {value}")
                elif response.status_code == 404:
                    print(f"404 Not Found")
                else:
                    print(f"Status {response.status_code}: {response.text[:200]}")

            except Exception as e:
                print(f"Error: {str(e)[:100]}")

    def run_full_investigation(self):
        """Run complete investigation"""
        print("\n" + "="*80)
        print("OKTA LABELS API - DEEP INVESTIGATION")
        print("Investigating 405 Method Not Allowed Error")
        print("="*80)

        # Step 1: Get labels with detailed analysis
        labels_data = self.list_labels_detailed()

        if not labels_data or 'data' not in labels_data:
            print("\n❌ Cannot proceed - no labels found")
            return

        label_names = [label.get('name') for label in labels_data.get('data', [])]
        print(f"\n📋 Found labels: {label_names}")

        if not label_names:
            print("❌ No label names found")
            return

        first_label = label_names[0]

        # Step 2: Try GET /labels/{name}
        self.try_get_label_by_name(first_label)

        # Step 3: Try all HTTP methods on resources endpoint
        self.try_all_methods_on_resources(first_label)

        # Step 4: Check if resources are in the label list response
        self.check_if_resources_in_label_response(labels_data)

        # Step 5: Try alternative endpoint patterns
        self.try_alternative_endpoints(first_label)

        # Step 6: Check catalog API
        self.check_catalog_api_for_labels()

        # Summary
        self.print_section("INVESTIGATION SUMMARY")
        print("""
Based on this investigation, we can determine:

1. Which endpoints are actually supported
2. What HTTP methods work for each endpoint
3. Whether resource information is included in other responses
4. What alternative endpoints might exist for querying resources by label

If GET /labels/{name}/resources returns 405:
  - The endpoint exists but doesn't support GET method
  - It might only support PUT (for applying labels)
  - Resource information might be available through a different endpoint
  - Or labels might only be visible when querying resources directly

Next steps based on findings...
        """)


def main():
    org_name = os.environ.get("OKTA_ORG_NAME")
    base_url = os.environ.get("OKTA_BASE_URL", "okta.com")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_name or not api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    investigator = LabelsAPIInvestigator(org_name, base_url, api_token)
    investigator.run_full_investigation()


if __name__ == "__main__":
    main()
