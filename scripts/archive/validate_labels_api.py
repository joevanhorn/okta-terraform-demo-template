#!/usr/bin/env python3
"""
validate_labels_api.py

Validates the Labels API integration based on Okta IGA API specification.
Tests that we can properly import existing labels and their resource assignments.

Based on Okta IGA Labels API:
- GET /governance/api/v1/labels - List all labels
- GET /governance/api/v1/labels/{labelName} - Get specific label
- GET /governance/api/v1/labels/{labelName}/resources - Get resources for label
- POST /governance/api/v1/labels - Create label
- PUT /governance/api/v1/labels/{labelName}/resources - Apply label to resources

Usage:
    python3 scripts/validate_labels_api.py
    python3 scripts/validate_labels_api.py --validate-imports
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List, Optional


class LabelsAPIValidator:
    """Validates Labels API endpoints and data structures"""

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

    def test_api_connection(self) -> bool:
        """Test basic API connectivity"""
        print("\n" + "="*80)
        print("TESTING API CONNECTION")
        print("="*80)

        try:
            url = f"{self.base_url}/api/v1/users?limit=1"
            response = self.session.get(url)
            response.raise_for_status()
            print("✅ API Connection: SUCCESS")
            print(f"   Org: {self.org_name}")
            print(f"   Base URL: {self.base_url}")
            return True
        except Exception as e:
            print(f"❌ API Connection: FAILED - {e}")
            return False

    def list_labels(self) -> Dict:
        """Test GET /governance/api/v1/labels"""
        print("\n" + "="*80)
        print("TEST: List All Labels")
        print("="*80)
        print(f"Endpoint: GET {self.governance_base}/labels")

        try:
            url = f"{self.governance_base}/labels"

            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                labels = data.get("data", [])
                print(f"✅ SUCCESS: Retrieved {len(labels)} labels")

                if labels:
                    print("\nLabel Details:")
                    for label in labels:
                        print(f"  • {label.get('name')}")
                        print(f"    - Description: {label.get('description', 'N/A')}")
                        print(f"    - ID: {label.get('id', 'N/A')}")
                        if 'color' in label:
                            print(f"    - Color: {label.get('color')}")
                        print()

                return {"success": True, "labels": labels, "count": len(labels)}
            elif response.status_code == 400:
                print("⚠️  400 Bad Request - Labels API may not be available")
                print(f"   Response: {response.text}")
                return {"success": False, "error": "bad_request", "labels": []}
            elif response.status_code == 404:
                print("⚠️  404 Not Found - Labels endpoint not available")
                return {"success": False, "error": "not_found", "labels": []}
            else:
                response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            return {"success": False, "error": str(e), "labels": []}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"success": False, "error": str(e), "labels": []}

    def get_label_by_id(self, label_name: str, label_id: str) -> Optional[Dict]:
        """Test GET /governance/api/v1/labels/{labelId}"""
        print("\n" + "="*80)
        print(f"TEST: Get Label by ID - '{label_name}' (ID: {label_id})")
        print("="*80)
        print(f"Endpoint: GET {self.governance_base}/labels/{label_id}")

        try:
            url = f"{self.governance_base}/labels/{label_id}"
            response = self.session.get(url)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: Retrieved label '{label_name}'")
                print(f"\nLabel Data:")
                print(json.dumps(data, indent=2))
                return data
            elif response.status_code == 404:
                print(f"⚠️  Label '{label_name}' not found")
                return None
            else:
                response.raise_for_status()

        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def list_all_resource_labels(self) -> Dict:
        """Test GET /governance/api/v1/resource-labels"""
        print("\n" + "="*80)
        print(f"TEST: List All Resource-Label Assignments")
        print("="*80)
        print(f"Endpoint: GET {self.governance_base}/resource-labels")

        try:
            url = f"{self.governance_base}/resource-labels"
            params = {"limit": 200}

            response = self.session.get(url, params=params)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                assignments = data.get("data", [])
                print(f"✅ SUCCESS: Retrieved {len(assignments)} resource-label assignments")

                if assignments:
                    print("\nSample assignments:")
                    for assignment in assignments[:3]:  # Show first 3
                        print(f"  • Resource: {assignment.get('resource', {}).get('name', 'N/A')}")
                        print(f"    ORN: {assignment.get('resource', {}).get('orn', 'N/A')}")
                        labels = assignment.get('labels', [])
                        print(f"    Labels: {[l.get('name') for l in labels]}")
                        print()

                    if len(assignments) > 3:
                        print(f"  ... and {len(assignments) - 3} more assignments")
                else:
                    print("  ℹ️  No resource-label assignments found")

                return {"success": True, "assignments": assignments, "count": len(assignments)}
            else:
                response.raise_for_status()

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"success": False, "assignments": [], "count": 0}

    def get_label_resources(self, label_name: str, label_id: str, label_value_id: str) -> Dict:
        """Get resources for a specific label using filter parameter"""
        print("\n" + "="*80)
        print(f"TEST: Get Resources for Label - '{label_name}' (using filter)")
        print("="*80)
        print(f"Endpoint: GET {self.governance_base}/resource-labels")
        print(f"Filter: labelValueId eq \"{label_value_id}\"")

        try:
            url = f"{self.governance_base}/resource-labels"
            filter_expr = f'labelValueId eq "{label_value_id}"'
            params = {
                "filter": filter_expr,
                "limit": 200
            }

            response = self.session.get(url, params=params)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                assignments = data.get("data", [])
                print(f"✅ SUCCESS: Found {len(assignments)} resources with label '{label_name}'")

                if assignments:
                    print("\nResources:")
                    for assignment in assignments[:5]:  # Show first 5
                        resource = assignment.get("resource", {})
                        print(f"  • Name: {resource.get('name', 'N/A')}")
                        print(f"    ORN: {resource.get('orn', 'N/A')}")
                        print(f"    Type: {resource.get('type', 'N/A')}")
                        print()

                    if len(assignments) > 5:
                        print(f"  ... and {len(assignments) - 5} more resources")
                else:
                    print("  ℹ️  No resources assigned to this label")

                return {"success": True, "resources": assignments, "count": len(assignments)}
            else:
                response.raise_for_status()

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"success": False, "resources": [], "count": 0}

    def validate_label_structure(self, label: Dict) -> Dict:
        """Validate that a label has the expected structure"""
        print("\n" + "="*80)
        print("VALIDATING LABEL DATA STRUCTURE")
        print("="*80)

        required_fields = ["name"]
        optional_fields = ["id", "description", "color", "created", "lastUpdated"]

        validation_results = {
            "valid": True,
            "missing_required": [],
            "present_optional": [],
            "extra_fields": []
        }

        # Check required fields
        for field in required_fields:
            if field in label:
                print(f"✅ Required field '{field}': present")
            else:
                print(f"❌ Required field '{field}': MISSING")
                validation_results["valid"] = False
                validation_results["missing_required"].append(field)

        # Check optional fields
        for field in optional_fields:
            if field in label:
                print(f"✅ Optional field '{field}': present")
                validation_results["present_optional"].append(field)

        # Check for extra fields
        all_expected = required_fields + optional_fields
        for field in label.keys():
            if field not in all_expected:
                print(f"ℹ️  Extra field '{field}': present (not in spec)")
                validation_results["extra_fields"].append(field)

        return validation_results

    def compare_with_export(self, export_file: str) -> Dict:
        """Compare API response with previous export file"""
        print("\n" + "="*80)
        print(f"COMPARING WITH EXPORT FILE: {export_file}")
        print("="*80)

        if not os.path.exists(export_file):
            print(f"⚠️  Export file not found: {export_file}")
            return {"success": False, "reason": "file_not_found"}

        with open(export_file, 'r') as f:
            export_data = json.load(f)

        print(f"Export Date: {export_data.get('export_date', 'N/A')}")
        print(f"Export Status: {export_data.get('export_status', {}).get('labels', 'N/A')}")
        print(f"Exported Labels: {len(export_data.get('labels', []))}")

        # Get current labels
        current_result = self.list_labels()
        current_labels = current_result.get("labels", [])

        print(f"\nCurrent Labels: {len(current_labels)}")

        # Compare
        if len(current_labels) != len(export_data.get('labels', [])):
            print(f"⚠️  Label count mismatch!")
            print(f"   Export: {len(export_data.get('labels', []))} labels")
            print(f"   Current: {len(current_labels)} labels")
        else:
            print(f"✅ Label count matches: {len(current_labels)}")

        return {
            "success": True,
            "export_count": len(export_data.get('labels', [])),
            "current_count": len(current_labels),
            "matches": len(current_labels) == len(export_data.get('labels', []))
        }

    def run_full_validation(self, validate_imports: bool = False) -> Dict:
        """Run complete validation suite"""
        print("\n" + "="*80)
        print("OKTA IGA LABELS API VALIDATION")
        print("="*80)
        print(f"Organization: {self.org_name}")
        print(f"Base URL: {self.base_url}")
        print("="*80)

        results = {
            "connection": False,
            "list_labels": False,
            "labels_found": 0,
            "individual_label_tests": [],
            "resource_assignment_tests": []
        }

        # Test 1: API Connection
        if not self.test_api_connection():
            print("\n❌ VALIDATION FAILED: Cannot connect to API")
            return results
        results["connection"] = True

        # Test 2: List Labels
        labels_result = self.list_labels()
        results["list_labels"] = labels_result.get("success", False)

        if not labels_result.get("success"):
            print("\n⚠️  Cannot retrieve labels - OIG may not be enabled")
            return results

        labels = labels_result.get("labels", [])
        results["labels_found"] = len(labels)

        if len(labels) == 0:
            print("\n⚠️  No labels found in environment")
            print("   Expected: 2 labels with no resources assigned")
            return results

        print(f"\n✅ Found {len(labels)} label(s) - validating each...")

        # Test 3: Validate each label
        for label in labels:
            label_name = label.get("name")
            label_id = label.get("labelId")

            if not label_id:
                print(f"⚠️  Label '{label_name}' has no labelId, skipping...")
                continue

            # Get label details
            label_details = self.get_label_by_id(label_name, label_id)

            # Validate structure
            if label_details:
                structure_validation = self.validate_label_structure(label_details)
                results["individual_label_tests"].append({
                    "name": label_name,
                    "label_id": label_id,
                    "retrieved": True,
                    "valid_structure": structure_validation.get("valid", False)
                })

            # Get labelValueId from label values
            label_value_id = None
            values = label.get("values", [])
            if values:
                label_value_id = values[0].get("labelValueId")

            # Get assigned resources (using labelValueId if available)
            if label_value_id:
                resources_result = self.get_label_resources(label_name, label_id, label_value_id)
                results["resource_assignment_tests"].append({
                    "label": label_name,
                    "label_id": label_id,
                    "label_value_id": label_value_id,
                    "resources_count": resources_result.get("count", 0)
                })
            else:
                print(f"⚠️  Label '{label_name}' has no labelValueId, skipping resource query...")
                results["resource_assignment_tests"].append({
                    "label": label_name,
                    "label_id": label_id,
                    "label_value_id": None,
                    "resources_count": 0
                })

        # Test 4: Compare with previous export (if requested)
        if validate_imports:
            export_file = "oig-exports/lowerdecklabs/latest.json"
            self.compare_with_export(export_file)

        # Summary
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"✅ API Connection: {'SUCCESS' if results['connection'] else 'FAILED'}")
        print(f"✅ List Labels: {'SUCCESS' if results['list_labels'] else 'FAILED'}")
        print(f"✅ Labels Found: {results['labels_found']}")
        print(f"✅ Individual Label Tests: {len(results['individual_label_tests'])} passed")
        print(f"✅ Resource Assignment Tests: {len(results['resource_assignment_tests'])} completed")
        print("="*80)

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Validate Okta IGA Labels API integration"
    )
    parser.add_argument(
        "--org-name",
        default=os.environ.get("OKTA_ORG_NAME"),
        help="Okta organization name"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OKTA_BASE_URL", "okta.com"),
        help="Okta base URL"
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("OKTA_API_TOKEN"),
        help="Okta API token"
    )
    parser.add_argument(
        "--validate-imports",
        action="store_true",
        help="Compare with previous export file"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    validator = LabelsAPIValidator(args.org_name, args.base_url, args.api_token)
    results = validator.run_full_validation(args.validate_imports)

    # Save results
    output_file = "labels_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Validation results saved to: {output_file}\n")


if __name__ == "__main__":
    main()
