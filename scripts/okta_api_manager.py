#!/usr/bin/env python3
"""
okta_api_manager.py

Manages Okta OIG governance Labels and Resource Owners via the API.

API-ONLY operations (no Terraform resource as of okta/okta v7.0.0):
- Assigning labels to resources (/governance/api/v1/resource-labels/assign)

ALSO AVAILABLE IN TERRAFORM (provider v6.13.0+), kept here for config-driven forks:
- Label definitions - okta_label
- Resource Owners - okta_resource_owner

TERRAFORM-MANAGED Resources (NOT in this script):
- Entitlements - okta_entitlement / okta_entitlement_bundle (okta_principal_entitlements is a read-only data source)
- Access Certification - okta_campaign / okta_review
- Access Requests - okta_request_condition / okta_request_sequence / okta_request_setting_*
- Resource Catalog - okta_catalog_entry_* data sources (read-only)
- Resource Sets - okta_resource_set

Usage:
  # Export API-only resources (Labels and Resource Owners)
  python okta_api_manager.py --action export --output export.json \
    --export-labels --export-owners --resource-orns <orn1> <orn2>

  # Apply labels and resource owners from config
  python okta_api_manager.py --action apply --config config.json

  # Query current labels and resource owners
  python okta_api_manager.py --action query --config config.json
"""

import argparse
import json
import sys
import requests
from typing import List, Dict, Optional
import time


