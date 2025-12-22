#!/usr/bin/env python3
"""
State-based backup for Okta Terraform tenants.

This script creates a synchronized backup of both:
1. Terraform state (S3 version ID captured)
2. Okta resources (exported data files)

The backup creates a manifest that links the S3 state version to the
exported resources, enabling consistent point-in-time recovery.

Usage:
    # Create backup with state version capture
    python backup_state.py \
        --environment mycompany \
        --output-dir environments/mycompany/backups/state-based/latest \
        --state-bucket okta-terraform-demo \
        --state-key Okta-GitOps/mycompany/terraform.tfstate

    # Create backup without S3 (local state)
    python backup_state.py \
        --environment mycompany \
        --output-dir backups/latest \
        --local-state environments/mycompany/terraform/terraform.tfstate

Environment Variables:
    AWS_REGION          - AWS region for S3 (default: us-east-1)
    OKTA_ORG_NAME       - Okta org name
    OKTA_BASE_URL       - Okta base URL (default: okta.com)
    OKTA_API_TOKEN      - Okta API token
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_s3_state_version(bucket: str, key: str, region: str = "us-east-1") -> Dict[str, Any]:
    """Get the current version of the Terraform state in S3."""
    if not HAS_BOTO3:
        raise RuntimeError("boto3 is required for S3 operations. Install with: pip install boto3")

    s3 = boto3.client("s3", region_name=region)

    try:
        # Get object metadata including version
        response = s3.head_object(Bucket=bucket, Key=key)

        version_info = {
            "bucket": bucket,
            "key": key,
            "region": region,
            "version_id": response.get("VersionId"),
            "etag": response.get("ETag", "").strip('"'),
            "last_modified": response.get("LastModified").isoformat() if response.get("LastModified") else None,
            "content_length": response.get("ContentLength"),
        }

        return version_info
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            raise FileNotFoundError(f"State file not found: s3://{bucket}/{key}")
        raise


def download_s3_state(bucket: str, key: str, output_path: str,
                      version_id: Optional[str] = None, region: str = "us-east-1") -> str:
    """Download state file from S3, optionally at a specific version."""
    if not HAS_BOTO3:
        raise RuntimeError("boto3 is required for S3 operations")

    s3 = boto3.client("s3", region_name=region)

    params = {"Bucket": bucket, "Key": key}
    if version_id:
        params["VersionId"] = version_id

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    s3.download_file(bucket, key, output_path, ExtraArgs={"VersionId": version_id} if version_id else None)

    return output_path


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def copy_local_state(state_path: str, output_dir: str) -> Dict[str, Any]:
    """Copy local state file and calculate metadata."""
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"Local state file not found: {state_path}")

    output_path = os.path.join(output_dir, "terraform.tfstate")
    os.makedirs(output_dir, exist_ok=True)
    shutil.copy2(state_path, output_path)

    stat = os.stat(output_path)
    return {
        "source": "local",
        "original_path": state_path,
        "backup_path": output_path,
        "sha256": calculate_file_hash(output_path),
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def create_state_manifest(
    output_dir: str,
    environment: str,
    state_info: Dict[str, Any],
    org_name: Optional[str] = None,
    schedule_type: str = "manual",
    resource_exports: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Create a manifest file for the state-based backup."""
    snapshot_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")

    manifest = {
        "version": "2.0",  # State-based backup version
        "backup_type": "state-based",
        "snapshot_id": snapshot_id,
        "environment": environment,
        "org_name": org_name or os.environ.get("OKTA_ORG_NAME", "unknown"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": os.environ.get("GITHUB_ACTOR", os.environ.get("USER", "unknown")),
        "schedule": schedule_type,
        "terraform_state": state_info,
        "resource_exports": resource_exports or {},
        "restore_instructions": {
            "state_restore": "Use restore_state.py --restore-state to rollback S3 state",
            "full_restore": "Use restore_state.py --full-restore for state + terraform apply",
        },
    }

    manifest_path = os.path.join(output_dir, "MANIFEST.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest created: {manifest_path}")
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Create state-based backup for Okta Terraform tenant"
    )
    parser.add_argument("--environment", "-e", required=True,
                        help="Environment name (matches environments/ directory)")
    parser.add_argument("--output-dir", "-o", required=True,
                        help="Output directory for backup files")

    # S3 state options
    parser.add_argument("--state-bucket", type=str,
                        help="S3 bucket containing Terraform state")
    parser.add_argument("--state-key", type=str,
                        help="S3 key for Terraform state file")
    parser.add_argument("--aws-region", type=str, default="us-east-1",
                        help="AWS region for S3 (default: us-east-1)")

    # Local state options
    parser.add_argument("--local-state", type=str,
                        help="Path to local Terraform state file (alternative to S3)")

    # Metadata options
    parser.add_argument("--org-name", type=str,
                        help="Okta org name (default: OKTA_ORG_NAME env var)")
    parser.add_argument("--schedule", type=str, default="manual",
                        choices=["manual", "daily", "weekly"],
                        help="Backup schedule type for metadata")

    # Options
    parser.add_argument("--download-state", action="store_true",
                        help="Download state file to backup directory")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Validate arguments
    if not args.state_bucket and not args.local_state:
        parser.error("Either --state-bucket/--state-key or --local-state is required")

    if args.state_bucket and not args.state_key:
        parser.error("--state-key is required when using --state-bucket")

    print(f"Creating state-based backup for: {args.environment}")
    print(f"Output directory: {args.output_dir}")

    # Get state information
    state_info = {}

    if args.state_bucket:
        # S3 state
        print(f"\nCapturing S3 state version...")
        print(f"  Bucket: {args.state_bucket}")
        print(f"  Key: {args.state_key}")

        try:
            state_info = get_s3_state_version(
                args.state_bucket,
                args.state_key,
                args.aws_region
            )
            state_info["source"] = "s3"

            print(f"  Version ID: {state_info.get('version_id', 'N/A')}")
            print(f"  ETag: {state_info.get('etag', 'N/A')}")
            print(f"  Last Modified: {state_info.get('last_modified', 'N/A')}")

            # Optionally download state file
            if args.download_state:
                state_path = os.path.join(args.output_dir, "terraform.tfstate")
                print(f"\nDownloading state to: {state_path}")
                download_s3_state(
                    args.state_bucket,
                    args.state_key,
                    state_path,
                    version_id=state_info.get("version_id"),
                    region=args.aws_region
                )
                state_info["backup_path"] = state_path
                state_info["backup_sha256"] = calculate_file_hash(state_path)

        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error accessing S3: {e}")
            sys.exit(1)

    else:
        # Local state
        print(f"\nCopying local state: {args.local_state}")
        try:
            state_info = copy_local_state(args.local_state, args.output_dir)
            print(f"  SHA256: {state_info.get('sha256', 'N/A')}")
            print(f"  Size: {state_info.get('size_bytes', 0)} bytes")
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    # Create manifest
    print(f"\nCreating backup manifest...")
    manifest = create_state_manifest(
        args.output_dir,
        args.environment,
        state_info,
        org_name=args.org_name,
        schedule_type=args.schedule,
    )

    print(f"\n✅ Backup complete!")
    print(f"  Snapshot ID: {manifest['snapshot_id']}")
    print(f"  Manifest: {args.output_dir}/MANIFEST.json")

    if state_info.get("version_id"):
        print(f"  State Version: {state_info['version_id']}")
        print(f"\n  To restore this state version:")
        print(f"    python restore_state.py --restore-state --version-id {state_info['version_id']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
