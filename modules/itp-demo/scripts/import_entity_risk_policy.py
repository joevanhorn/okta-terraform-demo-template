#!/usr/bin/env python3
"""
import_entity_risk_policy.py

Imports entity risk policy and rules from Okta ITP to a local config JSON file.
Each Okta org has exactly one entity risk policy with configurable rules that
determine actions (e.g., UNIVERSAL_LOGOUT) when user risk reaches certain levels.

Usage:
    python3 scripts/import_entity_risk_policy.py
    python3 scripts/import_entity_risk_policy.py --output environments/myorg/config/entity_risk_policy.json
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List, Optional
from datetime import datetime, timezone


class EntityRiskPolicyImporter:
    """Imports entity risk policy from Okta to local config"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = f"https://{org_name}.{base_url}"
        self.api_base = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_entity_risk_policy(self) -> Optional[Dict]:
        """
        Fetch the entity risk policy from Okta.
        Each org has exactly one ENTITY_RISK policy.
        """
        print("=" * 80)
        print("FETCHING ENTITY RISK POLICY FROM OKTA")
        print("=" * 80)
        print()

        url = f"{self.api_base}/policies"
        params = {"type": "ENTITY_RISK"}

        try:
            print("Fetching entity risk policy...")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            policies = response.json()

            if not policies:
                print("  No entity risk policy found (ITP may not be enabled)")
                return None

            # There's exactly one entity risk policy per org
            policy = policies[0]
            print(f"  Found policy: {policy.get('name')} (ID: {policy.get('id')})")
            print(f"     Status: {policy.get('status')}")
            print(f"     Type: {policy.get('type')}")

            return policy

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("  Entity risk policy API not available (ITP may not be enabled)")
                return None
            elif e.response.status_code == 403:
                print("  Access denied. Ensure API token has policy read permissions")
                return None
            else:
                error_msg = str(e)
                try:
                    error_detail = e.response.json()
                    error_msg = error_detail.get("errorSummary", error_msg)
                except Exception:
                    pass
                print(f"  Error fetching entity risk policy: {error_msg}")
                return None
        except Exception as e:
            print(f"  Unexpected error: {e}")
            return None

    def get_policy_rules(self, policy_id: str) -> List[Dict]:
        """Fetch all rules for an entity risk policy"""
        print(f"\nFetching rules for policy {policy_id}...")

        url = f"{self.api_base}/policies/{policy_id}/rules"

        try:
            response = self.session.get(url)
            response.raise_for_status()

            rules = response.json()
            print(f"  Found {len(rules)} rules")

            for rule in rules:
                name = rule.get("name", "Unknown")
                status = rule.get("status", "Unknown")
                actions = (rule.get("actions") or {}).get("entityRisk", {}).get("actions", [])
                conditions = rule.get("conditions") or {}

                risk_level = "Any"
                risk_score = conditions.get("riskScore") or {}
                if risk_score.get("level"):
                    risk_level = risk_score["level"]

                action_str = ", ".join(actions) if actions else "NONE"
                print(f"     - {name} (Status: {status}, Risk: {risk_level}, Action: {action_str})")

            return rules

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except Exception:
                pass
            print(f"  Error fetching rules: {error_msg}")
            return []
        except Exception as e:
            print(f"  Unexpected error: {e}")
            return []

    def transform_rules(self, raw_rules: List[Dict]) -> List[Dict]:
        """Transform raw API rules to config format, stripping read-only fields"""
        print("\nTransforming rules for config file...")

        transformed = []
        for rule in raw_rules:
            transformed_rule = {
                "name": rule.get("name"),
                "status": rule.get("status"),
                "system": rule.get("system", False),
                "conditions": rule.get("conditions", {}),
                "actions": rule.get("actions", {}),
            }

            # Clean up None values
            transformed_rule = {k: v for k, v in transformed_rule.items() if v is not None}

            # Add metadata for reference (read-only)
            transformed_rule["_metadata"] = {
                "id": rule.get("id"),
                "type": rule.get("type"),
                "priority": rule.get("priority"),
                "created": rule.get("created"),
                "lastUpdated": rule.get("lastUpdated"),
            }

            transformed.append(transformed_rule)
            print(f"  {rule.get('name')} (ID: {rule.get('id')})")

        return transformed

    def transform_policy(self, raw_policy: Dict) -> Dict:
        """Transform raw policy to config format metadata"""
        return {
            "id": raw_policy.get("id"),
            "name": raw_policy.get("name"),
            "status": raw_policy.get("status"),
            "type": raw_policy.get("type"),
            "created": raw_policy.get("created"),
            "lastUpdated": raw_policy.get("lastUpdated"),
        }

    def save_to_file(self, policy_meta: Dict, rules: List[Dict], output_file: str):
        """Save entity risk policy config to JSON file"""
        print(f"\nSaving entity risk policy to {output_file}...")

        config = {
            "description": "Entity risk policy synced from Okta Identity Threat Protection",
            "last_synced": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "policy": policy_meta,
            "rules": rules,
            "notes": [
                "This file manages the entity risk policy for Okta Identity Threat Protection (ITP)",
                "Each Okta org has exactly ONE entity risk policy — it cannot be created or deleted",
                "Only the RULES within the policy can be added, updated, or removed",
                "",
                "Rule Structure:",
                "  - name: Display name for the rule",
                "  - status: ACTIVE or INACTIVE",
                "  - system: true for the default catch-all rule (cannot be deleted)",
                "  - conditions.riskScore.level: HIGH, MEDIUM, or LOW",
                "  - actions.entityRisk.actions: ['UNIVERSAL_LOGOUT'] or ['NONE']",
                "",
                "Available Actions:",
                "  - UNIVERSAL_LOGOUT: Terminate all user sessions when risk threshold is met",
                "  - NONE: Detect and log but take no action",
                "",
                "To add a new rule, add an entry to the 'rules' array and run:",
                "  python3 scripts/apply_entity_risk_policy.py --config <this-file>",
                "",
                "To sync from Okta:",
                "  python3 scripts/import_entity_risk_policy.py --output <this-file>",
                "",
                "The '_metadata' field in each rule contains read-only information from Okta",
            ]
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"  Saved {len(rules)} rules")
        return config

    def import_policy(self, output_file: str) -> bool:
        """Run the complete import process"""
        # Fetch policy
        policy = self.get_entity_risk_policy()
        if not policy:
            print("\n  No entity risk policy found — ITP may not be enabled on this org")
            return False

        # Fetch rules
        raw_rules = self.get_policy_rules(policy["id"])

        # Transform
        policy_meta = self.transform_policy(policy)
        transformed_rules = self.transform_rules(raw_rules)

        # Save
        self.save_to_file(policy_meta, transformed_rules, output_file)

        # Summary
        print("\n" + "=" * 80)
        print("IMPORT SUMMARY")
        print("=" * 80)
        print(f"  Policy: {policy_meta.get('name')} (ID: {policy_meta.get('id')})")
        print(f"  Total rules imported: {len(transformed_rules)}")
        print(f"  Output file: {output_file}")
        print("=" * 80)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Import entity risk policy from Okta ITP to local config"
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
        "--output",
        default="config/entity_risk_policy.json",
        help="Output file path"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    importer = EntityRiskPolicyImporter(args.org_name, args.base_url, args.api_token)
    success = importer.import_policy(args.output)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