class OktaAPIManager:
    """Manages Okta OIG resources via REST API"""
    
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

        # Rate limit tracking
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.rate_limit_warning_threshold = 10  # Warn when fewer than this many requests remain
    
    def _update_rate_limit_info(self, response: requests.Response):
        """Update rate limit tracking from response headers"""
        try:
            self.rate_limit_remaining = int(response.headers.get('X-Rate-Limit-Remaining', 0))
            self.rate_limit_reset = int(response.headers.get('X-Rate-Limit-Reset', 0))

            # Warn if approaching rate limit
            if self.rate_limit_remaining is not None and self.rate_limit_remaining <= self.rate_limit_warning_threshold:
                print(f"  ⚠️  Rate limit warning: {self.rate_limit_remaining} requests remaining")
        except (ValueError, TypeError):
            pass  # Headers might not be integers or might be missing

    def _wait_for_rate_limit_reset(self):
        """Wait until rate limit reset time if we're close to the limit"""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 1:
            if self.rate_limit_reset:
                wait_time = max(self.rate_limit_reset - time.time() + 1, 1)  # Add 1 second buffer
                print(f"  ⏳ Rate limit nearly exhausted. Waiting {wait_time:.0f} seconds for reset...")
                time.sleep(wait_time)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make API request with rate limit awareness and retry logic"""
        max_retries = 5  # Increased for rate limit retries
        base_retry_delay = 1

        # Check if we should wait before making the request
        self._wait_for_rate_limit_reset()

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                # Update rate limit tracking from response headers
                self._update_rate_limit_info(response)

                # Handle rate limiting (429)
                if response.status_code == 429:
                    # Use X-Rate-Limit-Reset header for accurate wait time
                    reset_time = int(response.headers.get('X-Rate-Limit-Reset', time.time() + 60))
                    wait_time = max(reset_time - time.time() + 1, 1)  # Add 1 second buffer

                    print(f"  ⚠️  Rate limited (429). Waiting {wait_time:.0f} seconds until reset...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.HTTPError as e:
                # Don't retry on 4xx errors (except 429 which is handled above)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise

                if attempt == max_retries - 1:
                    raise

                # Exponential backoff for other errors
                wait_time = base_retry_delay * (2 ** attempt)
                print(f"  ⚠️  Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"     Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise

                # Exponential backoff
                wait_time = base_retry_delay * (2 ** attempt)
                print(f"  ⚠️  Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"     Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        raise Exception("Max retries exceeded")
    
    # ==================== Resource Owners ====================
    
    def assign_resource_owners(self, principal_orns: List[str], resource_orns: List[str]) -> Dict:
        """Assign owners to resources"""
        url = f"{self.base_url}/governance/api/v1/resource-owners"
        payload = {
            "principalOrns": principal_orns,
            "resourceOrns": resource_orns
        }
        
        print(f"Assigning {len(principal_orns)} owners to {len(resource_orns)} resources...")
        response = self._make_request("PUT", url, json=payload)
        return response.json()
    
    def list_resource_owners(self, parent_resource_orn: str, include_parent: bool = False) -> Dict:
        """List all resources with assigned owners for a parent resource"""
        url = f"{self.base_url}/governance/api/v1/resource-owners"
        
        # URL encode the filter
        filter_expr = f'parentResourceOrn eq "{parent_resource_orn}"'
        params = {
            "filter": filter_expr,
            "limit": 200
        }
        
        if include_parent:
            params["include"] = "parent_resource_owner"
        
        response = self._make_request("GET", url, params=params)
        return response.json()
    
    def update_resource_owners(self, resource_orn: str, operations: List[Dict]) -> Dict:
        """Update resource owners using PATCH operations"""
        url = f"{self.base_url}/governance/api/v1/resource-owners"
        payload = {
            "resourceOrn": resource_orn,
            "data": operations
        }
        
        response = self._make_request("PATCH", url, json=payload)
        return response.json()
    
    def remove_resource_owner(self, resource_orn: str, principal_orn: str) -> Dict:
        """Remove a specific owner from a resource"""
        operations = [{
            "op": "REMOVE",
            "path": "/principalOrn",
            "value": principal_orn
        }]
        return self.update_resource_owners(resource_orn, operations)
    
    def list_unassigned_resources(self, parent_resource_orn: str, resource_type: Optional[str] = None) -> Dict:
        """List resources without assigned owners"""
        url = f"{self.base_url}/governance/api/v1/resource-owners/catalog/resources"
        
        filter_expr = f'parentResourceOrn eq "{parent_resource_orn}"'
        if resource_type:
            filter_expr += f' AND resource.type eq "{resource_type}"'
        
        params = {
            "filter": filter_expr,
            "limit": 200
        }
        
        response = self._make_request("GET", url, params=params)
        return response.json()
    
    # ==================== Labels ====================
    
    def create_label(self, name: str, description: str = "") -> Dict:
        """Create a governance label"""
        url = f"{self.base_url}/governance/api/v1/labels"
        payload = {
            "name": name,
            "description": description or f"Governance label: {name}"
        }
        
        try:
            response = self._make_request("POST", url, json=payload)
            print(f"Created label: {name}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"Label already exists: {name}")
                return {"name": name, "exists": True}
            raise
    
    def list_labels(self) -> Dict:
        """List all governance labels"""
        url = f"{self.base_url}/governance/api/v1/labels"

        response = self._make_request("GET", url)
        return response.json()

    def get_label_id_from_name(self, label_name: str) -> Optional[str]:
        """Get labelId from label name by listing all labels"""
        labels_response = self.list_labels()
        for label in labels_response.get("data", []):
            if label.get("name") == label_name:
                return label.get("labelId")
        return None

    def get_label_value_id_from_name(self, label_name: str) -> Optional[str]:
        """Get labelValueId from label name by listing all labels"""
        labels_response = self.list_labels()
        for label in labels_response.get("data", []):
            if label.get("name") == label_name:
                # Get the first labelValueId from values array
                values = label.get("values", [])
                if values:
                    return values[0].get("labelValueId")
        return None

    def get_label(self, label_name: str) -> Optional[Dict]:
        """Get a specific label by name (looks up labelId first)"""
        label_id = self.get_label_id_from_name(label_name)
        if not label_id:
            print(f"Label '{label_name}' not found")
            return None

        url = f"{self.base_url}/governance/api/v1/labels/{label_id}"

        try:
            response = self._make_request("GET", url)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def apply_labels_to_resources(self, label_name: str, resource_orns: List[str]) -> Dict:
        """Apply a label to one or more resources (looks up labelId first)"""
        label_id = self.get_label_id_from_name(label_name)
        if not label_id:
            raise ValueError(f"Label '{label_name}' not found")

        url = f"{self.base_url}/governance/api/v1/labels/{label_id}/resources"
        payload = {"resourceOrns": resource_orns}

        response = self._make_request("PUT", url, json=payload)
        print(f"Applied label '{label_name}' to {len(resource_orns)} resources")
        return response.json()

    def list_all_resource_labels(self, limit: int = 200) -> Dict:
        """List all resource-label assignments"""
        url = f"{self.base_url}/governance/api/v1/resource-labels"
        params = {"limit": limit}

        response = self._make_request("GET", url, params=params)
        return response.json()

    def list_resources_by_label(self, label_name: str) -> Dict:
        """List all resources with a specific label using filter parameter"""
        # Get labelValueId for the label name
        label_value_id = self.get_label_value_id_from_name(label_name)
        if not label_value_id:
            raise ValueError(f"Label '{label_name}' not found")

        # Use filter parameter to query resources with this label
        url = f"{self.base_url}/governance/api/v1/resource-labels"
        filter_expr = f'labelValueId eq "{label_value_id}"'
        params = {
            "filter": filter_expr,
            "limit": 200
        }

        response = self._make_request("GET", url, params=params)
        return response.json()

    def remove_label_from_resources(self, label_name: str, resource_orns: List[str]) -> Dict:
        """Remove a label from resources (looks up labelId first)"""
        label_id = self.get_label_id_from_name(label_name)
        if not label_id:
            raise ValueError(f"Label '{label_name}' not found")

        url = f"{self.base_url}/governance/api/v1/labels/{label_id}/resources"
        payload = {"resourceOrns": resource_orns}

        response = self._make_request("DELETE", url, json=payload)
        print(f"Removed label '{label_name}' from {len(resource_orns)} resources")
        return response.json()

    def create_label_with_values(self, name: str, description: str, values: List[Dict]) -> Dict:
        """
        Create a governance label with multiple values in a single API call.

        Args:
            name: Label key name (e.g., "Compliance")
            description: Label description
            values: List of value dicts, each with 'name' and optional 'metadata'
                    Example: [{"name": "SOX", "metadata": {"additionalProperties": {"backgroundColor": "blue"}}}]

        Returns:
            Label object with labelId and array of values with labelValueIds

        Example:
            manager.create_label_with_values(
                "Compliance",
                "Compliance framework",
                [
                    {"name": "SOX", "metadata": {"additionalProperties": {"backgroundColor": "blue"}}},
                    {"name": "GDPR", "metadata": {"additionalProperties": {"backgroundColor": "blue"}}},
                    {"name": "PII", "metadata": {"additionalProperties": {"backgroundColor": "blue"}}}
                ]
            )
        """
        url = f"{self.base_url}/governance/api/v1/labels"
        payload = {
            "name": name,
            "description": description or f"Governance label: {name}",
            "values": values
        }

        try:
            response = self._make_request("POST", url, json=payload)
            result = response.json()
            print(f"Created label '{name}' with {len(values)} values")
            for value in result.get("values", []):
                print(f"  - {value.get('name')}: {value.get('labelValueId')}")
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"Label '{name}' already exists")
                return {"name": name, "exists": True}
            raise

    def get_label_value_id(self, label_name: str, value_name: str) -> Optional[str]:
        """
        Get labelValueId for a specific label value.

        Args:
            label_name: Label key name (e.g., "Compliance")
            value_name: Label value name (e.g., "SOX")

        Returns:
            labelValueId or None if not found

        Example:
            sox_value_id = manager.get_label_value_id("Compliance", "SOX")
        """
        labels_response = self.list_labels()
        for label in labels_response.get("data", []):
            if label.get("name") == label_name:
                values = label.get("values", [])
                for value in values:
                    if value.get("name") == value_name:
                        return value.get("labelValueId")
        return None

    def assign_label_values_to_resources(self, label_value_ids: List[str], resource_orns: List[str]) -> Dict:
        """
        Assign specific label values to resources using the /resource-labels/assign endpoint.

        This is the correct way to assign label values to resources - you assign
        labelValueIds (not labelIds) to resource ORNs.

        Args:
            label_value_ids: List of labelValueIds to assign
            resource_orns: List of resource ORNs

        Returns:
            API response

        Example:
            # Assign SOX label value to 4 applications
            sox_value_id = manager.get_label_value_id("Compliance", "SOX")
            manager.assign_label_values_to_resources(
                [sox_value_id],
                [
                    "orn:okta:application:00omx5xxhePEbjFNp1d7:apps:0oamxiwg4zsrWaeJF1d7",
                    "orn:okta:application:00omx5xxhePEbjFNp1d7:apps:0oan4ssz4lmqTnQry1d7"
                ]
            )
        """
        url = f"{self.base_url}/governance/api/v1/resource-labels/assign"
        payload = {
            "resourceOrns": resource_orns,
            "labelValueIds": label_value_ids
        }

        print(f"DEBUG: API Request Details:")
        print(f"  URL: {url}")
        print(f"  Payload: {json.dumps(payload, indent=2)}")

        try:
            response = self._make_request("POST", url, json=payload)
            print(f"Assigned {len(label_value_ids)} label value(s) to {len(resource_orns)} resource(s)")
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Print error details for debugging
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = f"\nResponse body: {e.response.text}"
                except:
                    pass
            print(f"Error assigning labels: {e}{error_detail}")
            print(f"DEBUG: Failed payload was: {json.dumps(payload, indent=2)}")
            raise

    # ==================== Helper Methods ====================

    def build_user_orn(self, user_id: str) -> str:
        """Build ORN for a user"""
        return f"orn:okta:directory:{self.org_name}:users:{user_id}"

    def build_group_orn(self, group_id: str) -> str:
        """Build ORN for a group"""
        return f"orn:okta:directory:{self.org_name}:groups:{group_id}"

    def build_app_orn(self, app_id: str, app_type: str = "oauth2") -> str:
        """Build ORN for an application"""
        return f"orn:okta:idp:{self.org_name}:apps:{app_type}:{app_id}"

    def build_entitlement_bundle_orn(self, bundle_id: str) -> str:
        """Build ORN for an entitlement bundle"""
        return f"orn:okta:governance:{self.org_name}:entitlement-bundles:{bundle_id}"


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file"""
    with open(config_file, 'r') as f:
        return json.load(f)


