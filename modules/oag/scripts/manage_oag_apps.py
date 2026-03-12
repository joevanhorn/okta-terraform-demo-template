#!/usr/bin/env python3
"""
Manage Okta Access Gateway Applications

CLI tool for deploying and managing OAG applications from configuration files.

Usage:
    python manage_oag_apps.py --config config/oag_apps.json --action deploy
    python manage_oag_apps.py --config config/oag_apps.json --action list
    python manage_oag_apps.py --config config/oag_apps.json --action delete --app "My App"

Environment Variables:
    OAG_HOSTNAME: OAG hostname (can also be in config)
    OAG_CLIENT_ID: Client ID (can also be in config)
    OAG_PRIVATE_KEY_PATH: Path to private key
    OAG_PRIVATE_KEY: Private key content
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from oag import OAGClient, OAGApplicationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def get_client(config: Dict[str, Any]) -> OAGClient:
    """
    Create OAG client from config or environment variables.

    Config gateway section takes precedence over environment variables.
    """
    gateway_config = config.get('gateway', {})

    # Get values from config or environment
    hostname = gateway_config.get('hostname') or os.environ.get('OAG_HOSTNAME')
    client_id = gateway_config.get('client_id') or os.environ.get('OAG_CLIENT_ID')
    private_key_path = gateway_config.get('private_key_path') or os.environ.get('OAG_PRIVATE_KEY_PATH')
    private_key = gateway_config.get('private_key') or os.environ.get('OAG_PRIVATE_KEY')
    verify_ssl = gateway_config.get('verify_ssl', True)

    if not hostname:
        raise ValueError("OAG hostname not configured (config.gateway.hostname or OAG_HOSTNAME)")
    if not client_id:
        raise ValueError("OAG client_id not configured (config.gateway.client_id or OAG_CLIENT_ID)")
    if not private_key_path and not private_key:
        raise ValueError("OAG private key not configured (config.gateway.private_key_path or OAG_PRIVATE_KEY_PATH)")

    return OAGClient(
        hostname=hostname,
        client_id=client_id,
        private_key_path=private_key_path,
        private_key=private_key,
        verify_ssl=verify_ssl
    )


def action_list(manager: OAGApplicationManager, args: argparse.Namespace) -> None:
    """List all applications."""
    apps = manager.list_applications()

    if not apps:
        print("No applications found")
        return

    print(f"\n{'Label':<40} {'Public Domain':<40} {'ID'}")
    print("-" * 100)

    for app in apps:
        label = app.get('label', 'N/A')[:39]
        domain = app.get('publicDomain', 'N/A')[:39]
        app_id = app.get('id', 'N/A')
        print(f"{label:<40} {domain:<40} {app_id}")

    print(f"\nTotal: {len(apps)} applications")


def action_deploy(
    manager: OAGApplicationManager,
    config: Dict[str, Any],
    args: argparse.Namespace
) -> None:
    """Deploy applications from configuration."""
    apps = config.get('applications', [])

    if not apps:
        print("No applications defined in configuration")
        return

    # Filter by app name if specified
    if args.app:
        apps = [app for app in apps if app.get('label') == args.app]
        if not apps:
            print(f"Application '{args.app}' not found in configuration")
            return

    results = []
    for app_config in apps:
        try:
            result = manager.deploy_application(app_config, dry_run=args.dry_run)
            results.append(result)

            if args.dry_run:
                action = f"Would {result['action']}"
            else:
                action = f"{result['action'].capitalize()}d"

            print(f"\n{action}: {result['label']}")

            if result['app_id']:
                print(f"  App ID: {result['app_id']}")

            if result['attributes']['added']:
                print(f"  Attributes added: {', '.join(result['attributes']['added'])}")
            if result['attributes']['updated']:
                print(f"  Attributes updated: {', '.join(result['attributes']['updated'])}")
            if result['attributes']['deleted']:
                print(f"  Attributes deleted: {', '.join(result['attributes']['deleted'])}")

        except Exception as e:
            logger.error(f"Failed to deploy {app_config.get('label')}: {e}")
            results.append({
                'label': app_config.get('label'),
                'action': 'error',
                'error': str(e)
            })

    # Summary
    created = sum(1 for r in results if r.get('action') == 'create')
    updated = sum(1 for r in results if r.get('action') == 'update')
    errors = sum(1 for r in results if r.get('action') == 'error')

    print(f"\n{'Dry run ' if args.dry_run else ''}Summary: {created} created, {updated} updated, {errors} errors")


def action_delete(manager: OAGApplicationManager, args: argparse.Namespace) -> None:
    """Delete an application."""
    if not args.app:
        print("Error: --app is required for delete action")
        sys.exit(1)

    # Find app by name
    app = manager.get_application_by_name(args.app)
    if not app:
        print(f"Application '{args.app}' not found")
        sys.exit(1)

    if args.dry_run:
        print(f"Would delete: {args.app} (ID: {app['id']})")
        return

    # Confirm deletion
    if not args.force:
        confirm = input(f"Delete application '{args.app}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return

    manager.delete_application(app['id'])
    print(f"Deleted: {args.app}")


def action_show(manager: OAGApplicationManager, args: argparse.Namespace) -> None:
    """Show details of an application."""
    if not args.app:
        print("Error: --app is required for show action")
        sys.exit(1)

    # Find app by name
    app = manager.get_application_by_name(args.app)
    if not app:
        print(f"Application '{args.app}' not found")
        sys.exit(1)

    print(f"\nApplication: {app.get('label')}")
    print(f"  ID: {app.get('id')}")
    print(f"  Public Domain: {app.get('publicDomain')}")
    print(f"  Description: {app.get('description', 'N/A')}")

    # Show protected resources
    resources = app.get('protectedResources', [])
    if resources:
        print(f"\n  Protected Resources:")
        for resource in resources:
            print(f"    - {resource.get('url')} (weight: {resource.get('weight', 100)})")

    # Show attributes
    try:
        attrs = manager.list_attributes(app['id'])
        if attrs:
            print(f"\n  Attributes:")
            for attr in attrs:
                source = attr.get('dataSource', 'IDP')
                field = attr.get('field', 'N/A')
                target = attr.get('targetType', 'Header')
                name = attr.get('name', 'N/A')
                print(f"    - {source}.{field} → {target}: {name}")
    except Exception as e:
        logger.warning(f"Failed to get attributes: {e}")


def action_import(
    manager: OAGApplicationManager,
    config: Dict[str, Any],
    args: argparse.Namespace
) -> None:
    """Import applications from OAG to configuration format."""
    apps = manager.import_applications()

    if not apps:
        print("No applications found to import")
        return

    # Build output config
    output = {
        'gateway': config.get('gateway', {}),
        'applications': apps
    }

    # Write to file or stdout
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Exported {len(apps)} applications to {args.output}")
    else:
        print(json.dumps(output, indent=2))


def action_health(client: OAGClient, args: argparse.Namespace) -> None:
    """Check OAG API health."""
    status = client.health_check()

    print(f"\nOAG Health Check")
    print(f"  Hostname: {status['hostname']}")
    print(f"  Status: {status['status']}")
    print(f"  Authenticated: {status['authenticated']}")

    if status.get('error'):
        print(f"  Error: {status['error']}")


def main():
    parser = argparse.ArgumentParser(
        description='Manage Okta Access Gateway Applications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all applications
  python manage_oag_apps.py --config config/oag_apps.json --action list

  # Deploy all applications (dry run)
  python manage_oag_apps.py --config config/oag_apps.json --action deploy --dry-run

  # Deploy specific application
  python manage_oag_apps.py --config config/oag_apps.json --action deploy --app "My App"

  # Show application details
  python manage_oag_apps.py --config config/oag_apps.json --action show --app "My App"

  # Import existing applications
  python manage_oag_apps.py --config config/oag_apps.json --action import --output imported.json

  # Check health
  python manage_oag_apps.py --config config/oag_apps.json --action health
        """
    )

    parser.add_argument(
        '--config', '-c',
        required=True,
        help='Path to OAG configuration file (JSON)'
    )

    parser.add_argument(
        '--action', '-a',
        required=True,
        choices=['list', 'deploy', 'delete', 'show', 'import', 'health'],
        help='Action to perform'
    )

    parser.add_argument(
        '--app',
        help='Application name (for deploy, delete, show actions)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying'
    )

    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation prompts'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file (for import action)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Create client
    try:
        client = get_client(config)
    except Exception as e:
        logger.error(f"Failed to create OAG client: {e}")
        sys.exit(1)

    # Create manager
    manager = OAGApplicationManager(client)

    # Execute action
    try:
        if args.action == 'list':
            action_list(manager, args)
        elif args.action == 'deploy':
            action_deploy(manager, config, args)
        elif args.action == 'delete':
            action_delete(manager, args)
        elif args.action == 'show':
            action_show(manager, args)
        elif args.action == 'import':
            action_import(manager, config, args)
        elif args.action == 'health':
            action_health(client, args)
    except Exception as e:
        logger.error(f"Action failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
