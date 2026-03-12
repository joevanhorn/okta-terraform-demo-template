# OAG API Management Guide

Reference guide for using the Python scripts to manage Okta Access Gateway applications.

## Overview

The OAG management scripts provide programmatic access to the OAG API for:
- Creating and managing header-based applications
- Configuring protected resources and load balancing
- Managing header/cookie attributes
- Importing existing configurations

---

## Prerequisites

### Python Dependencies

```bash
pip install requests pyjwt cryptography
```

### OAG API Access

1. Enable API in OAG Admin Console (Settings → API)
2. Download client ID and private key
3. Configure credentials:
   ```bash
   mkdir -p ~/.oag
   # Save private key to ~/.oag/private_key.pem
   chmod 600 ~/.oag/private_key.pem
   ```

---

## CLI Reference

### Basic Usage

```bash
python scripts/manage_oag_apps.py --config <config_file> --action <action> [options]
```

### Actions

| Action | Description |
|--------|-------------|
| `list` | List all applications |
| `deploy` | Deploy applications from config |
| `delete` | Delete an application |
| `show` | Show application details |
| `import` | Import apps from OAG to config |
| `health` | Check API health |

### Options

| Option | Description |
|--------|-------------|
| `--config, -c` | Path to configuration file (required) |
| `--action, -a` | Action to perform (required) |
| `--app` | Application name (for specific operations) |
| `--dry-run` | Preview changes without applying |
| `--force, -f` | Skip confirmation prompts |
| `--output, -o` | Output file (for import) |
| `--verbose, -v` | Enable debug logging |

### Examples

```bash
# List all applications
python scripts/manage_oag_apps.py -c config/oag_apps.json -a list

# Deploy with dry run
python scripts/manage_oag_apps.py -c config/oag_apps.json -a deploy --dry-run

# Deploy specific app
python scripts/manage_oag_apps.py -c config/oag_apps.json -a deploy --app "My App"

# Show app details
python scripts/manage_oag_apps.py -c config/oag_apps.json -a show --app "My App"

# Delete app (with confirmation)
python scripts/manage_oag_apps.py -c config/oag_apps.json -a delete --app "My App"

# Import existing apps
python scripts/manage_oag_apps.py -c config/oag_apps.json -a import -o imported.json

# Check health
python scripts/manage_oag_apps.py -c config/oag_apps.json -a health
```

---

## Configuration File

### Structure

```json
{
  "gateway": {
    "hostname": "oag.example.com",
    "client_id": "your_client_id",
    "private_key_path": "~/.oag/private_key.pem",
    "verify_ssl": true
  },
  "applications": [
    {
      "label": "Application Name",
      "public_domain": "app.example.com",
      "description": "Optional description",
      "protected_resources": [...],
      "attributes": [...],
      "group": "Group-Name",
      "policy": "Protected"
    }
  ]
}
```

### Gateway Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `hostname` | Yes | OAG hostname |
| `client_id` | Yes | API client ID |
| `private_key_path` | Yes* | Path to private key file |
| `private_key` | Yes* | Private key content (alternative) |
| `verify_ssl` | No | Verify SSL certificates (default: true) |

*Either `private_key_path` or `private_key` is required.

### Application Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `label` | Yes | Application name |
| `public_domain` | Yes | External domain |
| `description` | No | Description |
| `protected_resources` | Yes | Backend servers |
| `attributes` | No | Header/cookie mappings |
| `group` | No | Assigned group |
| `policy` | No | Policy type |

### Protected Resources

```json
"protected_resources": [
  {
    "url": "https://server:8443",
    "weight": 100,
    "health_check": {
      "path": "/health",
      "method": "GET",
      "expected_status": 200,
      "interval": 10,
      "timeout": 3,
      "unhealthy_threshold": 3,
      "healthy_threshold": 2
    }
  }
]
```

### Attributes

```json
"attributes": [
  {
    "source": "IDP",
    "field": "login",
    "type": "Header",
    "name": "X-Remote-User"
  }
]
```

| Field | Values | Description |
|-------|--------|-------------|
| `source` | IDP, Static | Data source |
| `field` | string | Source field name |
| `type` | Header, Cookie | Target type |
| `name` | string | Header/cookie name |
| `value` | string | Static value (if source=Static) |

---

## Python API

### OAGClient

```python
from scripts.oag import OAGClient

# From configuration
client = OAGClient(
    hostname="oag.example.com",
    client_id="your_client_id",
    private_key_path="~/.oag/private_key.pem"
)

# From environment variables
client = OAGClient.from_environment()

# Make API calls
apps = client.get('/api/v2/apps')
```

### OAGApplicationManager

```python
from scripts.oag import OAGClient, OAGApplicationManager

client = OAGClient.from_environment()
manager = OAGApplicationManager(client)

# List applications
apps = manager.list_applications()

# Create application
config = {
    'label': 'My App',
    'public_domain': 'app.example.com',
    'protected_resources': [
        {'url': 'https://backend:8443', 'weight': 100}
    ]
}
app = manager.create_application(config)

# Add attribute
manager.add_attribute(app['id'], {
    'source': 'IDP',
    'field': 'login',
    'type': 'Header',
    'name': 'X-Remote-User'
})

# Deploy complete application
result = manager.deploy_application(config, dry_run=False)
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OAG_HOSTNAME` | OAG hostname |
| `OAG_CLIENT_ID` | API client ID |
| `OAG_PRIVATE_KEY_PATH` | Path to private key |
| `OAG_PRIVATE_KEY` | Private key content |
| `OAG_VERIFY_SSL` | Verify SSL (true/false) |

---

## API Scopes

| Scope | Purpose |
|-------|---------|
| `okta.oag.app.manage` | Create and manage apps |
| `okta.oag.app.read` | Read app details |
| `okta.oag.cert.read` | Read certificates |
| `okta.oag.idp.manage` | Manage identity providers |
| `okta.oag.idp.read` | Read identity providers |

---

## Error Handling

### Common Errors

**OAGAuthenticationError**
- Invalid client ID or private key
- Expired token
- API not enabled

**OAGAPIError**
- Invalid request
- Resource not found
- Permission denied

### Debugging

```bash
# Enable verbose logging
python scripts/manage_oag_apps.py -c config.json -a list -v

# Check API health
python scripts/manage_oag_apps.py -c config.json -a health
```

---

## Best Practices

1. **Use dry-run first**: Always preview changes before applying
2. **Version control configs**: Keep OAG configs in Git
3. **Rotate credentials**: Regularly rotate API keys
4. **Use environment secrets**: Don't commit private keys
5. **Monitor deployments**: Check OAG logs after changes

---

## Related Documentation

- [OAG Deployment Guide](./OAG_DEPLOYMENT.md)
- [OAG Demo App](../examples/oag-demo-app/README.md)
- [Okta Access Gateway API](https://developer.okta.com/docs/api/openapi/oag/guides/overview/)