def apply_configuration(manager: OktaAPIManager, config: Dict):
    """Apply resource owners and labels from configuration"""
    print("\n=== Applying Resource Owners and Labels ===\n")
    
    # Create labels
    if "labels" in config:
        print("Creating labels...")
        for label in config["labels"]:
            manager.create_label(
                name=label.get("name"),
                description=label.get("description", "")
            )
    
    # Assign resource owners
    if "resource_owners" in config:
        print("\nAssigning resource owners...")
        for assignment in config["resource_owners"]:
            principal_orns = [
                manager.build_user_orn(uid) if assignment["principal_type"] == "user"
                else manager.build_group_orn(uid)
                for uid in assignment["principal_ids"]
            ]
            
            resource_type = assignment.get("resource_type", "app")
            if resource_type == "app":
                resource_orns = [
                    manager.build_app_orn(rid, assignment.get("app_type", "oauth2"))
                    for rid in assignment["resource_ids"]
                ]
            elif resource_type == "group":
                resource_orns = [manager.build_group_orn(rid) for rid in assignment["resource_ids"]]
            else:
                resource_orns = assignment["resource_orns"]
            
            manager.assign_resource_owners(principal_orns, resource_orns)
    
    # Apply labels to resources
    if "label_assignments" in config:
        print("\nApplying labels to resources...")
        for assignment in config["label_assignments"]:
            label_name = assignment["label_name"]
            
            resource_type = assignment.get("resource_type", "app")
            if resource_type == "app":
                resource_orns = [
                    manager.build_app_orn(rid, assignment.get("app_type", "oauth2"))
                    for rid in assignment["resource_ids"]
                ]
            elif resource_type == "group":
                resource_orns = [manager.build_group_orn(rid) for rid in assignment["resource_ids"]]
            else:
                resource_orns = assignment["resource_orns"]
            
            manager.apply_labels_to_resources(label_name, resource_orns)
    
    print("\n✅ Configuration applied successfully!")


