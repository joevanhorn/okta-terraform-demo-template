#!/usr/bin/env python3
"""
import_oig_resources.py

Automatically import existing OIG resources from Okta into Terraform.

This script:
1. Queries Okta API for existing OIG resources (entitlements, reviews, etc.)
2. Generates Terraform configuration files (.tf)
3. Generates terraform import commands

Usage:
    python3 scripts/import_oig_resources.py --output-dir imported_oig

Environment variables required:
    OKTA_ORG_NAME - Your Okta org name
    OKTA_API_TOKEN - API token with governance scopes
    OKTA_BASE_URL - Base URL (default: okta.com)
"""

import argparse
import json
import os
import sys
import requests
from typing import List, Dict, Optional
import re


class OIGImporter:
    """Import existing OIG resources from Okta"""

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

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make API request with error handling"""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid Terraform resource name"""
        # Remove special characters, convert to lowercase, replace spaces with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"resource_{sanitized}"
        return sanitized or "unnamed"

    def fetch_entitlements(self) -> List[Dict]:
        """Fetch all entitlement bundles from Okta"""
        print("Fetching entitlement bundles...")
        try:
            # Use the correct entitlement-bundles endpoint with full entitlements included
            url = f"{self.base_url}/governance/api/v1/entitlement-bundles"
            params = {
                "limit": 200,
                "include": "full_entitlements"  # Include entitlement details in response
            }
            response = self._make_request("GET", url, params=params)

            # Handle both dict and list responses
            data = response.json()
            if isinstance(data, list):
                bundles = data
            elif isinstance(data, dict):
                bundles = data.get("data", data.get("entitlements", []))
            else:
                bundles = []

            print(f"  Found {len(bundles)} entitlement bundles")
            return bundles
        except Exception as e:
            print(f"  ⚠️  Could not fetch entitlement bundles: {e}")
            return []

    def validate_bundle_readable(self, bundle_id: str) -> bool:
        """Test if a bundle can be individually retrieved (not all listed bundles are readable)"""
        try:
            # Correct endpoint: entitlement-bundles (not entitlements)
            url = f"{self.base_url}/governance/api/v1/entitlement-bundles/{bundle_id}"
            response = self._make_request("GET", url)
            return response.status_code == 200
        except Exception:
            return False

    def fetch_entitlements_for_resource(self, resource_id: str, resource_type: str = "APPLICATION") -> List[Dict]:
        """Fetch individual entitlements for a specific resource (app/group/etc)"""
        try:
            url = f"{self.base_url}/governance/api/v1/entitlements"
            # Build filter: parent.externalId eq "resourceId" AND parent.type eq "resourceType"
            filter_expr = f'parent.externalId eq "{resource_id}" AND parent.type eq "{resource_type}"'
            params = {
                "filter": filter_expr,
                "limit": 200
            }
            response = self._make_request("GET", url, params=params)
            entitlements = response.json().get("data", [])
            return entitlements
        except Exception as e:
            print(f"  ⚠️  Could not fetch entitlements for resource {resource_id}: {e}")
            return []

    def fetch_reviews(self) -> List[Dict]:
        """Fetch all access review campaigns"""
        print("Fetching access review campaigns...")
        try:
            url = f"{self.base_url}/governance/api/v1/reviews"
            params = {"limit": 200}
            response = self._make_request("GET", url, params=params)
            reviews = response.json().get("data", [])
            print(f"  Found {len(reviews)} review campaigns")
            return reviews
        except Exception as e:
            print(f"  ⚠️  Could not fetch reviews: {e}")
            return []

    def fetch_request_sequences(self, entitlement_bundles: List[Dict]) -> List[Dict]:
        """
        Fetch all approval workflows (request sequences).

        Note: API v2 requires request sequences to be fetched per-resource.
        We iterate through entitlement bundles and collect unique sequences.

        API: GET /governance/api/v2/resources/{resourceId}/request-sequences
        """
        print("Fetching approval workflows (request sequences)...")
        all_sequences = {}  # Use dict to deduplicate by ID

        if not entitlement_bundles:
            print("  ℹ️  No entitlement bundles to query for sequences")
            return []

        # Sample a few bundles to find sequences (most bundles share sequences)
        sample_size = min(5, len(entitlement_bundles))
        print(f"  Sampling {sample_size} of {len(entitlement_bundles)} bundles for sequences...")

        for bundle in entitlement_bundles[:sample_size]:
            bundle_id = bundle.get("id") or bundle.get("bundleId")
            if not bundle_id:
                continue

            try:
                # v2 API endpoint with resourceId
                url = f"{self.base_url}/governance/api/v2/resources/{bundle_id}/request-sequences"
                params = {"limit": 200}
                response = self._make_request("GET", url, params=params)
                sequences = response.json().get("data", [])

                # Add to dict to deduplicate. Remember which resource the
                # sequence was found on: okta_request_sequence needs resource_id.
                for seq in sequences:
                    seq_id = seq.get("id")
                    if seq_id and seq_id not in all_sequences:
                        seq["_resource_id"] = bundle_id
                        all_sequences[seq_id] = seq

            except Exception as e:
                # Expected for bundles without sequences - continue silently
                continue

        sequences_list = list(all_sequences.values())
        print(f"  Found {len(sequences_list)} unique approval workflows")
        return sequences_list

    def fetch_catalog_entries(self) -> List[Dict]:
        """
        Fetch all catalog entries.

        Note: This endpoint is not currently used for imports.
        Catalog entries are managed through request conditions in v2 API.
        Keeping for backwards compatibility but returning empty list.
        """
        print("Fetching catalog entries...")
        print("  ℹ️  Catalog entries import not currently supported")
        print("  ℹ️  Use request conditions API instead (v2)")
        return []

    def fetch_request_settings(self) -> Optional[Dict]:
        """
        Fetch organization-level request settings.

        API: GET /governance/api/v2/request-settings (org-level)
        """
        print("Fetching organization request settings...")
        try:
            # v2 API endpoint (org-level)
            url = f"{self.base_url}/governance/api/v2/request-settings"
            response = self._make_request("GET", url)
            settings = response.json()
            print(f"  ✅ Found organization request settings")
            return settings
        except Exception as e:
            print(f"  ⚠️  Could not fetch request settings: {e}")
            print(f"  ℹ️  This may be expected if request settings are not configured")
            return None

    def generate_entitlement_tf(self, bundles: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for entitlement bundles"""
        if not bundles:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# =============================================================================")
        tf_config.append("# OKTA IDENTITY GOVERNANCE - ENTITLEMENT BUNDLES")
        tf_config.append("# =============================================================================")
        tf_config.append("# Entitlement bundles define collections of access rights that can be assigned")
        tf_config.append("# to users and groups. These bundles are managed via Terraform.")
        tf_config.append("#")
        tf_config.append("# IMPORTANT:")
        tf_config.append("# - Entitlement BUNDLES (definitions) are managed here in Terraform")
        tf_config.append("# - Entitlement ASSIGNMENTS (which users/groups have bundles) should be")
        tf_config.append("#   managed in Okta Admin UI or via direct API calls, NOT in Terraform")
        tf_config.append("#")
        tf_config.append("# Resource: okta_entitlement_bundle")
        tf_config.append("# Documentation: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/entitlement_bundle")
        tf_config.append("# =============================================================================")
        tf_config.append("")

        for bundle in bundles:
            bundle_id = bundle.get("id") or bundle.get("bundleId")
            name = bundle.get("name", "unnamed")
            description = bundle.get("description", "")
            orn = bundle.get("orn", "")
            bundle_type = bundle.get("bundleType", "MANUAL")

            # Skip app-managed bundles if they shouldn't be in Terraform
            if ":apps:" in orn and bundle_type != "MANUAL":
                print(f"  Skipping app-managed bundle: {name}")
                continue

            # Validate bundle can be individually retrieved
            # Some bundles are listed but return 404 when accessed individually
            if not self.validate_bundle_readable(bundle_id):
                print(f"  ⚠️  Skipping unreadable bundle (404): {name} (ID: {bundle_id})")
                continue

            safe_name = self._sanitize_name(name)

            # Extract bundle properties
            target = bundle.get("target", {})
            target_id = target.get("externalId", "")
            target_type = target.get("type", "")
            target_name = target.get("name", "")
            status = bundle.get("status", "ACTIVE")
            entitlements = bundle.get("entitlements", [])

            print(f"  Generating resource for bundle: {name}")

            # Add comment header
            tf_config.append(f'# {"-" * 77}')
            tf_config.append(f'# {name}')
            if description:
                tf_config.append(f'# {description}')
            tf_config.append(f'# {"-" * 77}')
            tf_config.append(f'')

            # Generate okta_entitlement_bundle resource
            tf_config.append(f'resource "okta_entitlement_bundle" "{safe_name}" {{')
            tf_config.append(f'  name = "{name}"')

            if description:
                # Escape quotes in description
                escaped_desc = description.replace('"', '\\"')
                tf_config.append(f'  description = "{escaped_desc}"')

            if orn:
                tf_config.append(f'  target_resource_orn = "{orn}"')

            if status:
                tf_config.append(f'  status = "{status}"')

            tf_config.append(f'')

            # Add target block
            if target_id and target_type:
                tf_config.append(f'  target {{')
                tf_config.append(f'    external_id = "{target_id}"')
                tf_config.append(f'    type        = "{target_type}"')
                if target_name:
                    tf_config.append(f'    # Resource name: {target_name}')
                tf_config.append(f'  }}')
                tf_config.append(f'')

            # Add entitlements blocks
            if entitlements:
                for entitlement in entitlements:
                    ent_id = entitlement.get("id") or entitlement.get("externalId")
                    ent_values = entitlement.get("values", [])

                    if ent_id:
                        tf_config.append(f'  entitlements {{')
                        tf_config.append(f'    id = "{ent_id}"')

                        if ent_values:
                            for value in ent_values:
                                value_id = value.get("id") or value.get("externalId")
                                if value_id:
                                    tf_config.append(f'    values {{')
                                    tf_config.append(f'      id = "{value_id}"')
                                    tf_config.append(f'    }}')

                        tf_config.append(f'  }}')
                        tf_config.append(f'')

            tf_config.append(f'  # Bundle Type: {bundle_type}')
            tf_config.append(f'  # ORN: {orn}')
            tf_config.append(f'}}')
            tf_config.append('')

            # Generate import command
            import_commands.append(f'# Import bundle: {name}')
            import_commands.append(f'terraform import okta_entitlement_bundle.{safe_name} {bundle_id}')
            import_commands.append('')

        return "\n".join(tf_config), import_commands

    def generate_reviews_tf(self, reviews: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for access reviews"""
        if not reviews:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# Access Review Campaigns\n")

        for idx, review in enumerate(reviews, 1):
            review_id = review.get("id")
            name = review.get("name")
            description = review.get("description", "")

            # Use name if available, otherwise use ID or index for uniqueness
            if name:
                safe_name = self._sanitize_name(name)
            else:
                # Use last 8 chars of ID or index to create unique name
                id_suffix = review_id[-8:] if review_id else f"{idx:03d}"
                safe_name = f"review_{id_suffix}"
                name = f"Review {id_suffix}"  # Placeholder display name

            # okta_campaign requires all five settings blocks. Pre-fill them from
            # the campaign JSON where the API returned it, otherwise use safe
            # defaults and leave a TODO so the file is valid HCL out of the box.
            sched = review.get("scheduleSettings") or {}
            res = review.get("resourceSettings") or {}
            scope = review.get("principalScopeSettings") or {}
            rev = review.get("reviewerSettings") or {}
            rem = review.get("remediationSettings") or {}
            notif = review.get("notificationSettings") or {}

            def tf_bool(value, default):
                return str(value if isinstance(value, bool) else default).lower()

            tf_config.append(f'resource "okta_campaign" "{safe_name}" {{')
            tf_config.append(f'  # ID: {review_id}')
            tf_config.append(f'  name          = "{name}"')
            if description:
                tf_config.append(f'  description   = "{description}"')
            tf_config.append(f'  campaign_type = "{review.get("campaignType", "RESOURCE")}"')
            tf_config.append('')
            tf_config.append('  # REVIEW: values below come from the exported campaign JSON (reviews.json)')
            tf_config.append('  # where available; everything marked TODO is a placeholder.')
            tf_config.append('  schedule_settings {')
            tf_config.append(f'    type             = "{sched.get("type", "ONE_OFF")}"')
            tf_config.append(f'    start_date       = "{sched.get("startDate", "2027-01-01T08:00:00.000Z")}"')
            tf_config.append(f'    duration_in_days = {sched.get("durationInDays", 30)}')
            tf_config.append(f'    time_zone        = "{sched.get("timeZone", "America/Los_Angeles")}"')
            tf_config.append('  }')
            tf_config.append('')
            tf_config.append('  resource_settings {')
            tf_config.append(f'    type = "{res.get("type", "APPLICATION")}"')
            for target in res.get("targetResources") or []:
                tf_config.append('    target_resources {')
                tf_config.append(f'      resource_id   = "{target.get("resourceId", "")}"')
                tf_config.append(f'      resource_type = "{target.get("resourceType", "APPLICATION")}"')
                tf_config.append('    }')
            if not res.get("targetResources"):
                tf_config.append('    # TODO: add target_resources { resource_id = ... resource_type = "APPLICATION" | "GROUP" }')
            tf_config.append('  }')
            tf_config.append('')
            tf_config.append('  principal_scope_settings {')
            tf_config.append(f'    type = "{scope.get("type", "USERS")}"')
            tf_config.append('  }')
            tf_config.append('')
            tf_config.append('  reviewer_settings {')
            tf_config.append(f'    type = "{rev.get("type", "RESOURCE_OWNER")}"')
            if rev.get("reviewerId"):
                tf_config.append(f'    reviewer_id = "{rev["reviewerId"]}"')
            if rev.get("reviewerGroupId"):
                tf_config.append(f'    reviewer_group_id = "{rev["reviewerGroupId"]}"')
            if rev.get("fallbackReviewerId"):
                tf_config.append(f'    fallback_reviewer_id = "{rev["fallbackReviewerId"]}"')
            if not (rev.get("reviewerId") or rev.get("reviewerGroupId") or rev.get("fallbackReviewerId")):
                tf_config.append('    # TODO: reviewer_id (USER), reviewer_group_id (GROUP) or fallback_reviewer_id (RESOURCE_OWNER / REVIEWER_EXPRESSION)')
            tf_config.append('  }')
            tf_config.append('')
            tf_config.append('  remediation_settings {')
            tf_config.append(f'    access_approved = "{rem.get("accessApproved", "NO_ACTION")}"')
            tf_config.append(f'    access_revoked  = "{rem.get("accessRevoked", "DENY")}"')
            tf_config.append(f'    no_response     = "{rem.get("noResponse", "DENY")}"')
            tf_config.append('  }')
            tf_config.append('')
            tf_config.append('  notification_settings {')
            tf_config.append(f'    notify_reviewer_when_review_assigned      = {tf_bool(notif.get("notifyReviewerWhenReviewAssigned"), True)}')
            tf_config.append(f'    notify_reviewer_during_midpoint_of_review = {tf_bool(notif.get("notifyReviewerDuringMidpointOfReview"), True)}')
            tf_config.append(f'    notify_reviewer_when_overdue              = {tf_bool(notif.get("notifyReviewerWhenOverdue"), True)}')
            tf_config.append(f'    notify_review_period_end                  = {tf_bool(notif.get("notifyReviewPeriodEnd"), True)}')
            tf_config.append(f'    notify_reviewer_at_campaign_end           = {tf_bool(notif.get("notifyReviewerAtCampaignEnd"), True)}')
            tf_config.append('  }')
            tf_config.append('')
            tf_config.append('  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/campaign')
            tf_config.append('}')
            tf_config.append('')

            import_commands.append(f'terraform import okta_campaign.{safe_name} {review_id}')

        return "\n".join(tf_config), import_commands

    def generate_request_sequences_tf(self, sequences: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for approval workflows"""
        if not sequences:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# Approval Workflows (Request Sequences)\n")

        for seq in sequences:
            seq_id = seq.get("id")
            name = seq.get("name", "unnamed")
            description = seq.get("description", "")
            safe_name = self._sanitize_name(name)

            # okta_request_sequence binds an EXISTING approval sequence (authored
            # in the Access Requests admin UI) to a resource. The sequence's
            # stages are not managed in Terraform; name/description are read back.
            resource_id = seq.get("_resource_id", "<resource-id>")

            tf_config.append(f'resource "okta_request_sequence" "{safe_name}" {{')
            tf_config.append(f'  # Sequence: {name}')
            if description:
                tf_config.append(f'  # {description}')
            tf_config.append(f'  id          = "{seq_id}"')
            tf_config.append(f'  resource_id = "{resource_id}"')
            tf_config.append('')
            tf_config.append('  # Approval stages are configured in Okta Admin Console > Access Requests.')
            tf_config.append('  # Make the resource requestable with okta_request_condition (see RESOURCE_EXAMPLES.tf).')
            tf_config.append('  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_sequence')
            tf_config.append('}')
            tf_config.append('')

            import_commands.append(f'terraform import okta_request_sequence.{safe_name} {resource_id}/{seq_id}')

        return "\n".join(tf_config), import_commands

    def generate_catalog_entries_tf(self, entries: List[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for catalog entries"""
        if not entries:
            return "", []

        tf_config = []
        import_commands = []

        tf_config.append("# Catalog Entries\n")

        for entry in entries:
            entry_id = entry.get("id")
            app_id = entry.get("appId")
            name = entry.get("name", "unnamed")
            safe_name = self._sanitize_name(name)

            # Catalog entries are READ-ONLY in the provider (data source). What
            # makes an app requestable is an okta_request_condition on the app.
            tf_config.append(f'data "okta_catalog_entry_default" "{safe_name}" {{')
            tf_config.append(f'  # App: {app_id}')
            tf_config.append(f'  entry_id = "{entry_id}"')
            tf_config.append('}')
            tf_config.append('')
            tf_config.append('# To manage who can request this entry, create an okta_request_condition')
            tf_config.append('# (see RESOURCE_EXAMPLES.tf). Catalog entries themselves cannot be imported.')
            tf_config.append('')

        return "\n".join(tf_config), import_commands

    def generate_request_settings_tf(self, settings: Optional[Dict]) -> tuple[str, List[str]]:
        """Generate Terraform config and import commands for request settings"""
        if not settings:
            return "", []

        tf_config = []
        import_commands = []

        acknowledged = str(bool(settings.get("subprocessorsAcknowledged", False))).lower()

        tf_config.append("# Global Request Settings\n")
        tf_config.append('resource "okta_request_setting_organization" "org" {')
        tf_config.append('  # Org-wide access request settings (the only writable field today)')
        tf_config.append('  id                         = "default"')
        tf_config.append(f'  subprocessors_acknowledged = {acknowledged}')
        tf_config.append('')
        tf_config.append('  # Per-resource settings (request on behalf of, risk settings) live in')
        tf_config.append('  # okta_request_setting_resource; see RESOURCE_EXAMPLES.tf.')
        tf_config.append('  # See: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_setting_organization')
        tf_config.append('}')
        tf_config.append('')

        import_commands.append('terraform import okta_request_setting_organization.org default')

        return "\n".join(tf_config), import_commands

    def export_json(self, output_file: str, data: Dict):
        """Export raw API data to JSON for reference"""
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Exported JSON to: {output_file}")

    def generate_import_files(self, output_dir: str):
        """Generate all Terraform files and import commands"""
        print(f"\n{'='*60}")
        print(f"Importing OIG Resources from Okta")
        print(f"{'='*60}\n")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Fetch all resources
        entitlements = self.fetch_entitlements()
        # Skip reviews - they should be managed in Okta Admin UI
        # Reviews are individual access review decisions, not campaign definitions
        # For campaign management, use the Okta Admin Console
        reviews = []  # self.fetch_reviews() - disabled by default
        sequences = self.fetch_request_sequences(entitlements)  # Pass bundles for v2 API
        catalog_entries = self.fetch_catalog_entries()
        request_settings = self.fetch_request_settings()

        print(f"\n{'='*60}")
        print(f"Generating Terraform Configurations")
        print(f"{'='*60}\n")

        all_import_commands = []

        # Generate entitlements
        if entitlements:
            print("Generating entitlements configuration...")
            tf_content, imports = self.generate_entitlement_tf(entitlements)
            if tf_content:
                tf_file = os.path.join(output_dir, "entitlements.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            # Export raw JSON for reference
            json_file = os.path.join(output_dir, "entitlements.json")
            self.export_json(json_file, {"entitlements": entitlements})

        # Generate reviews
        if reviews:
            print("Generating access reviews configuration...")
            tf_content, imports = self.generate_reviews_tf(reviews)
            if tf_content:
                tf_file = os.path.join(output_dir, "reviews.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "reviews.json")
            self.export_json(json_file, {"reviews": reviews})

        # Generate request sequences
        if sequences:
            print("Generating approval workflows configuration...")
            tf_content, imports = self.generate_request_sequences_tf(sequences)
            if tf_content:
                tf_file = os.path.join(output_dir, "request_sequences.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "request_sequences.json")
            self.export_json(json_file, {"sequences": sequences})

        # Generate catalog entries
        if catalog_entries:
            print("Generating catalog entries configuration...")
            tf_content, imports = self.generate_catalog_entries_tf(catalog_entries)
            if tf_content:
                tf_file = os.path.join(output_dir, "catalog_entries.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "catalog_entries.json")
            self.export_json(json_file, {"catalog_entries": catalog_entries})

        # Generate request settings
        if request_settings:
            print("Generating request settings configuration...")
            tf_content, imports = self.generate_request_settings_tf(request_settings)
            if tf_content:
                tf_file = os.path.join(output_dir, "request_settings.tf")
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                print(f"  Created: {tf_file}")
                all_import_commands.extend(imports)

            json_file = os.path.join(output_dir, "request_settings.json")
            self.export_json(json_file, {"request_settings": request_settings})

        # Generate import script
        if all_import_commands:
            print("\nGenerating import script...")
            import_script = os.path.join(output_dir, "import.sh")
            with open(import_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Terraform import commands for OIG resources\n")
                f.write("# Review the generated .tf files and complete TODO items before running\n\n")
                f.write("set -e\n\n")
                for cmd in all_import_commands:
                    f.write(f"{cmd}\n")

            os.chmod(import_script, 0o755)
            print(f"  Created: {import_script}")

        print(f"\n{'='*60}")
        print(f"Import Generation Complete!")
        print(f"{'='*60}\n")
        print(f"Generated files in: {output_dir}/")
        print(f"")
        print(f"Next steps:")
        print(f"1. Review the generated .tf files in {output_dir}/")
        print(f"2. Complete TODO items in each file")
        print(f"3. Copy files to your Terraform directory")
        print(f"4. Run: cd {output_dir} && terraform init")
        print(f"5. Run: ./import.sh")
        print(f"6. Verify: terraform plan (should show no changes)")
        print(f"")
        print(f"Note: .json files contain raw API data for reference")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Import existing OIG resources from Okta into Terraform"
    )
    parser.add_argument(
        "--output-dir",
        default="imported_oig",
        help="Output directory for generated Terraform files"
    )
    parser.add_argument(
        "--org-name",
        help="Okta organization name (or set OKTA_ORG_NAME env var)"
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Okta base URL (default: okta.com, or OKTA_BASE_URL env var)"
    )
    parser.add_argument(
        "--api-token",
        help="Okta API token (or set OKTA_API_TOKEN env var)"
    )

    args = parser.parse_args()

    # Get credentials
    org_name = args.org_name or os.environ.get("OKTA_ORG_NAME")
    api_token = args.api_token or os.environ.get("OKTA_API_TOKEN")
    base_url = args.base_url or os.environ.get("OKTA_BASE_URL", "okta.com")

    if not org_name or not api_token:
        print("Error: Okta org name and API token required")
        print("Set via --org-name and --api-token or OKTA_ORG_NAME and OKTA_API_TOKEN env vars")
        sys.exit(1)

    # Run import
    importer = OIGImporter(org_name, base_url, api_token)
    importer.generate_import_files(args.output_dir)


if __name__ == "__main__":
    main()
