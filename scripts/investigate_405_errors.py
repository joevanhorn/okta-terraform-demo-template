#!/usr/bin/env python3
"""
investigate_405_errors.py

Investigation script to test the correct API endpoints based on official documentation.

This script tests the corrected v2 endpoints that were failing with 405 errors in v1.

Key findings from API documentation:
- Request Sequences: /governance/api/v2/resources/{resourceId}/request-sequences (not v1!)
- Request Settings: /governance/api/v2/request-settings (org-level)
                    /governance/api/v2/resources/{resourceId}/request-settings (resource-level)
- Request Conditions: /governance/api/v2/resources/{resourceId}/request-conditions (new)

Usage:
    # Set environment variables (replace with your actual values)
    export OKTA_ORG_NAME="your-org"
    export OKTA_BASE_URL="okta.com"  # or oktapreview.com
    export OKTA_API_TOKEN="<paste-your-token-here>"  # Example placeholder

    python3 scripts/investigate_405_errors.py
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional


class EndpointInvestigator:
    """Test various API endpoints to identify correct patterns"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def test_endpoint(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Test a single endpoint and return results"""
        url = f"{self.base_url}{endpoint}"
        result = {
            "method": method,
            "endpoint": endpoint,
            "url": url,
            "status": None,
            "success": False,
            "error": None,
            "data": None
        }

        try:
            response = self.session.request(method, url, params=params, timeout=10)
            result["status"] = response.status_code

            if response.status_code == 200:
                result["success"] = True
                result["data"] = response.json()
            elif response.status_code == 204:
                result["success"] = True
                result["data"] = "No Content"
            else:
                result["error"] = response.text[:500]

        except requests.exceptions.RequestException as e:
            result["error"] = str(e)

        return result

    def print_result(self, result: Dict):
        """Pretty print test result"""
        status_symbol = "✅" if result["success"] else "❌"
        print(f"\n{status_symbol} {result['method']} {result['endpoint']}")
        print(f"   Status: {result['status']}")

        if result["success"] and result["data"]:
            if isinstance(result["data"], dict):
                if "data" in result["data"]:
                    count = len(result["data"]["data"])
                    print(f"   📊 Found {count} items")
                    if count > 0:
                        print(f"   📝 First item keys: {list(result['data']['data'][0].keys())}")
                else:
                    print(f"   📝 Response keys: {list(result['data'].keys())}")
        elif result["error"]:
            print(f"   ⚠️  Error: {result['error'][:200]}")

    def get_sample_resource_id(self) -> Optional[str]:
        """Get a sample entitlement bundle ID to use for testing"""
        print("\n" + "="*80)
        print("GETTING SAMPLE RESOURCE ID")
        print("="*80)

        result = self.test_endpoint("GET", "/governance/api/v1/entitlement-bundles",
                                    params={"limit": 1})
        self.print_result(result)

        if result["success"] and result["data"]:
            bundles = result["data"].get("data", [])
            if bundles:
                bundle_id = bundles[0].get("id")
                print(f"\n📌 Using resource ID: {bundle_id}")
                return bundle_id

        print("\n⚠️  No entitlement bundles found to use as sample resource")
        return None


