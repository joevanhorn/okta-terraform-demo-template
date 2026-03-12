#!/usr/bin/env python3
"""
import_opa_resources.py

Automatically import existing OPA (Okta Privileged Access) resources into Terraform.

This script:
1. Queries OPA API for existing resources (resource groups, projects, secrets, etc.)
2. Generates Terraform configuration files (.tf)
3. Generates terraform import commands

Usage:
    python3 scripts/import_opa_resources.py --output-dir environments/myorg/terraform

Environment variables required:
    OKTAPAM_KEY    - OPA service user key (ID)
    OKTAPAM_SECRET - OPA service user secret
    OKTAPAM_TEAM   - OPA team name
"""

import argparse
import json
import os
import sys
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re
import base64
import time


class OPAImporter:
    """Import existing OPA resources from Okta Privileged Access"""

    # OPA API base URL
    API_BASE = "https://app.scaleft.com/v1"

    def __init__(self, team: str, key: str, secret: str):
        self.team = team
        self.key = key
        self.secret = secret
        self.token = None
        self.token_expiry = 0
        self.session = requests.Session()

    def _get_token(self) -> str:
        """Get or refresh bearer token for OPA API"""
        current_time = time.time()

        # Return cached token if still valid (with 60 second buffer)
        if self.token and current_time < (self.token_expiry - 60):
            return self.token

        # Request new token
        auth_url = f"{self.API_BASE}/teams/{self.team}/service_token"
        auth_data = {
            "key_id": self.key,
            "key_secret": self.secret
        }

        try:
            response = requests.post(auth_url, json=auth_data)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get("bearer_token")
            # Token is typically valid for 1 hour
            self.token_expiry = current_time + 3600
            return self.token
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to authenticate with OPA: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            sys.exit(1)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated API request to OPA"""
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        url = f"{self.API_BASE}/teams/{self.team}{endpoint}"

        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API request failed: {method} {endpoint}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text[:500]}")
            raise

    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid Terraform resource name"""
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')
        if sanitized and sanitized[0].isdigit():
            sanitized = f"resource_{sanitized}"
        return sanitized or "unnamed"

    # =========================================================================
    # Fetch Resources
    # =========================================================================

    def fetch_resource_groups(self) -> List[Dict]:
        """Fetch all resource groups"""
        print("Fetching resource groups...")
        try:
            response = self._make_request("GET", "/resource_groups")
            groups = response.json().get("list", [])
            print(f"  Found {len(groups)} resource groups")
            return groups
        except Exception as e:
            print(f"  ⚠️  Could not fetch resource groups: {e}")
            return []

    def fetch_projects(self, resource_group_id: Optional[str] = None) -> List[Dict]:
        """Fetch all projects (optionally filtered by resource group)"""
        print("Fetching projects...")
        try:
            if resource_group_id:
                endpoint = f"/resource_groups/{resource_group_id}/projects"
            else:
                endpoint = "/projects"
            response = self._make_request("GET", endpoint)
            projects = response.json().get("list", [])
            print(f"  Found {len(projects)} projects")
            return projects
        except Exception as e:
            print(f"  ⚠️  Could not fetch projects: {e}")
            return []

    def fetch_groups(self) -> List[Dict]:
        """Fetch all OPA groups"""
        print("Fetching groups...")
        try:
            response = self._make_request("GET", "/groups")
            groups = response.json().get("list", [])
            print(f"  Found {len(groups)} groups")
            return groups
        except Exception as e:
            print(f"  ⚠️  Could not fetch groups: {e}")
            return []

    def fetch_server_enrollment_tokens(self, project_name: str) -> List[Dict]:
        """Fetch server enrollment tokens for a project"""
        try:
            response = self._make_request("GET", f"/projects/{project_name}/server_enrollment_tokens")
            tokens = response.json().get("list", [])
            return tokens
        except Exception as e:
            print(f"  ⚠️  Could not fetch enrollment tokens for {project_name}: {e}")
            return []

    def fetch_gateway_setup_tokens(self) -> List[Dict]:
        """Fetch gateway setup tokens"""
        print("Fetching gateway setup tokens...")
        try:
            response = self._make_request("GET", "/gateway_setup_tokens")
            tokens = response.json().get("list", [])
            print(f"  Found {len(tokens)} gateway setup tokens")
            return tokens
        except Exception as e:
            print(f"  ⚠️  Could not fetch gateway setup tokens: {e}")
            return []

    def fetch_secret_folders(self, resource_group_id: str, project_id: str) -> List[Dict]:
        """Fetch secret folders for a project"""
        try:
            endpoint = f"/resource_groups/{resource_group_id}/projects/{project_id}/secret_folders"
            response = self._make_request("GET", endpoint)
            folders = response.json().get("list", [])
            return folders
        except Exception as e:
            return []

    def fetch_security_policies(self) -> List[Dict]:
        """Fetch security policies"""
        print("Fetching security policies...")
        try:
            response = self._make_request("GET", "/security_policies")
            policies = response.json().get("list", [])
            print(f"  Found {len(policies)} security policies")
            return policies
        except Exception as e:
            print(f"  ⚠️  Could not fetch security policies: {e}")
            return []

    # =========================================================================
    # Generate Terraform
    # =========================================================================

    def generate_resource_group_tf(self, rg: Dict) -> Tuple[str, str]:
        """Generate Terraform for a resource group"""
        name = rg.get("name", "unnamed")
        tf_name = self._sanitize_name(name)
        rg_id = rg.get("id", "")
        description = rg.get("description", "")

        tf_code = f'''
resource "oktapam_resource_group" "{tf_name}" {{
  name        = "{name}"
  description = "{description}"
}}
'''
        import_cmd = f"terraform import oktapam_resource_group.{tf_name} {rg_id}"
        return tf_code, import_cmd

    def generate_project_tf(self, project: Dict, resource_group_tf_name: str = None) -> Tuple[str, str]:
        """Generate Terraform for a project"""
        name = project.get("name", "unnamed")
        tf_name = self._sanitize_name(name)
        project_id = project.get("id", "")

        # Determine resource group reference
        rg_id = project.get("resource_group_id", "")
        if resource_group_tf_name:
            rg_ref = f"oktapam_resource_group.{resource_group_tf_name}.id"
        else:
            rg_ref = f'"{rg_id}"'

        ssh_cert_type = project.get("ssh_certificate_type", "CERT_TYPE_ED25519")
        account_discovery = str(project.get("account_discovery", True)).lower()
        create_server_users = str(project.get("create_server_users", True)).lower()
        forward_traffic = str(project.get("forward_traffic", False)).lower()

        tf_code = f'''
resource "oktapam_resource_group_project" "{tf_name}" {{
  name                 = "{name}"
  resource_group       = {rg_ref}
  ssh_certificate_type = "{ssh_cert_type}"
  account_discovery    = {account_discovery}
  create_server_users  = {create_server_users}
  forward_traffic      = {forward_traffic}
}}
'''
        import_cmd = f"terraform import oktapam_resource_group_project.{tf_name} {rg_id}/{project_id}"
        return tf_code, import_cmd

    def generate_group_tf(self, group: Dict) -> Tuple[str, str]:
        """Generate Terraform for an OPA group"""
        name = group.get("name", "unnamed")
        tf_name = self._sanitize_name(name)
        group_id = group.get("id", "")

        tf_code = f'''
resource "oktapam_group" "{tf_name}" {{
  name = "{name}"
}}
'''
        import_cmd = f"terraform import oktapam_group.{tf_name} {group_id}"
        return tf_code, import_cmd

    def generate_gateway_token_tf(self, token: Dict) -> Tuple[str, str]:
        """Generate Terraform for a gateway setup token"""
        description = token.get("description", "Gateway token")
        tf_name = self._sanitize_name(description or "gateway_token")
        token_id = token.get("id", "")
        labels = token.get("labels", {})

        labels_str = ""
        if labels:
            labels_items = [f'    {k} = "{v}"' for k, v in labels.items()]
            labels_str = f'''
  labels = {{
{chr(10).join(labels_items)}
  }}'''

        tf_code = f'''
resource "oktapam_gateway_setup_token" "{tf_name}" {{
  description = "{description}"{labels_str}
}}
'''
        import_cmd = f"terraform import oktapam_gateway_setup_token.{tf_name} {token_id}"
        return tf_code, import_cmd

    def generate_secret_folder_tf(self, folder: Dict, rg_tf_name: str, project_tf_name: str) -> Tuple[str, str]:
        """Generate Terraform for a secret folder"""
        name = folder.get("name", "unnamed")
        tf_name = self._sanitize_name(f"{project_tf_name}_{name}")
        folder_id = folder.get("id", "")
        description = folder.get("description", "")

        tf_code = f'''
resource "oktapam_secret_folder" "{tf_name}" {{
  name           = "{name}"
  description    = "{description}"
  resource_group = oktapam_resource_group.{rg_tf_name}.id
  project        = oktapam_resource_group_project.{project_tf_name}.id
}}
'''
        import_cmd = f"terraform import oktapam_secret_folder.{tf_name} {folder_id}"
        return tf_code, import_cmd

    # =========================================================================
    # Main Import Logic
    # =========================================================================

    def import_all(self, output_dir: str, dry_run: bool = False):
        """Import all OPA resources"""
        print(f"\n{'=' * 60}")
        print("OPA Resource Import")
        print(f"{'=' * 60}")
        print(f"Team: {self.team}")
        print(f"Output: {output_dir}")
        print(f"Dry Run: {dry_run}")
        print(f"{'=' * 60}\n")

        # Ensure output directory exists
        if not dry_run:
            os.makedirs(output_dir, exist_ok=True)

        tf_code_blocks = []
        import_commands = []

        # Header
        tf_code_blocks.append(f'''# =============================================================================
# OPA RESOURCES - Auto-imported from Okta Privileged Access
# =============================================================================
# Generated: {datetime.now().isoformat()}
# Team: {self.team}
#
# This file was auto-generated by import_opa_resources.py
# Review and customize before applying
# =============================================================================
''')

        # Resource Groups
        resource_groups = self.fetch_resource_groups()
        rg_map = {}  # Map RG ID to TF name
        if resource_groups:
            tf_code_blocks.append("\n# -----------------------------------------------------------------------------")
            tf_code_blocks.append("# Resource Groups")
            tf_code_blocks.append("# -----------------------------------------------------------------------------")
            for rg in resource_groups:
                tf_code, import_cmd = self.generate_resource_group_tf(rg)
                tf_code_blocks.append(tf_code)
                import_commands.append(import_cmd)
                rg_map[rg.get("id")] = self._sanitize_name(rg.get("name", ""))

        # Projects (for each resource group)
        all_projects = []
        project_map = {}  # Map project ID to (TF name, RG TF name)
        for rg in resource_groups:
            rg_id = rg.get("id")
            rg_tf_name = rg_map.get(rg_id, "")
            projects = self.fetch_projects(rg_id)
            if projects:
                tf_code_blocks.append(f"\n# Projects in {rg.get('name', 'Unknown')}")
                for project in projects:
                    tf_code, import_cmd = self.generate_project_tf(project, rg_tf_name)
                    tf_code_blocks.append(tf_code)
                    import_commands.append(import_cmd)
                    project_tf_name = self._sanitize_name(project.get("name", ""))
                    project_map[project.get("id")] = (project_tf_name, rg_tf_name)
                    all_projects.append((project, rg_tf_name))

        # Groups
        groups = self.fetch_groups()
        if groups:
            tf_code_blocks.append("\n# -----------------------------------------------------------------------------")
            tf_code_blocks.append("# OPA Groups")
            tf_code_blocks.append("# -----------------------------------------------------------------------------")
            for group in groups:
                tf_code, import_cmd = self.generate_group_tf(group)
                tf_code_blocks.append(tf_code)
                import_commands.append(import_cmd)

        # Gateway Setup Tokens
        gateway_tokens = self.fetch_gateway_setup_tokens()
        if gateway_tokens:
            tf_code_blocks.append("\n# -----------------------------------------------------------------------------")
            tf_code_blocks.append("# Gateway Setup Tokens")
            tf_code_blocks.append("# -----------------------------------------------------------------------------")
            for token in gateway_tokens:
                tf_code, import_cmd = self.generate_gateway_token_tf(token)
                tf_code_blocks.append(tf_code)
                import_commands.append(import_cmd)

        # Secret Folders (for each project)
        secret_folders_found = []
        for project, rg_tf_name in all_projects:
            rg_id = project.get("resource_group_id")
            project_id = project.get("id")
            project_tf_name = self._sanitize_name(project.get("name", ""))
            folders = self.fetch_secret_folders(rg_id, project_id)
            if folders:
                for folder in folders:
                    secret_folders_found.append((folder, rg_tf_name, project_tf_name))

        if secret_folders_found:
            tf_code_blocks.append("\n# -----------------------------------------------------------------------------")
            tf_code_blocks.append("# Secret Folders")
            tf_code_blocks.append("# -----------------------------------------------------------------------------")
            for folder, rg_tf_name, project_tf_name in secret_folders_found:
                tf_code, import_cmd = self.generate_secret_folder_tf(folder, rg_tf_name, project_tf_name)
                tf_code_blocks.append(tf_code)
                import_commands.append(import_cmd)

        # Write output files
        if dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN - Generated Terraform Code:")
            print("=" * 60)
            print("\n".join(tf_code_blocks))
            print("\n" + "=" * 60)
            print("DRY RUN - Import Commands:")
            print("=" * 60)
            for cmd in import_commands:
                print(cmd)
        else:
            # Write Terraform file
            tf_file = os.path.join(output_dir, "opa_resources_imported.tf")
            with open(tf_file, "w") as f:
                f.write("\n".join(tf_code_blocks))
            print(f"\n✅ Terraform code written to: {tf_file}")

            # Write import commands
            import_file = os.path.join(output_dir, "opa_import_commands.sh")
            with open(import_file, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("# OPA Resource Import Commands\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write("# Run these commands after terraform init\n\n")
                for cmd in import_commands:
                    f.write(cmd + "\n")
            os.chmod(import_file, 0o755)
            print(f"✅ Import commands written to: {import_file}")

            # Write JSON export for reference
            json_file = os.path.join(output_dir, "opa_resources_export.json")
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "team": self.team,
                "resource_groups": resource_groups,
                "groups": groups,
                "gateway_tokens": gateway_tokens,
            }
            with open(json_file, "w") as f:
                json.dump(export_data, f, indent=2)
            print(f"✅ JSON export written to: {json_file}")

        # Summary
        print(f"\n{'=' * 60}")
        print("Import Summary")
        print(f"{'=' * 60}")
        print(f"Resource Groups: {len(resource_groups)}")
        print(f"Projects: {len(all_projects)}")
        print(f"Groups: {len(groups)}")
        print(f"Gateway Tokens: {len(gateway_tokens)}")
        print(f"Secret Folders: {len(secret_folders_found)}")
        print(f"Total Import Commands: {len(import_commands)}")

        if not dry_run:
            print(f"\nNext Steps:")
            print(f"1. Review generated Terraform: {tf_file}")
            print(f"2. Run: cd {output_dir} && terraform init")
            print(f"3. Run import commands: bash {import_file}")
            print(f"4. Verify state: terraform plan")


def main():
    parser = argparse.ArgumentParser(
        description="Import OPA resources from Okta Privileged Access into Terraform"
    )
    parser.add_argument(
        "--output-dir",
        default="environments/myorg/terraform",
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated Terraform without writing files"
    )
    parser.add_argument(
        "--team",
        default=os.environ.get("OKTAPAM_TEAM"),
        help="OPA team name (or set OKTAPAM_TEAM env var)"
    )
    parser.add_argument(
        "--key",
        default=os.environ.get("OKTAPAM_KEY"),
        help="OPA service user key (or set OKTAPAM_KEY env var)"
    )
    parser.add_argument(
        "--secret",
        default=os.environ.get("OKTAPAM_SECRET"),
        help="OPA service user secret (or set OKTAPAM_SECRET env var)"
    )

    args = parser.parse_args()

    # Validate required parameters
    if not args.team:
        print("❌ Error: OKTAPAM_TEAM is required (env var or --team)")
        sys.exit(1)
    if not args.key:
        print("❌ Error: OKTAPAM_KEY is required (env var or --key)")
        sys.exit(1)
    if not args.secret:
        print("❌ Error: OKTAPAM_SECRET is required (env var or --secret)")
        sys.exit(1)

    # Run import
    importer = OPAImporter(
        team=args.team,
        key=args.key,
        secret=args.secret
    )
    importer.import_all(args.output_dir, args.dry_run)


if __name__ == "__main__":
    main()