def destroy_configuration(manager: OktaAPIManager, config: Dict):
    """Remove resource owners and labels"""
    print("\n=== Removing Resource Owners and Labels ===\n")
    
    # Remove label assignments
    if "label_assignments" in config:
        print("Removing label assignments...")
        for assignment in config["label_assignments"]:
            label_name = assignment["label_name"]
            
            resource_type = assignment.get("resource_type", "app")
            if resource_type == "app":
                resource_orns = [
                    manager.build_app_orn(rid, assignment.get("app_type", "oauth2"))
                    for rid in assignment["resource_ids"]
                ]
            elif resource_type == "group":
                resource_orns = [manager.build_group_orn(rid) for rid in assignment["resource_ids"]]
            else:
                resource_orns = assignment["resource_orns"]
            
            try:
                manager.remove_label_from_resources(label_name, resource_orns)
            except Exception as e:
                print(f"Warning: Could not remove labels: {e}")
    
    # Remove resource owners
    if "resource_owners" in config:
        print("\nRemoving resource owners...")
        for assignment in config["resource_owners"]:
            principal_orns = [
                manager.build_user_orn(uid) if assignment["principal_type"] == "user"
                else manager.build_group_orn(uid)
                for uid in assignment["principal_ids"]
            ]
            
            resource_type = assignment.get("resource_type", "app")
            if resource_type == "app":
                resource_orns = [
                    manager.build_app_orn(rid, assignment.get("app_type", "oauth2"))
                    for rid in assignment["resource_ids"]
                ]
            elif resource_type == "group":
                resource_orns = [manager.build_group_orn(rid) for rid in assignment["resource_ids"]]
            else:
                resource_orns = assignment["resource_orns"]
            
            for resource_orn in resource_orns:
                for principal_orn in principal_orns:
                    try:
                        manager.remove_resource_owner(resource_orn, principal_orn)
                    except Exception as e:
                        print(f"Warning: Could not remove owner: {e}")
    
    print("\n✅ Configuration destroyed successfully!")


