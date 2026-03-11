"""
Okta Access Gateway Application Management

Provides CRUD operations for OAG applications including
header-based apps, attributes, and policies.
"""

import logging
from typing import Optional, Dict, Any, List

from .oag_client import OAGClient, OAGAPIError

logger = logging.getLogger(__name__)


class OAGApplicationManager:
    """
    Manage Okta Access Gateway applications.

    Supports:
    - Header-based applications
    - Protected web resources with load balancing
    - Header/cookie attribute mappings
    - Access policies
    """

    def __init__(self, client: OAGClient):
        """
        Initialize application manager.

        Args:
            client: Authenticated OAGClient instance
        """
        self.client = client

    # ==================== Application CRUD ====================

    def list_applications(self) -> List[Dict[str, Any]]:
        """
        List all applications in Access Gateway.

        Returns:
            List of application objects
        """
        response = self.client.get('/api/v2/apps')
        return response.get('data', response) if isinstance(response, dict) else response

    def get_application(self, app_id: str) -> Dict[str, Any]:
        """
        Get a specific application by ID.

        Args:
            app_id: Application ID

        Returns:
            Application object
        """
        return self.client.get(f'/api/v2/apps/{app_id}')

    def get_application_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find an application by its label/name.

        Args:
            name: Application label

        Returns:
            Application object or None if not found
        """
        apps = self.list_applications()
        for app in apps:
            if app.get('label') == name:
                return app
        return None

    def create_application(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new header-based application.

        Args:
            config: Application configuration:
                - label: Application name (required)
                - public_domain: External hostname (required)
                - description: Optional description
                - protected_resources: List of backend servers
                - group: Assigned group name
                - policy: Policy type (Protected, Not Protected, etc.)

        Returns:
            Created application object
        """
        # Build application payload
        payload = {
            'type': 'header',
            'label': config['label'],
            'publicDomain': config['public_domain'],
        }

        if config.get('description'):
            payload['description'] = config['description']

        # Configure protected resources (backend servers)
        if config.get('protected_resources'):
            payload['protectedResources'] = self._build_protected_resources(
                config['protected_resources']
            )

        # Set group if specified
        if config.get('group'):
            payload['group'] = config['group']

        logger.info(f"Creating application: {config['label']}")
        return self.client.post('/api/v2/apps', payload)

    def update_application(self, app_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing application.

        Args:
            app_id: Application ID
            config: Updated configuration

        Returns:
            Updated application object
        """
        payload = {}

        if 'label' in config:
            payload['label'] = config['label']
        if 'description' in config:
            payload['description'] = config['description']
        if 'public_domain' in config:
            payload['publicDomain'] = config['public_domain']
        if 'protected_resources' in config:
            payload['protectedResources'] = self._build_protected_resources(
                config['protected_resources']
            )
        if 'group' in config:
            payload['group'] = config['group']

        logger.info(f"Updating application: {app_id}")
        return self.client.put(f'/api/v2/apps/{app_id}', payload)

    def delete_application(self, app_id: str) -> bool:
        """
        Delete an application.

        Args:
            app_id: Application ID

        Returns:
            True if successful
        """
        logger.info(f"Deleting application: {app_id}")
        return self.client.delete(f'/api/v2/apps/{app_id}')

    # ==================== Attributes ====================

    def list_attributes(self, app_id: str) -> List[Dict[str, Any]]:
        """
        List all attributes for an application.

        Args:
            app_id: Application ID

        Returns:
            List of attribute objects
        """
        response = self.client.get(f'/api/v2/apps/{app_id}/attributes')
        return response.get('data', response) if isinstance(response, dict) else response

    def add_attribute(self, app_id: str, attribute: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a header/cookie attribute to an application.

        Args:
            app_id: Application ID
            attribute: Attribute configuration:
                - source: Data source (IDP, Static, etc.)
                - field: Source field name (e.g., 'login', 'email')
                - type: Target type (Header or Cookie)
                - name: Header/cookie name (e.g., 'X-Remote-User')
                - value: Static value (if source is Static)

        Returns:
            Created attribute object
        """
        payload = {
            'dataSource': attribute.get('source', 'IDP'),
            'field': attribute['field'],
            'targetType': attribute.get('type', 'Header'),
            'name': attribute['name']
        }

        if attribute.get('value'):
            payload['value'] = attribute['value']

        logger.info(f"Adding attribute {attribute['name']} to app {app_id}")
        return self.client.post(f'/api/v2/apps/{app_id}/attributes', payload)

    def update_attribute(
        self,
        app_id: str,
        attribute_id: str,
        attribute: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing attribute.

        Args:
            app_id: Application ID
            attribute_id: Attribute ID
            attribute: Updated attribute configuration

        Returns:
            Updated attribute object
        """
        payload = {}

        if 'source' in attribute:
            payload['dataSource'] = attribute['source']
        if 'field' in attribute:
            payload['field'] = attribute['field']
        if 'type' in attribute:
            payload['targetType'] = attribute['type']
        if 'name' in attribute:
            payload['name'] = attribute['name']
        if 'value' in attribute:
            payload['value'] = attribute['value']

        return self.client.put(f'/api/v2/apps/{app_id}/attributes/{attribute_id}', payload)

    def delete_attribute(self, app_id: str, attribute_id: str) -> bool:
        """
        Delete an attribute.

        Args:
            app_id: Application ID
            attribute_id: Attribute ID

        Returns:
            True if successful
        """
        logger.info(f"Deleting attribute {attribute_id} from app {app_id}")
        return self.client.delete(f'/api/v2/apps/{app_id}/attributes/{attribute_id}')

    def sync_attributes(
        self,
        app_id: str,
        desired_attributes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synchronize attributes to match desired state.

        Args:
            app_id: Application ID
            desired_attributes: List of desired attribute configurations

        Returns:
            Summary of changes (added, updated, deleted)
        """
        current = self.list_attributes(app_id)
        current_by_name = {attr['name']: attr for attr in current}

        added = []
        updated = []
        deleted = []

        # Track desired attribute names
        desired_names = {attr['name'] for attr in desired_attributes}

        # Add or update attributes
        for attr in desired_attributes:
            name = attr['name']
            if name in current_by_name:
                # Check if update needed
                current_attr = current_by_name[name]
                if self._attribute_needs_update(current_attr, attr):
                    self.update_attribute(app_id, current_attr['id'], attr)
                    updated.append(name)
            else:
                # Add new attribute
                self.add_attribute(app_id, attr)
                added.append(name)

        # Delete attributes not in desired state
        for name, attr in current_by_name.items():
            if name not in desired_names:
                self.delete_attribute(app_id, attr['id'])
                deleted.append(name)

        return {
            'added': added,
            'updated': updated,
            'deleted': deleted
        }

    # ==================== Policies ====================

    def get_policies(self, app_id: str) -> List[Dict[str, Any]]:
        """
        Get policies for an application.

        Args:
            app_id: Application ID

        Returns:
            List of policy objects
        """
        response = self.client.get(f'/api/v2/apps/{app_id}/policies')
        return response.get('data', response) if isinstance(response, dict) else response

    def add_policy(self, app_id: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a policy to an application.

        Args:
            app_id: Application ID
            policy: Policy configuration:
                - type: Policy type (Protected, NotProtected, ProtectedRule, Adaptive)
                - pattern: URL pattern to match
                - priority: Policy priority (lower = higher priority)
                - rules: Access rules (for ProtectedRule type)

        Returns:
            Created policy object
        """
        payload = {
            'type': policy['type'],
            'pattern': policy.get('pattern', '/*'),
            'priority': policy.get('priority', 100)
        }

        if policy.get('rules'):
            payload['rules'] = policy['rules']

        logger.info(f"Adding policy to app {app_id}: {policy['type']}")
        return self.client.post(f'/api/v2/apps/{app_id}/policies', payload)

    # ==================== Certificates ====================

    def assign_certificate(self, app_id: str, certificate_id: str) -> Dict[str, Any]:
        """
        Assign a certificate to an application.

        Args:
            app_id: Application ID
            certificate_id: Certificate ID

        Returns:
            Updated application object
        """
        payload = {'certificateId': certificate_id}
        return self.client.put(f'/api/v2/apps/{app_id}/certificate', payload)

    def list_certificates(self) -> List[Dict[str, Any]]:
        """
        List all available certificates.

        Returns:
            List of certificate objects
        """
        response = self.client.get('/api/v2/certificates')
        return response.get('data', response) if isinstance(response, dict) else response

    # ==================== High-Level Operations ====================

    def deploy_application(self, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Deploy an application with full configuration.

        This is a high-level operation that:
        1. Creates the application (or updates if exists)
        2. Configures protected resources
        3. Sets up header attributes
        4. Configures policies

        Args:
            config: Complete application configuration
            dry_run: Preview changes without applying

        Returns:
            Deployment result summary
        """
        result = {
            'label': config['label'],
            'action': None,
            'app_id': None,
            'attributes': {'added': [], 'updated': [], 'deleted': []},
            'dry_run': dry_run
        }

        # Check if app exists
        existing = self.get_application_by_name(config['label'])

        if existing:
            result['action'] = 'update'
            result['app_id'] = existing['id']

            if not dry_run:
                # Update application
                self.update_application(existing['id'], config)

                # Sync attributes
                if config.get('attributes'):
                    result['attributes'] = self.sync_attributes(
                        existing['id'],
                        config['attributes']
                    )
        else:
            result['action'] = 'create'

            if not dry_run:
                # Create application
                app = self.create_application(config)
                result['app_id'] = app.get('id')

                # Add attributes
                if config.get('attributes'):
                    for attr in config['attributes']:
                        self.add_attribute(app['id'], attr)
                        result['attributes']['added'].append(attr['name'])

                # Add default policy if specified
                if config.get('policy'):
                    self.add_policy(app['id'], {
                        'type': config['policy'],
                        'pattern': '/*'
                    })

        return result

    def import_applications(self) -> List[Dict[str, Any]]:
        """
        Import all applications from OAG to configuration format.

        Returns:
            List of application configurations suitable for JSON export
        """
        apps = self.list_applications()
        configs = []

        for app in apps:
            config = {
                'label': app.get('label'),
                'public_domain': app.get('publicDomain'),
                'description': app.get('description', ''),
                'protected_resources': [],
                'attributes': []
            }

            # Get protected resources
            if app.get('protectedResources'):
                for resource in app['protectedResources']:
                    config['protected_resources'].append({
                        'url': resource.get('url'),
                        'weight': resource.get('weight', 100)
                    })

            # Get attributes
            try:
                attrs = self.list_attributes(app['id'])
                for attr in attrs:
                    config['attributes'].append({
                        'source': attr.get('dataSource', 'IDP'),
                        'field': attr.get('field'),
                        'type': attr.get('targetType', 'Header'),
                        'name': attr.get('name')
                    })
            except Exception as e:
                logger.warning(f"Failed to get attributes for {app['id']}: {e}")

            configs.append(config)

        return configs

    # ==================== Helper Methods ====================

    def _build_protected_resources(
        self,
        resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build protected resources payload.

        Args:
            resources: List of resource configurations

        Returns:
            Formatted payload for API
        """
        result = []
        for resource in resources:
            entry = {
                'url': resource['url'],
                'weight': resource.get('weight', 100)
            }

            # Health check configuration
            if resource.get('health_check'):
                hc = resource['health_check']
                entry['healthCheck'] = {
                    'enabled': True,
                    'path': hc.get('path', '/health'),
                    'method': hc.get('method', 'GET'),
                    'expectedStatus': hc.get('expected_status', 200),
                    'interval': hc.get('interval', 10),
                    'timeout': hc.get('timeout', 1),
                    'unhealthyThreshold': hc.get('unhealthy_threshold', 3),
                    'healthyThreshold': hc.get('healthy_threshold', 2)
                }

            result.append(entry)

        return result

    def _attribute_needs_update(
        self,
        current: Dict[str, Any],
        desired: Dict[str, Any]
    ) -> bool:
        """
        Check if an attribute needs to be updated.

        Args:
            current: Current attribute state
            desired: Desired attribute state

        Returns:
            True if update needed
        """
        # Map desired keys to API keys
        mappings = {
            'source': 'dataSource',
            'field': 'field',
            'type': 'targetType',
            'name': 'name'
        }

        for desired_key, api_key in mappings.items():
            if desired.get(desired_key) != current.get(api_key):
                return True

        return False
