#!/usr/bin/env python3
"""
setup_ssf_provider.py

Post-Terraform setup for the SSF (Shared Signals Framework) security events provider.

Prerequisites:
  - Run `terraform apply` first to create the Lambda JWKS endpoint, RSA key pair,
    and SSM parameters. This script reads the config Terraform created.

This script:
  1. Reads provider config from SSM (JWKS URL, issuer, key_id — created by Terraform)
  2. Registers the provider with Okta via POST /api/v1/security-events-providers
  3. Updates the SSM config parameter with the Okta-assigned provider_id

After running this, use `trigger_itp_demo.py --mode ssf` to send signals.

Usage:
    # Register provider with Okta (reads config from SSM)
    python3 scripts/setup_ssf_provider.py --ssm-prefix /myorg/itp/ssf-demo

    # List existing providers
    python3 scripts/setup_ssf_provider.py --list

    # Delete a provider
    python3 scripts/setup_ssf_provider.py --delete --provider-id sep1234567890
"""

import os
import sys
import json
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Register SSF security events provider with Okta (post-Terraform)"
    )
    parser.add_argument(
        "--org-name",
        default=os.environ.get("OKTA_ORG_NAME"),
        help="Okta organization name",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OKTA_BASE_URL", "okta.com"),
        help="Okta base URL",
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("OKTA_API_TOKEN"),
        help="Okta API token",
    )

    # SSM config
    parser.add_argument(
        "--ssm-prefix",
        required=False,
        default=None,
        help="SSM parameter path prefix (e.g., /myorg/itp/ssf-demo)",
    )
    parser.add_argument(
        "--provider-name",
        default="ITP Demo Signal Source",
        help="Display name for the provider in Okta",
    )
    parser.add_argument(
        "--aws-region",
        default=None,
        help="AWS region for SSM (default: boto3 default)",
    )
    parser.add_argument(
        "--aws-profile",
        default=os.environ.get("AWS_PROFILE"),
        help="AWS CLI profile name",
    )

    # Alternative actions
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing security events providers",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete a security events provider",
    )
    parser.add_argument(
        "--provider-id",
        help="Provider ID (for --delete)",
    )

    args = parser.parse_args()

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    # Import after arg parsing to fail fast on missing args
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from itp.ssf_provider import SSFProvider

    provider = SSFProvider(
        org_name=args.org_name,
        base_url=args.base_url,
        api_token=args.api_token,
    )

    # --- List providers ---
    if args.list:
        print("Registered Security Events Providers:")
        print("-" * 60)
        providers = provider.list_providers()
        if not providers:
            print("  (none)")
        for p in providers:
            settings = p.get("settings", {})
            print(f"  ID:     {p.get('id')}")
            print(f"  Name:   {p.get('name')}")
            print(f"  Type:   {p.get('type')}")
            print(f"  Issuer: {settings.get('issuer')}")
            print(f"  JWKS:   {settings.get('jwks_url')}")
            print()
        sys.exit(0)

    # --- Delete provider ---
    if args.delete:
        if not args.provider_id:
            print("Error: --provider-id is required with --delete")
            sys.exit(1)
        print(f"Deleting provider: {args.provider_id}...")
        provider.delete_provider(args.provider_id)
        print("  Done.")
        sys.exit(0)

    # --- Register with Okta (post-Terraform) ---
    if not args.ssm_prefix:
        print("Error: --ssm-prefix is required for registration")
        print("  Example: --ssm-prefix /myorg/itp/ssf-demo")
        sys.exit(1)

    print("=" * 60)
    print("SSF PROVIDER REGISTRATION (Post-Terraform)")
    print("=" * 60)
    print(f"  Okta org:  {args.org_name}.{args.base_url}")
    print(f"  SSM path:  {args.ssm_prefix}")

    try:
        import boto3

        session_kwargs = {}
        if args.aws_region:
            session_kwargs["region_name"] = args.aws_region
        if args.aws_profile:
            session_kwargs["profile_name"] = args.aws_profile
        boto_session = boto3.Session(**session_kwargs)
        ssm = boto_session.client("ssm")

        # Step 1: Read config from SSM (created by Terraform)
        print("\n  [1/3] Reading provider config from SSM...")
        config_resp = ssm.get_parameter(Name=f"{args.ssm_prefix}/provider-config")
        config = json.loads(config_resp["Parameter"]["Value"])

        jwks_url = config["jwks_url"]
        issuer = config["issuer"]
        key_id = config["key_id"]

        print(f"         JWKS URL: {jwks_url}")
        print(f"         Issuer:   {issuer}")
        print(f"         Key ID:   {key_id}")

        if config.get("provider_id") and config["provider_id"] != "pending-registration":
            print(f"\n  Provider already registered: {config['provider_id']}")
            print("  Use --delete to remove and re-register if needed.")
            sys.exit(0)

        # Step 2: Register with Okta
        print(f"\n  [2/3] Registering with Okta...")
        result = provider.register_provider(
            name=args.provider_name,
            issuer=issuer,
            jwks_url=jwks_url,
        )
        provider_id = result.get("id")
        print(f"         Provider ID: {provider_id}")

        # Step 3: Update SSM config with provider_id
        print(f"\n  [3/3] Updating SSM config with provider ID...")
        config["provider_id"] = provider_id
        config["provider_name"] = args.provider_name
        ssm.put_parameter(
            Name=f"{args.ssm_prefix}/provider-config",
            Value=json.dumps(config),
            Type="String",
            Overwrite=True,
        )
        print(f"         Updated: {args.ssm_prefix}/provider-config")

        print("\n" + "=" * 60)
        print("REGISTRATION COMPLETE")
        print("=" * 60)
        print(f"  Provider ID: {provider_id}")
        print(f"  Issuer:      {issuer}")
        print(f"  JWKS URL:    {jwks_url}")
        print()
        print("Test with:")
        print("  python3 scripts/trigger_itp_demo.py --mode ssf \\")
        print("    --user <email> --risk-level HIGH --monitor")

    except Exception as e:
        print(f"\nRegistration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
