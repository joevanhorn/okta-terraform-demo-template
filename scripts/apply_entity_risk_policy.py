#!/usr/bin/env python3
"""
apply_entity_risk_policy.py

Applies entity risk policy rule configuration from config JSON to Okta ITP.

Each Okta org has exactly one entity risk policy (immutable). This script
manages the RULES within that policy: creating new rules, updating existing
rules, and optionally deleting rules not present in the config.

Usage:
    python3 scripts/apply_entity_risk_policy.py --config config/entity_risk_policy.json --dry-run
    python3 scripts/apply_entity_risk_policy.py --config config/entity_risk_policy.json
    python3 scripts/apply_entity_risk_policy.py --config config/entity_risk_policy.json --delete-removed
"""

import os
import sys
import json
import requests
import argparse
from typing import List, Dict, Optional


class EntityRiskPolicyApplier:
    """Applies entity risk policy rule configuration to Okta"""

    def __init__(self, org_name: str, base_url: str, api_token: str, dry_run: bool = False):
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
        self.dry_run = dry_run

    def load_config(self, config_file: str) -> Optional[Dict]:
        """Load entity risk policy config from file"""
        print("\n" + "=" * 80)
        print("LOADING ENTITY RISK POLICY CONFIG")
        print("=" * 80)

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            rules = config.get("rules", [])
            policy = config.get("policy", {})
            print(f"Loaded {len(rules)} rules from config")
            print(f"   Policy ID: {policy.get('id', 'Unknown')}")

            return config

        except FileNotFoundError:
            print(f"Config file not found: {config_file}")
            return None
        except Exception as e:
            print(f"Error loading config: {e}")
            return None

    def get_policy_id(self) -> Optional[str]:
        """Fetch the entity risk policy ID from Okta"""
        url = f"{self.api_base}/policies"
        params = {"type": "ENTITY_RISK"}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()

            policies = response.json()
            if not policies:
                print("  No entity risk policy found (ITP may not be enabled)")
                return None

            return policies[0].get("id")

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except Exception:
                pass
            print(f"  Error fetching policy: {error_msg}")
            return None

    def get_existing_rules(self, policy_id: str) -> Dict[str, Dict]:
        """Fetch existing rules from Okta, indexed by name"""
        print("\n" + "=" * 80)
        print("FETCHING EXISTING RULES FROM OKTA")
        print("=" * 80)

        url = f"{self.api_base}/policies/{policy_id}/rules"

        try:
            response = self.session.get(url)
            response.raise_for_status()

            rules = response.json()
            rules_by_name = {}
            for rule in rules:
                rule_name = rule.get("name")
                rules_by_name[rule_name] = rule

            print(f"Found {len(rules_by_name)} existing rules in Okta")
            for name, rule in rules_by_name.items():
                system = " (system)" if rule.get("system") else ""
                print(f"   - {name} (ID: {rule.get('id')}){system}")

            return rules_by_name

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("  Policy rules API not available")
                return {}
            elif e.response.status_code == 403:
                print("  Access denied")
                return {}
            else:
                print(f"  Error fetching existing rules: {e}")
                return {}
        except Exception as e:
            print(f"  Unexpected error: {e}")
            return {}

    def create_rule(self, policy_id: str, rule_config: Dict) -> Dict:
        """Create a new rule in the entity risk policy"""
        url = f"{self.api_base}/policies/{policy_id}/rules"

        # Build payload — strip metadata and system flag
        payload = {
            "name": rule_config.get("name"),
            "status": rule_config.get("status", "ACTIVE"),
            "conditions": rule_config.get("conditions", {}),
            "actions": rule_config.get("actions", {}),
        }

        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would create rule: {rule_config.get('name')}")
                return {"status": "dry_run"}

            response = self.session.post(url, json=payload)
            response.raise_for_status()

            return {"status": "success", "rule": response.json()}

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except Exception:
                pass
            return {"status": "error", "error": error_msg}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def update_rule(self, policy_id: str, rule_id: str, rule_config: Dict) -> Dict:
        """Update an existing rule"""
        url = f"{self.api_base}/policies/{policy_id}/rules/{rule_id}"

        payload = {
            "id": rule_id,
            "name": rule_config.get("name"),
            "status": rule_config.get("status", "ACTIVE"),
            "conditions": rule_config.get("conditions", {}),
            "actions": rule_config.get("actions", {}),
        }

        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would update rule: {rule_config.get('name')} (ID: {rule_id})")
                return {"status": "dry_run"}

            response = self.session.put(url, json=payload)
            response.raise_for_status()

            return {"status": "success", "rule": response.json()}

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except Exception:
                pass
            return {"status": "error", "error": error_msg}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def delete_rule(self, policy_id: str, rule_id: str, rule_name: str) -> Dict:
        """Delete a rule from the entity risk policy"""
        url = f"{self.api_base}/policies/{policy_id}/rules/{rule_id}"

        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would delete rule: {rule_name} (ID: {rule_id})")
                return {"status": "dry_run"}

            response = self.session.delete(url)
            response.raise_for_status()

            return {"status": "success"}

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("errorSummary", error_msg)
            except Exception:
                pass
            return {"status": "error", "error": error_msg}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def plan_changes(self, config_rules: List[Dict], existing_rules: Dict[str, Dict],
                     delete_removed: bool) -> Dict:
        """Determine what changes need to be made"""
        print("\n" + "=" * 80)
        print("PLANNING CHANGES")
        print("=" * 80)

        changes = {
            "create": [],
            "update": [],
            "delete": []
        }

        matched_existing = set()

        for config_rule in config_rules:
            rule_name = config_rule.get("name")
            metadata_id = config_rule.get("_metadata", {}).get("id") if config_rule.get("_metadata") else None

            if rule_name in existing_rules:
                existing_rule = existing_rules[rule_name]
                existing_id = existing_rule.get("id")
                matched_existing.add(rule_name)

                # Check if anything actually changed
                # Normalize None to {} for comparison (API returns null for catch-all)
                existing_actions = existing_rule.get("actions") or {}
                config_actions = config_rule.get("actions") or {}
                existing_conditions = existing_rule.get("conditions") or {}
                config_conditions = config_rule.get("conditions") or {}
                existing_status = existing_rule.get("status")
                config_status = config_rule.get("status")

                if (existing_actions != config_actions or
                        existing_conditions != config_conditions or
                        existing_status != config_status):
                    changes["update"].append({
                        "config": config_rule,
                        "existing_id": existing_id,
                        "existing": existing_rule
                    })
                    print(f"  UPDATE: {rule_name} (ID: {existing_id})")
                else:
                    print(f"  NO CHANGE: {rule_name} (ID: {existing_id})")

            elif metadata_id:
                matched_existing.add(rule_name)
                changes["update"].append({
                    "config": config_rule,
                    "existing_id": metadata_id,
                    "existing": None
                })
                print(f"  UPDATE: {rule_name} (ID from metadata: {metadata_id})")

            else:
                changes["create"].append({"config": config_rule})
                print(f"  CREATE: {rule_name}")

        if delete_removed:
            for existing_name, existing_rule in existing_rules.items():
                if existing_name not in matched_existing:
                    # Never delete system rules (catch-all)
                    if existing_rule.get("system"):
                        print(f"  SKIP DELETE (system rule): {existing_name}")
                        continue

                    existing_id = existing_rule.get("id")
                    id_matched = any(
                        r.get("_metadata", {}).get("id") == existing_id
                        for r in config_rules
                    )

                    if not id_matched:
                        changes["delete"].append({"existing": existing_rule})
                        print(f"  DELETE: {existing_name} (ID: {existing_rule.get('id')})")

        print(f"\nPlanned changes:")
        print(f"  Create: {len(changes['create'])}")
        print(f"  Update: {len(changes['update'])}")
        print(f"  Delete: {len(changes['delete'])}")

        return changes

    def apply_changes(self, policy_id: str, changes: Dict) -> Dict:
        """Execute the planned changes"""
        print("\n" + "=" * 80)
        if self.dry_run:
            print("APPLYING CHANGES (DRY RUN)")
        else:
            print("APPLYING CHANGES")
        print("=" * 80)

        results = {
            "create": [],
            "update": [],
            "delete": [],
            "summary": {
                "total": 0,
                "success": 0,
                "errors": 0,
                "dry_run": self.dry_run
            }
        }

        if changes["create"]:
            print("\n--- Creating New Rules ---")
            for item in changes["create"]:
                rule_config = item["config"]
                rule_name = rule_config.get("name", "Unknown")

                print(f"\n{rule_name}:")
                result = self.create_rule(policy_id, rule_config)
                result["rule_name"] = rule_name
                results["create"].append(result)
                results["summary"]["total"] += 1

                if result["status"] in ("success", "dry_run"):
                    if result["status"] == "success":
                        print(f"Created successfully")
                    results["summary"]["success"] += 1
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    results["summary"]["errors"] += 1

        if changes["update"]:
            print("\n--- Updating Existing Rules ---")
            for item in changes["update"]:
                rule_config = item["config"]
                existing_id = item["existing_id"]
                rule_name = rule_config.get("name", "Unknown")

                print(f"\n{rule_name} (ID: {existing_id}):")
                result = self.update_rule(policy_id, existing_id, rule_config)
                result["rule_name"] = rule_name
                result["rule_id"] = existing_id
                results["update"].append(result)
                results["summary"]["total"] += 1

                if result["status"] in ("success", "dry_run"):
                    if result["status"] == "success":
                        print(f"Updated successfully")
                    results["summary"]["success"] += 1
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    results["summary"]["errors"] += 1

        if changes["delete"]:
            print("\n--- Deleting Removed Rules ---")
            for item in changes["delete"]:
                existing_rule = item["existing"]
                rule_id = existing_rule.get("id")
                rule_name = existing_rule.get("name", "Unknown")

                print(f"\n{rule_name} (ID: {rule_id}):")
                result = self.delete_rule(policy_id, rule_id, rule_name)
                result["rule_name"] = rule_name
                result["rule_id"] = rule_id
                results["delete"].append(result)
                results["summary"]["total"] += 1

                if result["status"] in ("success", "dry_run"):
                    if result["status"] == "success":
                        print(f"Deleted successfully")
                    results["summary"]["success"] += 1
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    results["summary"]["errors"] += 1

        return results

    def run(self, config_file: str, delete_removed: bool = False):
        """Main execution"""
        print("=" * 80)
        if self.dry_run:
            print("ENTITY RISK POLICY APPLIER (DRY RUN MODE)")
        else:
            print("ENTITY RISK POLICY APPLIER")
        print("=" * 80)

        # Load config
        config = self.load_config(config_file)
        if not config:
            return False

        config_rules = config.get("rules", [])

        # Get the policy ID from Okta (or from config)
        config_policy_id = config.get("policy", {}).get("id")

        print(f"\nResolving entity risk policy ID...")
        policy_id = self.get_policy_id()
        if not policy_id:
            if config_policy_id:
                print(f"  Using policy ID from config: {config_policy_id}")
                policy_id = config_policy_id
            else:
                print("  Cannot determine policy ID")
                return False
        else:
            print(f"  Policy ID: {policy_id}")

        # Get existing rules from Okta
        existing_rules = self.get_existing_rules(policy_id)

        # Plan changes
        changes = self.plan_changes(config_rules, existing_rules, delete_removed)

        # Check if there are any changes
        total_changes = len(changes["create"]) + len(changes["update"]) + len(changes["delete"])
        if total_changes == 0:
            print("\nNo changes needed — config matches Okta")
            return True

        # Apply changes
        results = self.apply_changes(policy_id, changes)

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total operations: {results['summary']['total']}")
        print(f"  Created: {len(results['create'])}")
        print(f"  Updated: {len(results['update'])}")
        print(f"  Deleted: {len(results['delete'])}")
        print(f"Successful: {results['summary']['success']}")
        print(f"Errors: {results['summary']['errors']}")
        if self.dry_run:
            print("\nDRY RUN MODE — No changes were made to Okta")
        print("=" * 80)

        return results['summary']['errors'] == 0


def main():
    parser = argparse.ArgumentParser(
        description="Apply entity risk policy rules from config to Okta"
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
        "--config",
        default="config/entity_risk_policy.json",
        help="Entity risk policy config file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--delete-removed",
        action="store_true",
        help="Delete rules that exist in Okta but not in config (default: false)"
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    applier = EntityRiskPolicyApplier(
        args.org_name,
        args.base_url,
        args.api_token,
        dry_run=args.dry_run
    )

    success = applier.run(args.config, delete_removed=args.delete_removed)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
