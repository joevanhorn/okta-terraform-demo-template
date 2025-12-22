#!/usr/bin/env python3
"""
State-based restore for Okta Terraform tenants.

This script restores Terraform state to a specific S3 version, then optionally
runs terraform apply to sync the actual resources with the restored state.

Restore Modes:
1. --restore-state: Only restore S3 state to the specified version
2. --full-restore: Restore state AND run terraform apply to sync resources

Usage:
    # Restore state only (rollback S3 to previous version)
    python restore_state.py \
        --manifest environments/mycompany/backups/state-based/2025-01-15T10-30-00/MANIFEST.json \
        --restore-state \
        --dry-run

    # Full restore (state + terraform apply)
    python restore_state.py \
        --manifest environments/mycompany/backups/state-based/latest/MANIFEST.json \
        --full-restore \
        --dry-run

    # Restore to specific version ID
    python restore_state.py \
        --state-bucket okta-terraform-demo \
        --state-key Okta-GitOps/mycompany/terraform.tfstate \
        --version-id "abc123..." \
        --restore-state

Environment Variables:
    AWS_REGION          - AWS region for S3 (default: us-east-1)
    OKTA_ORG_NAME       - Okta org name
    OKTA_BASE_URL       - Okta base URL (default: okta.com)
    OKTA_API_TOKEN      - Okta API token
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load and validate a backup manifest file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Validate manifest
    if manifest.get("backup_type") != "state-based":
        raise ValueError(f"Invalid manifest: expected backup_type='state-based', got '{manifest.get('backup_type')}'")

    if "terraform_state" not in manifest:
        raise ValueError("Invalid manifest: missing terraform_state section")

    return manifest


def get_s3_state_version(bucket: str, key: str, region: str = "us-east-1") -> Dict[str, Any]:
    """Get the current version of the Terraform state in S3."""
    if not HAS_BOTO3:
        raise RuntimeError("boto3 is required for S3 operations")

    s3 = boto3.client("s3", region_name=region)

    response = s3.head_object(Bucket=bucket, Key=key)
    return {
        "version_id": response.get("VersionId"),
        "etag": response.get("ETag", "").strip('"'),
        "last_modified": response.get("LastModified").isoformat() if response.get("LastModified") else None,
    }


def list_state_versions(bucket: str, key: str, region: str = "us-east-1", limit: int = 10) -> list:
    """List available versions of the state file."""
    if not HAS_BOTO3:
        raise RuntimeError("boto3 is required for S3 operations")

    s3 = boto3.client("s3", region_name=region)

    response = s3.list_object_versions(Bucket=bucket, Prefix=key, MaxKeys=limit)

    versions = []
    for version in response.get("Versions", []):
        if version.get("Key") == key:
            versions.append({
                "version_id": version.get("VersionId"),
                "last_modified": version.get("LastModified").isoformat() if version.get("LastModified") else None,
                "size": version.get("Size"),
                "is_latest": version.get("IsLatest", False),
            })

    return versions


def restore_s3_state_version(
    bucket: str,
    key: str,
    target_version_id: str,
    region: str = "us-east-1",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Restore S3 state to a specific version by copying that version as the latest.

    This works by:
    1. Getting the state from the target version
    2. Uploading it as a new version (which becomes current)
    """
    if not HAS_BOTO3:
        raise RuntimeError("boto3 is required for S3 operations")

    s3 = boto3.client("s3", region_name=region)

    # Get current version for logging
    current = get_s3_state_version(bucket, key, region)
    print(f"Current state version: {current.get('version_id')}")
    print(f"Target state version: {target_version_id}")

    if current.get("version_id") == target_version_id:
        print("⚠️  Target version is already the current version")
        return {"status": "already_current", "version_id": target_version_id}

    if dry_run:
        print("\n🔍 DRY RUN - Would perform the following:")
        print(f"  1. Download state from version: {target_version_id}")
        print(f"  2. Upload as new current version")
        print(f"  3. Previous version ({current.get('version_id')}) preserved in version history")
        return {"status": "dry_run", "would_restore": target_version_id}

    # Download the target version to a temp file
    print(f"\nDownloading state from version: {target_version_id}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tfstate") as tmp:
        tmp_path = tmp.name

    try:
        s3.download_file(
            bucket, key, tmp_path,
            ExtraArgs={"VersionId": target_version_id}
        )

        # Upload as new current version
        print(f"Uploading as new current version...")
        response = s3.upload_file(tmp_path, bucket, key)

        # Get the new version ID
        new_version = get_s3_state_version(bucket, key, region)
        print(f"✅ State restored! New version: {new_version.get('version_id')}")

        return {
            "status": "restored",
            "previous_version": current.get("version_id"),
            "restored_from": target_version_id,
            "new_version": new_version.get("version_id"),
        }

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def run_terraform_apply(
    terraform_dir: str,
    dry_run: bool = True,
    auto_approve: bool = False
) -> Dict[str, Any]:
    """Run terraform apply to sync resources with state."""
    if not os.path.isdir(terraform_dir):
        raise FileNotFoundError(f"Terraform directory not found: {terraform_dir}")

    print(f"\nRunning Terraform in: {terraform_dir}")

    # Initialize terraform
    print("Initializing Terraform...")
    init_result = subprocess.run(
        ["terraform", "init", "-input=false"],
        cwd=terraform_dir,
        capture_output=True,
        text=True
    )

    if init_result.returncode != 0:
        print(f"❌ Terraform init failed:\n{init_result.stderr}")
        return {"status": "init_failed", "error": init_result.stderr}

    # Run plan
    print("Running Terraform plan...")
    plan_result = subprocess.run(
        ["terraform", "plan", "-input=false", "-out=restore.tfplan"],
        cwd=terraform_dir,
        capture_output=True,
        text=True
    )

    print(plan_result.stdout)

    if plan_result.returncode != 0:
        print(f"❌ Terraform plan failed:\n{plan_result.stderr}")
        return {"status": "plan_failed", "error": plan_result.stderr}

    if dry_run:
        print("\n🔍 DRY RUN - Terraform plan complete. Would apply the above changes.")
        # Cleanup plan file
        plan_file = os.path.join(terraform_dir, "restore.tfplan")
        if os.path.exists(plan_file):
            os.unlink(plan_file)
        return {"status": "dry_run", "plan": plan_result.stdout}

    # Apply
    print("\nApplying Terraform changes...")
    apply_cmd = ["terraform", "apply", "-input=false"]
    if auto_approve:
        apply_cmd.append("-auto-approve")
    apply_cmd.append("restore.tfplan")

    apply_result = subprocess.run(
        apply_cmd,
        cwd=terraform_dir,
        capture_output=True,
        text=True
    )

    print(apply_result.stdout)

    # Cleanup
    plan_file = os.path.join(terraform_dir, "restore.tfplan")
    if os.path.exists(plan_file):
        os.unlink(plan_file)

    if apply_result.returncode != 0:
        print(f"❌ Terraform apply failed:\n{apply_result.stderr}")
        return {"status": "apply_failed", "error": apply_result.stderr}

    return {"status": "applied", "output": apply_result.stdout}