def export_labels_only(manager: OktaAPIManager) -> Dict:
    """Export only governance labels"""
    print("Exporting labels...")
    labels_data = []

    try:
        labels_response = manager.list_labels()
        for label in labels_response.get("data", []):
            label_name = label.get("name")
            try:
                # Get resources for this label
                resources = manager.list_resources_by_label(label_name)
                labels_data.append({
                    "name": label_name,
                    "description": label.get("description", ""),
                    "resources": resources.get("data", [])
                })
                print(f"  ✅ {label_name}: {len(resources.get('data', []))} resources")
            except Exception as e:
                print(f"  ⚠️  Could not get resources for label '{label_name}': {e}")

        print(f"✅ Exported {len(labels_data)} labels")
        return {"labels": labels_data, "status": "success"}

    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [400, 404]:
            print("  ℹ️  Labels not available (OIG may not be enabled or no labels exist)")
            return {"labels": [], "status": "not_available", "reason": str(e)}
        print(f"  ❌ Labels export failed: {e}")
        return {"labels": [], "status": "error", "reason": str(e)}
    except Exception as e:
        print(f"  ❌ Labels export failed: {e}")
        return {"labels": [], "status": "error", "reason": str(e)}


def export_resource_owners_only(manager: OktaAPIManager, resource_orns: List[str] = None) -> Dict:
    """Export only resource owners for specified resources"""
    print("Exporting resource owners...")
    resource_owners_data = []

    if not resource_orns:
        print("  ℹ️  No resource ORNs specified - skipping resource owners export")
        print("  ℹ️  Provide resource ORNs to export their owners")
        return {"resource_owners": [], "status": "skipped", "reason": "no_resources_specified"}

    try:
        for resource_orn in resource_orns:
            try:
                owners = manager.list_resource_owners(resource_orn)
                if owners.get("data"):
                    resource_owners_data.append({
                        "resource_orn": resource_orn,
                        "owners": owners.get("data", [])
                    })
                    print(f"  ✅ {resource_orn}: {len(owners.get('data', []))} owners")
            except Exception as e:
                print(f"  ⚠️  Could not get owners for {resource_orn}: {e}")

        print(f"✅ Exported owners for {len(resource_owners_data)} resources")
        return {"resource_owners": resource_owners_data, "status": "success"}

    except Exception as e:
        print(f"  ❌ Resource owners export failed: {e}")
        return {"resource_owners": [], "status": "error", "reason": str(e)}


