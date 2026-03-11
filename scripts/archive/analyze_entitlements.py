#!/usr/bin/env python3
"""
Analyze entitlement structure to identify app-managed vs manual entitlements.

This script examines entitlements from the Okta API to find fields that
differentiate between:
- App-managed/synced entitlements (e.g., from Salesforce, auto-discovered)
- Manually created/BYO (Bring Your Own) entitlements
"""

import os
import sys
import json
from okta_api_manager import OktaAPIManager

def analyze_entitlement_structure(manager: OktaAPIManager):
    """Analyze entitlement structure and categorize by source."""

    print("=== Analyzing Entitlement Structure ===\n")

    # Get all entitlements
    entitlements_response = manager.list_entitlements(limit=200)

    # Handle response format
    if isinstance(entitlements_response, list):
        entitlements = entitlements_response
    elif isinstance(entitlements_response, dict):
        entitlements = entitlements_response.get("entitlements", entitlements_response.get("data", []))
    else:
        print("Error: Unexpected response format")
        return

    print(f"Found {len(entitlements)} entitlements\n")

    if not entitlements:
        print("No entitlements to analyze")
        return

    # Examine first few entitlements in detail
    print("=== Sample Entitlement Structures ===\n")

    for i, ent in enumerate(entitlements[:3]):
        print(f"--- Entitlement {i+1} ---")
        print(json.dumps(ent, indent=2))
        print()

    # Collect all unique fields across entitlements
    all_fields = set()
    for ent in entitlements:
        all_fields.update(ent.keys())

    print(f"=== All Fields Found Across {len(entitlements)} Entitlements ===")
    print(sorted(all_fields))
    print()

    # Look for fields that might indicate source
    potential_source_fields = [
        'source', 'type', 'category', 'managed', 'synchronized',
        'provider', 'origin', 'resourceType', 'resource', 'application',
        'appId', 'app', 'discoverySource', 'custom', 'manual'
    ]

    found_source_fields = [f for f in potential_source_fields if f in all_fields]

    print("=== Potential Source Indicator Fields ===")
    if found_source_fields:
        print(f"Found: {found_source_fields}")
        print()

        # Show values for these fields
        for field in found_source_fields:
            values = set()
            for ent in entitlements:
                if field in ent and ent[field] is not None:
                    val = ent[field]
                    # Handle nested objects
                    if isinstance(val, dict):
                        values.add(f"<dict: {list(val.keys())}>" if val else "<empty dict>")
                    elif isinstance(val, list):
                        values.add(f"<list: {len(val)} items>" if val else "<empty list>")
                    else:
                        values.add(str(val))

            print(f"\n{field}: {sorted(values)}")
    else:
        print("No obvious source indicator fields found")
        print("Will need to examine resource/application relationships")

    print("\n=== Resource Analysis ===")

    # Analyze resource field structure
    resource_types = {}
    for ent in entitlements:
        if 'resource' in ent and ent['resource']:
            res = ent['resource']
            if isinstance(res, dict):
                res_type = res.get('type', 'unknown')
                if res_type not in resource_types:
                    resource_types[res_type] = []
                resource_types[res_type].append(res)

    print(f"\nResource types found: {list(resource_types.keys())}")
    for res_type, resources in resource_types.items():
        print(f"  {res_type}: {len(resources)} entitlements")
        if resources:
            print(f"    Sample fields: {list(resources[0].keys())}")

    # Categorization strategy
    print("\n=== Categorization Strategy ===")
    print("""
Based on Okta documentation:

1. **App-Managed/Synced Entitlements:**
   - Discovered from provisioning-enabled applications
   - Cannot be manually edited (structure/values)
   - Examples: Salesforce profiles, permissions
   - Likely indicators:
     * resource.type might indicate app type
     * May have discoverySource or similar field
     * Resource ORN includes app ID

2. **Manual/Custom/BYO Entitlements:**
   - Created via API or Okta Workflows
   - Can be manually edited
   - "Bring Your Own" entitlements
   - Likely indicators:
     * Different resource type
     * May have 'custom' field or type
     * Created via entitlement bundles API

3. **Policy-Based Entitlements:**
   - Granted via entitlement policies
   - Type changes to "Custom" when granted outside policy
    """)

    # Try to identify patterns
    print("\n=== Pattern Analysis ===")

    app_managed_candidates = []
    manual_candidates = []

    for ent in entitlements:
        ent_id = ent.get('id', 'unknown')
        ent_name = ent.get('name', 'unknown')

        # Check resource field for app info
        resource = ent.get('resource', {})
        if isinstance(resource, dict):
            resource_orn = resource.get('orn', '')

            # If resource ORN contains 'apps:', likely app-managed
            if 'apps:' in resource_orn:
                app_managed_candidates.append({
                    'id': ent_id,
                    'name': ent_name,
                    'resource_orn': resource_orn,
                    'reason': 'Resource ORN contains apps:'
                })
            else:
                manual_candidates.append({
                    'id': ent_id,
                    'name': ent_name,
                    'resource_orn': resource_orn,
                    'reason': 'Resource ORN does not contain apps:'
                })

    print(f"\nApp-managed candidates: {len(app_managed_candidates)}")
    if app_managed_candidates:
        print("  Sample:")
        for item in app_managed_candidates[:3]:
            print(f"    - {item['name']}: {item['resource_orn']}")

    print(f"\nManual/Custom candidates: {len(manual_candidates)}")
    if manual_candidates:
        print("  Sample:")
        for item in manual_candidates[:3]:
            print(f"    - {item['name']}: {item['resource_orn']}")

    # Save detailed analysis
    analysis = {
        'total_entitlements': len(entitlements),
        'all_fields': sorted(all_fields),
        'source_indicator_fields': found_source_fields,
        'resource_types': {k: len(v) for k, v in resource_types.items()},
        'app_managed_count': len(app_managed_candidates),
        'manual_count': len(manual_candidates),
        'sample_entitlements': entitlements[:5]
    }

    with open('entitlement_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)

    print("\n✅ Detailed analysis saved to: entitlement_analysis.json")

def main():
    # Get credentials from environment
    org_name = os.getenv('OKTA_ORG_NAME', 'demo-lowerdecklabs')
    base_url = os.getenv('OKTA_BASE_URL', 'oktapreview.com')
    api_token = os.getenv('OKTA_API_TOKEN')

    if not api_token:
        print("Error: OKTA_API_TOKEN environment variable required")
        print("\nUsage:")
        print("  export OKTA" + "_API_TOKEN=<your-token-here>")
        print("  python3 analyze_entitlements.py")
        sys.exit(1)

    # Initialize manager
    manager = OktaAPIManager(org_name, base_url, api_token)

    # Run analysis
    analyze_entitlement_structure(manager)

if __name__ == "__main__":
    main()