def main():
    parser = argparse.ArgumentParser(
        description="Restore Okta Terraform state from backup"
    )

    # Source options (either manifest or direct S3 params)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--manifest", "-m", type=str,
                              help="Path to backup manifest file")
    source_group.add_argument("--version-id", type=str,
                              help="Specific S3 version ID to restore (requires --state-bucket and --state-key)")

    # S3 options (required if using --version-id)
    parser.add_argument("--state-bucket", type=str,
                        help="S3 bucket containing Terraform state")
    parser.add_argument("--state-key", type=str,
                        help="S3 key for Terraform state file")
    parser.add_argument("--aws-region", type=str, default="us-east-1",
                        help="AWS region for S3 (default: us-east-1)")

    # Restore mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--restore-state", action="store_true",
                            help="Only restore S3 state to the backup version")
    mode_group.add_argument("--full-restore", action="store_true",
                            help="Restore state AND run terraform apply")
    mode_group.add_argument("--list-versions", action="store_true",
                            help="List available state versions (no restore)")

    # Terraform options
    parser.add_argument("--terraform-dir", type=str,
                        help="Terraform directory (for --full-restore)")
    parser.add_argument("--auto-approve", action="store_true",
                        help="Auto-approve terraform apply (no prompts)")

    # Common options
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without applying")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Validate arguments
    if args.version_id and (not args.state_bucket or not args.state_key):
        parser.error("--state-bucket and --state-key are required when using --version-id")

    if args.full_restore and not args.terraform_dir and not args.manifest:
        parser.error("--terraform-dir is required for --full-restore (or use --manifest)")

    # Load configuration
    bucket = args.state_bucket
    key = args.state_key
    region = args.aws_region
    version_id = args.version_id
    terraform_dir = args.terraform_dir

    if args.manifest:
        print(f"Loading manifest: {args.manifest}")
        manifest = load_manifest(args.manifest)
        state_info = manifest.get("terraform_state", {})

        if state_info.get("source") == "s3":
            bucket = state_info.get("bucket")
            key = state_info.get("key")
            region = state_info.get("region", "us-east-1")
            version_id = state_info.get("version_id")
        else:
            print("❌ Manifest uses local state, not S3. Cannot restore S3 version.")
            sys.exit(1)

        # Infer terraform directory from manifest
        if not terraform_dir and args.full_restore:
            env = manifest.get("environment")
            terraform_dir = f"environments/{env}/terraform"

        print(f"  Snapshot ID: {manifest.get('snapshot_id')}")
        print(f"  Environment: {manifest.get('environment')}")
        print(f"  Created: {manifest.get('created_at')}")
        print(f"  State Version: {version_id}")

    # List versions mode
    if args.list_versions:
        print(f"\nAvailable state versions for s3://{bucket}/{key}:")
        versions = list_state_versions(bucket, key, region)

        for i, v in enumerate(versions):
            marker = "→ " if v.get("is_latest") else "  "
            print(f"{marker}{v.get('version_id')[:12]}... | {v.get('last_modified')} | {v.get('size')} bytes")

        return 0

    # Restore state mode
    if args.restore_state or args.full_restore:
        print(f"\n{'=' * 60}")
        print("RESTORE STATE")
        print(f"{'=' * 60}")
        print(f"Bucket: {bucket}")
        print(f"Key: {key}")
        print(f"Target Version: {version_id}")

        if args.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made")

        result = restore_s3_state_version(
            bucket, key, version_id, region,
            dry_run=args.dry_run
        )

        if result.get("status") == "already_current":
            print("State is already at target version")
        elif result.get("status") != "restored" and not args.dry_run:
            print(f"❌ State restore failed")
            return 1

    # Full restore mode - also run terraform
    if args.full_restore:
        print(f"\n{'=' * 60}")
        print("TERRAFORM APPLY")
        print(f"{'=' * 60}")
        print(f"Directory: {terraform_dir}")

        if args.dry_run:
            print("\n⚠️  DRY RUN MODE - Will run plan only")

        result = run_terraform_apply(
            terraform_dir,
            dry_run=args.dry_run,
            auto_approve=args.auto_approve
        )

        if result.get("status") not in ["applied", "dry_run"]:
            print(f"❌ Terraform failed: {result.get('status')}")
            return 1

    print(f"\n{'=' * 60}")
    if args.dry_run:
        print("✅ DRY RUN COMPLETE - No changes were made")
        print("\nTo perform actual restore, run again without --dry-run")
    else:
        print("✅ RESTORE COMPLETE")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