def export_all_oig_resources(manager: OktaAPIManager, output_file: str,
                            export_labels: bool = True,
                            export_owners: bool = False,
                            resource_orns: List[str] = None):
    """Export OIG API-only resources (Labels and Resource Owners) to a JSON file"""
    print("\n=== Exporting OIG API-Only Resources ===\n")

    export_data = {
        "export_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "okta_org": manager.org_name,
        "okta_base_url": manager.base_url.replace(f"https://{manager.org_name}.", ""),
        "export_status": {}
    }

    # Export labels (optional)
    if export_labels:
        labels_result = export_labels_only(manager)
        export_data["labels"] = labels_result.get("labels", [])
        export_data["export_status"]["labels"] = labels_result.get("status")
        print()

    # Export resource owners (optional)
    if export_owners:
        owners_result = export_resource_owners_only(manager, resource_orns)
        export_data["resource_owners"] = owners_result.get("resource_owners", [])
        export_data["export_status"]["resource_owners"] = owners_result.get("status")
        print()

    # Write to file
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    # Summary
    print(f"\n{'='*50}")
    print(f"📄 Export saved to: {output_file}")
    print(f"\n📊 Export Summary:")
    if export_labels:
        status = export_data["export_status"].get("labels", "unknown")
        count = len(export_data.get("labels", []))
        emoji = "✅" if status == "success" else "⚠️" if status == "not_available" else "❌"
        print(f"  {emoji} Labels: {count} ({status})")

    if export_owners:
        status = export_data["export_status"].get("resource_owners", "unknown")
        count = len(export_data.get("resource_owners", []))
        emoji = "✅" if status == "success" else "⚠️" if status == "skipped" else "❌"
        print(f"  {emoji} Resource Owners: {count} ({status})")

    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Manage Okta OIG Resource Owners and Labels (API-only resources)"
    )
    parser.add_argument(
        "--action",
        choices=["apply", "destroy", "query", "export"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration JSON file (required for apply/destroy)"
    )
    parser.add_argument(
        "--output",
        help="Output file for export action"
    )
    parser.add_argument(
        "--org-name",
        help="Okta organization name (overrides config)"
    )
    parser.add_argument(
        "--base-url",
        default="okta.com",
        help="Okta base URL (default: okta.com)"
    )
    parser.add_argument(
        "--api-token",
        help="Okta API token (overrides config)"
    )
    parser.add_argument(
        "--export-labels",
        action="store_true",
        default=True,
        help="Export governance labels (default: True)"
    )
    parser.add_argument(
        "--export-owners",
        action="store_true",
        help="Export resource owners (default: False, requires --resource-orns)"
    )
    parser.add_argument(
        "--resource-orns",
        nargs='+',
        help="List of resource ORNs to export owners for"
    )

    args = parser.parse_args()

    # Get credentials
    if args.config:
        config = load_config(args.config)
        org_name = args.org_name or config.get("okta_org_name")
        api_token = args.api_token or config.get("okta_api_token")
    else:
        config = {}
        org_name = args.org_name
        api_token = args.api_token

    if not org_name or not api_token:
        print("Error: Okta org name and API token required")
        sys.exit(1)

    # Initialize manager
    manager = OktaAPIManager(org_name, args.base_url, api_token)

    # Perform action
    if args.action == "apply":
        if not args.config:
            print("Error: --config required for apply action")
            sys.exit(1)
        apply_configuration(manager, config)
    elif args.action == "destroy":
        if not args.config:
            print("Error: --config required for destroy action")
            sys.exit(1)
        destroy_configuration(manager, config)
    elif args.action == "export":
        output_file = args.output or f"oig_export_{manager.org_name}_{int(time.time())}.json"
        export_all_oig_resources(
            manager,
            output_file,
            export_labels=args.export_labels,
            export_owners=args.export_owners,
            resource_orns=args.resource_orns
        )
    elif args.action == "query":
        # Query current state
        print("\n=== Current State ===\n")

        print("Labels:")
        labels = manager.list_labels()
        for label in labels.get("data", []):
            print(f"  - {label.get('name')}: {label.get('description')}")

        print("\nResource Owners:")
        if config.get("query_resources"):
            for resource in config["query_resources"]:
                owners = manager.list_resource_owners(resource)
                print(f"  Resource: {resource}")
                for item in owners.get("data", []):
                    principals = item.get("principals", [])
                    print(f"    Owners: {len(principals)}")


if __name__ == "__main__":
    main()