def main():
    """Run investigation tests"""

    # Get credentials from environment
    org_name = os.getenv("OKTA_ORG_NAME")
    base_url = os.getenv("OKTA_BASE_URL", "okta.com")
    api_token = os.getenv("OKTA_API_TOKEN")

    if not all([org_name, api_token]):
        print("❌ Error: Missing required environment variables")
        print("   Required: OKTA_ORG_NAME, OKTA_API_TOKEN")
        print("   Optional: OKTA_BASE_URL (default: okta.com)")
        sys.exit(1)

    print("="*80)
    print("OKTA IGA API ENDPOINT INVESTIGATION")
    print("="*80)
    print(f"Organization: {org_name}")
    print(f"Base URL: https://{org_name}.{base_url}")
    print("="*80)

    investigator = EndpointInvestigator(org_name, base_url, api_token)

    # Get a sample resource ID for testing
    resource_id = investigator.get_sample_resource_id()

    # Test 1: Organization Request Settings (v2)
    print("\n" + "="*80)
    print("TEST 1: Organization Request Settings (v2)")
    print("="*80)
    print("Expected: GET /governance/api/v2/request-settings")
    print("This is the CORRECTED endpoint (was v1 before)")

    result = investigator.test_endpoint("GET", "/governance/api/v2/request-settings")
    investigator.print_result(result)

    # Compare with old v1 endpoint
    print("\n--- Comparison: Old v1 endpoint (should fail) ---")
    result_v1 = investigator.test_endpoint("GET", "/governance/api/v1/request-settings")
    investigator.print_result(result_v1)

    # Test 2: Resource Request Settings (v2)
    if resource_id:
        print("\n" + "="*80)
        print("TEST 2: Resource Request Settings (v2)")
        print("="*80)
        print(f"Expected: GET /governance/api/v2/resources/{resource_id}/request-settings")

        result = investigator.test_endpoint(
            "GET",
            f"/governance/api/v2/resources/{resource_id}/request-settings"
        )
        investigator.print_result(result)

    # Test 3: Request Sequences (v2)
    if resource_id:
        print("\n" + "="*80)
        print("TEST 3: Request Sequences (v2)")
        print("="*80)
        print(f"Expected: GET /governance/api/v2/resources/{resource_id}/request-sequences")
        print("This is the CORRECTED endpoint (was v1 without resourceId before)")

        result = investigator.test_endpoint(
            "GET",
            f"/governance/api/v2/resources/{resource_id}/request-sequences"
        )
        investigator.print_result(result)

        # Compare with old v1 endpoint
        print("\n--- Comparison: Old v1 endpoint (should fail with 405) ---")
        result_v1 = investigator.test_endpoint("GET", "/governance/api/v1/request-sequences")
        investigator.print_result(result_v1)

    # Test 4: Request Conditions (v2) - NEW
    if resource_id:
        print("\n" + "="*80)
        print("TEST 4: Request Conditions (v2) - NEW ENDPOINT")
        print("="*80)
        print(f"Expected: GET /governance/api/v2/resources/{resource_id}/request-conditions")
        print("This was not in the original import script")

        result = investigator.test_endpoint(
            "GET",
            f"/governance/api/v2/resources/{resource_id}/request-conditions"
        )
        investigator.print_result(result)

    # Test 5: Resource Owners (with proper filtering)
    print("\n" + "="*80)
    print("TEST 5: Resource Owners API")
    print("="*80)
    print("Testing various filter patterns for resource owners")

    # Test basic list (no filter)
    print("\n--- Basic list (no filter) ---")
    result = investigator.test_endpoint(
        "GET",
        "/governance/api/v1/resource-owners",
        params={"limit": 10}
    )
    investigator.print_result(result)

    # Summary
    print("\n" + "="*80)
    print("INVESTIGATION SUMMARY")
    print("="*80)
    print("\n✅ FIXES NEEDED:")
    print("1. Request Settings: Change v1 → v2")
    print("   Old: /governance/api/v1/request-settings")
    print("   New: /governance/api/v2/request-settings")
    print("\n2. Request Sequences: Change v1 → v2 AND add resourceId")
    print("   Old: /governance/api/v1/request-sequences")
    print("   New: /governance/api/v2/resources/{resourceId}/request-sequences")
    print("\n3. Request Conditions: Add new import (was missing)")
    print("   New: /governance/api/v2/resources/{resourceId}/request-conditions")
    print("\n4. Resource Owners: Add rate limiting and retry logic")
    print("   Current: Works but hits rate limits when querying many resources")
    print("="*80)


if __name__ == "__main__":
    main()
