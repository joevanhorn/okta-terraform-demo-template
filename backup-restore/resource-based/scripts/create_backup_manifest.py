#!/usr/bin/env python3
"""
Create a backup manifest file for Okta tenant snapshots.

This script generates a manifest file that documents the contents of a backup
snapshot, including resource counts, file checksums, and metadata.

Usage:
    # Create manifest for backup directory
    python scripts/create_backup_manifest.py \
        --backup-dir environments/myorg/backups/latest \
        --output environments/myorg/backups/latest/MANIFEST.json

    # Include Terraform state reference
    python scripts/create_backup_manifest.py \
        --backup-dir backups/latest \
        --output backups/latest/MANIFEST.json \
        --state-bucket okta-terraform-demo \
        --state-key Okta-GitOps/myorg/terraform.tfstate

Environment Variables:
    OKTA_ORG_NAME   - Okta org name (for manifest metadata)
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, Optional


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def count_csv_rows(filepath: str) -> int:
    """Count data rows in a CSV file (excluding headers and comments)."""
    count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty rows, header, and comments
            if row and not row[0].startswith('#') and row[0] != 'email':
                count += 1
    return count


def count_json_items(filepath: str, key: Optional[str] = None) -> int:
    """Count items in a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    if key:
        if key in data:
            return len(data[key]) if isinstance(data[key], list) else 1
        return 0

    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict):
        # Try common keys
        for k in ['users', 'groups', 'memberships', 'applications', 'rules', 'labels', 'owners']:
            if k in data:
                return len(data[k]) if isinstance(data[k], list) else 1
        return len(data)
    return 1


def get_file_info(backup_dir: str, filename: str, count_key: Optional[str] = None) -> Dict[str, Any]:
    """Get information about a backup file."""
    filepath = os.path.join(backup_dir, filename)

    if not os.path.exists(filepath):
        return None

    stat = os.stat(filepath)
    info = {
        'file': filename,
        'size_bytes': stat.st_size,
        'modified': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(stat.st_mtime)),
        'sha256': calculate_file_hash(filepath),
    }

    # Count records based on file type
    if filename.endswith('.csv'):
        info['count'] = count_csv_rows(filepath)
    elif filename.endswith('.json'):
        info['count'] = count_json_items(filepath, count_key)

    return info


def create_manifest(
    backup_dir: str,
    output_file: str,
    org_name: Optional[str] = None,
    schedule_type: str = 'manual',
    state_bucket: Optional[str] = None,
    state_key: Optional[str] = None,
    state_version: Optional[str] = None,
) -> Dict:
    """Create a backup manifest file."""
    snapshot_id = time.strftime('%Y-%m-%dT%H-%M-%S', time.gmtime())

    manifest = {
        'version': '1.0',
        'snapshot_id': snapshot_id,
        'org_name': org_name or os.environ.get('OKTA_ORG_NAME', 'unknown'),
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'created_by': os.environ.get('GITHUB_ACTOR', os.environ.get('USER', 'unknown')),
        'schedule': schedule_type,
        'backup_dir': backup_dir,
        'resources': {},
        'files': [],
    }

    # Define expected backup files and their JSON keys for counting
    backup_files = [
        ('users.csv', None),
        ('groups.json', 'groups'),
        ('memberships.json', 'memberships'),
        ('app_assignments.json', 'applications'),
        ('owner_mappings.json', None),
        ('label_mappings.json', 'labels'),
        ('risk_rules.json', 'rules'),
    ]

    # OIG subdirectory files
    oig_files = [
        ('oig/entitlements.json', 'entitlements'),
        ('oig/reviews.json', 'reviews'),
        ('oig/request_sequences.json', 'sequences'),
        ('oig/catalog_entries.json', 'entries'),
    ]

    print(f"Creating manifest for: {backup_dir}")
    print(f"Snapshot ID: {snapshot_id}")

    total_files = 0
    total_resources = 0

    # Process main backup files
    for filename, count_key in backup_files:
        info = get_file_info(backup_dir, filename, count_key)
        if info:
            manifest['files'].append(info)
            resource_name = filename.replace('.csv', '').replace('.json', '')
            manifest['resources'][resource_name] = {
                'count': info.get('count', 0),
                'file': filename,
                'source': 'export'
            }
            total_files += 1
            total_resources += info.get('count', 0)
            print(f"  {filename}: {info.get('count', 0)} items")

    # Process OIG subdirectory files
    for filename, count_key in oig_files:
        info = get_file_info(backup_dir, filename, count_key)
        if info:
            manifest['files'].append(info)
            resource_name = filename.replace('oig/', '').replace('.json', '')
            manifest['resources'][resource_name] = {
                'count': info.get('count', 0),
                'file': filename,
                'source': 'terraform'
            }
            total_files += 1
            total_resources += info.get('count', 0)
            print(f"  {filename}: {info.get('count', 0)} items")

    # Add Terraform state reference if provided
    if state_bucket and state_key:
        manifest['terraform_state'] = {
            's3_bucket': state_bucket,
            's3_key': state_key,
        }
        if state_version:
            manifest['terraform_state']['version_id'] = state_version

    # Summary statistics
    manifest['summary'] = {
        'total_files': total_files,
        'total_resources': total_resources,
    }

    # Write manifest
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest created: {output_file}")
    print(f"  Total files: {total_files}")
    print(f"  Total resources: {total_resources}")

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Create backup manifest for Okta tenant snapshot"
    )
    parser.add_argument("--backup-dir", "-d", required=True,
                        help="Backup directory containing exported files")
    parser.add_argument("--output", "-o", required=True,
                        help="Output manifest file path")
    parser.add_argument("--org-name", type=str,
                        help="Okta org name (default: OKTA_ORG_NAME env var)")
    parser.add_argument("--schedule", type=str, default="manual",
                        choices=["manual", "daily", "weekly"],
                        help="Backup schedule type")
    parser.add_argument("--state-bucket", type=str,
                        help="S3 bucket for Terraform state")
    parser.add_argument("--state-key", type=str,
                        help="S3 key for Terraform state")
    parser.add_argument("--state-version", type=str,
                        help="S3 version ID for Terraform state")

    args = parser.parse_args()

    if not os.path.isdir(args.backup_dir):
        print(f"Error: Backup directory not found: {args.backup_dir}")
        sys.exit(1)

    manifest = create_manifest(
        args.backup_dir,
        args.output,
        org_name=args.org_name,
        schedule_type=args.schedule,
        state_bucket=args.state_bucket,
        state_key=args.state_key,
        state_version=args.state_version,
    )

    return 0 if manifest else 1


if __name__ == "__main__":
    sys.exit(main())
