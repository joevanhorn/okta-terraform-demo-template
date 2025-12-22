#!/usr/bin/env python3
"""
Detect applications that have entitlement resources defined in Terraform files.

This script scans Terraform files for okta_entitlement and okta_entitlement_bundle
resources and extracts the app IDs or app resource references they target.

Used by the auto-enable-entitlements workflow to automatically enable entitlement
management on apps when entitlement Terraform files are created.

Usage:
    # Scan specific files (from git diff)
    python scripts/detect_entitlement_apps.py --files file1.tf file2.tf

    # Scan all TF files in an environment
    python scripts/detect_entitlement_apps.py --environment myorg

    # Output JSON for workflow consumption
    python scripts/detect_entitlement_apps.py --environment myorg --json

Output:
    List of app IDs that have entitlement resources defined but may not have
    entitlement management enabled yet.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_app_references_from_file(filepath: str) -> Tuple[Set[str], Set[str]]:
    """
    Extract app ID references from a Terraform file.

    Returns:
        Tuple of (literal_app_ids, terraform_references)
        - literal_app_ids: Direct app IDs like "0oaXXXXXX"
        - terraform_references: Terraform references like "okta_app_oauth.my_app.id"
    """
    literal_ids = set()
    tf_references = set()

    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return literal_ids, tf_references

    # Skip if file is commented out examples
    if filepath.endswith('RESOURCE_EXAMPLES.tf'):
        return literal_ids, tf_references

    # Pattern for okta_entitlement resource with app_id
    # resource "okta_entitlement" "name" {
    #   app_id = okta_app_oauth.my_app.id
    #   OR
    #   app_id = "0oaXXXXXX"
    entitlement_pattern = r'resource\s+"okta_entitlement"\s+"[^"]+"\s*\{[^}]*app_id\s*=\s*([^\n]+)'

    for match in re.finditer(entitlement_pattern, content, re.DOTALL):
        app_id_line = match.group(1).strip()

        # Check if it's a literal ID (quoted string starting with 0oa)
        literal_match = re.match(r'"(0oa[^"]+)"', app_id_line)
        if literal_match:
            literal_ids.add(literal_match.group(1))
            continue

        # Check if it's a Terraform reference (okta_app_*.name.id)
        ref_match = re.match(r'(okta_app_[a-z_]+\.[a-zA-Z0-9_]+)\.id', app_id_line)
        if ref_match:
            tf_references.add(ref_match.group(1))
            continue

        # Could be a variable reference
        var_match = re.match(r'var\.([a-zA-Z0-9_]+)', app_id_line)
        if var_match:
            # Can't resolve variables, skip
            continue

    # Pattern for okta_entitlement_bundle with target block
    # resource "okta_entitlement_bundle" "name" {
    #   target {
    #     external_id = okta_app_oauth.my_app.id
    #     OR
    #     external_id = "0oaXXXXXX"
    bundle_pattern = r'resource\s+"okta_entitlement_bundle"\s+"[^"]+"\s*\{[^}]*target\s*\{[^}]*external_id\s*=\s*([^\n]+)'

    for match in re.finditer(bundle_pattern, content, re.DOTALL):
        external_id_line = match.group(1).strip()

        # Check if it's a literal ID
        literal_match = re.match(r'"(0oa[^"]+)"', external_id_line)
        if literal_match:
            literal_ids.add(literal_match.group(1))
            continue

        # Check if it's a Terraform reference
        ref_match = re.match(r'(okta_app_[a-z_]+\.[a-zA-Z0-9_]+)\.id', external_id_line)
        if ref_match:
            tf_references.add(ref_match.group(1))

    return literal_ids, tf_references


def resolve_terraform_references(tf_dir: str, references: Set[str]) -> Dict[str, str]:
    """
    Attempt to resolve Terraform resource references to app labels.

    This is a best-effort resolution - we look for the app label in the
    resource definition which can be used to look up the app via API.

    Returns:
        Dict mapping reference name to app label (if found)
    """
    resolved = {}

    if not references:
        return resolved

    # Look through all TF files for app definitions
    tf_path = Path(tf_dir)
    for tf_file in tf_path.glob('*.tf'):
        try:
            with open(tf_file, 'r') as f:
                content = f.read()
        except Exception:
            continue

        for ref in references:
            if ref in resolved:
                continue

            # Extract resource type and name from reference
            # e.g., "okta_app_oauth.my_app" -> type="okta_app_oauth", name="my_app"
            parts = ref.split('.')
            if len(parts) != 2:
                continue

            resource_type, resource_name = parts

            # Look for the resource definition with label
            # resource "okta_app_oauth" "my_app" {
            #   label = "My Application"
            pattern = rf'resource\s+"{resource_type}"\s+"{resource_name}"\s*\{{[^}}]*label\s*=\s*"([^"]+)"'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                resolved[ref] = match.group(1)

    return resolved


def find_tf_files(environment: str, base_path: str = '.') -> List[str]:
    """Find all Terraform files in an environment directory."""
    env_path = Path(base_path) / 'environments' / environment / 'terraform'
    if not env_path.exists():
        return []

    return [str(f) for f in env_path.glob('*.tf')]


def main():
    parser = argparse.ArgumentParser(
        description="Detect apps with entitlement resources in Terraform files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Specific Terraform files to scan"
    )
    parser.add_argument(
        "--environment",
        help="Environment to scan (e.g., myorg)"
    )
    parser.add_argument(
        "--base-path",
        default=".",
        help="Base path of the repository"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--resolve-labels",
        action="store_true",
        help="Attempt to resolve Terraform references to app labels"
    )

    args = parser.parse_args()

    if not args.files and not args.environment:
        parser.error("Either --files or --environment is required")

    # Collect files to scan
    files_to_scan = []
    if args.files:
        files_to_scan = args.files
    elif args.environment:
        files_to_scan = find_tf_files(args.environment, args.base_path)

    if not files_to_scan:
        if args.json:
            print(json.dumps({"apps": [], "references": [], "error": "No files found"}))
        else:
            print("No Terraform files found to scan")
        sys.exit(0)

    # Scan all files
    all_literal_ids = set()
    all_tf_references = set()

    for filepath in files_to_scan:
        literal_ids, tf_refs = extract_app_references_from_file(filepath)
        all_literal_ids.update(literal_ids)
        all_tf_references.update(tf_refs)

    # Resolve references if requested
    resolved_labels = {}
    if args.resolve_labels and args.environment and all_tf_references:
        tf_dir = str(Path(args.base_path) / 'environments' / args.environment / 'terraform')
        resolved_labels = resolve_terraform_references(tf_dir, all_tf_references)

    # Output results
    if args.json:
        output = {
            "app_ids": list(all_literal_ids),
            "terraform_references": list(all_tf_references),
            "resolved_labels": resolved_labels,
            "files_scanned": len(files_to_scan)
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Scanned {len(files_to_scan)} file(s)")
        print()

        if all_literal_ids:
            print("Direct App IDs found:")
            for app_id in sorted(all_literal_ids):
                print(f"  - {app_id}")
            print()

        if all_tf_references:
            print("Terraform App References found:")
            for ref in sorted(all_tf_references):
                label = resolved_labels.get(ref, "")
                if label:
                    print(f"  - {ref} (label: \"{label}\")")
                else:
                    print(f"  - {ref}")
            print()

        total = len(all_literal_ids) + len(all_tf_references)
        print(f"Total: {total} app(s) with entitlement resources")


if __name__ == "__main__":
    main()
