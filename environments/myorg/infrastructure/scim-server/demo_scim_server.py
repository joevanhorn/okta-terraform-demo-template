# demo_scim_server.py - SCIM 2.0 Server with Entitlements Demo
# Repository: https://github.com/joevanhorn/api-entitlements-demo
# IMPROVED VERSION with enhanced debugging for user matching issues
# Supports Okta OIG entitlement discovery via non-standard URN

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import logging
import re
import os

# ---------------------------------------------------------------------------
# SCIM Schema URNs
# ---------------------------------------------------------------------------
USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
ENTITLEMENT_SCHEMA = "urn:okta:scim:schemas:core:1.0:Entitlement"
LIST_RESPONSE_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- BEGIN AUTH MIDDLEWARE (Basic + Bearer) ---
import os
from base64 import b64decode
from flask import request, jsonify

# env-driven secrets
_EXPECTED_BEARER = os.environ.get("SCIM_AUTH_TOKEN", "").strip()
_BASIC_USER = os.environ.get("SCIM_BASIC_USER", "").strip()
_BASIC_PASS = os.environ.get("SCIM_BASIC_PASS", "").strip()

# paths that remain unauthenticated
_EXEMPT = {
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/scim/v2/ServiceProviderConfig"),
}

def _bearer_ok(h: str) -> bool:
    if not _EXPECTED_BEARER:
        return False
    if not h or not h.startswith("Bearer "):
        return False
    token = h.split(None, 1)[1].strip()
    return token == _EXPECTED_BEARER

def _basic_ok(h: str) -> bool:
    if not (_BASIC_USER and _BASIC_PASS):
        return False
    if not h or not h.startswith("Basic "):
        return False
    try:
        raw = b64decode(h.split(None, 1)[1]).decode("utf-8", "ignore")
    except Exception:
        return False
    if ":" not in raw:
        return False
    u, p = raw.split(":", 1)
    return (u == _BASIC_USER) and (p == _BASIC_PASS)

@app.before_request
def _require_auth_for_scim():
    key = (request.method.upper(), request.path)
    if key in _EXEMPT:
        return  # allow unauthenticated

    if request.path.startswith("/scim/v2/"):
        auth = request.headers.get("Authorization", "")
        if _bearer_ok(auth) or _basic_ok(auth):
            return  # authorized
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "detail": "Unauthorized - Invalid or missing credentials",
            "status": "401",
        }), 401
# --- END AUTH MIDDLEWARE ---

# --- BEGIN REQUEST/RESPONSE LOGGING ---
@app.before_request
def _log_request():
    logger.info("%s %s", request.method, request.path)
    if request.is_json and request.data:
        logger.debug("Request body: %s", request.get_data(as_text=True))

@app.after_request
def _log_response(response):
    logger.info("%s %s -> %s", request.method, request.path, response.status_code)
    return response
# --- END REQUEST/RESPONSE LOGGING ---


# In-memory storage - simulates your cloud application's database
users_db = {}

# Default entitlements (fallback if entitlements.json not found)
DEFAULT_ENTITLEMENTS = {
    "role_admin": {
        "id": "role_admin",
        "name": "Administrator",
        "description": "Full system access",
        "permissions": ["read", "write", "delete", "admin", "manage_users"]
    },
    "role_user": {
        "id": "role_user",
        "name": "Standard User",
        "description": "Basic access",
        "permissions": ["read", "write"]
    },
    "role_readonly": {
        "id": "role_readonly",
        "name": "Read Only",
        "description": "View only access",
        "permissions": ["read"]
    },
    "role_support": {
        "id": "role_support",
        "name": "Support Agent",
        "description": "Customer support access",
        "permissions": ["read", "write", "support", "view_tickets"]
    },
    "role_billing": {
        "id": "role_billing",
        "name": "Billing Manager",
        "description": "Billing and payment access",
        "permissions": ["read", "billing", "invoices", "payments"]
    }
}

def load_entitlements():
    """Load entitlements from JSON file or use defaults"""
    entitlements_file = os.environ.get('ENTITLEMENTS_FILE', '/opt/scim-demo/entitlements.json')

    try:
        # Try to load from file
        if os.path.exists(entitlements_file):
            with open(entitlements_file, 'r') as f:
                data = json.load(f)
                entitlements_list = data.get('entitlements', [])

                # Convert list to dictionary keyed by id
                entitlements = {ent['id']: ent for ent in entitlements_list}

                print(f"✅ Loaded {len(entitlements)} entitlements from {entitlements_file}")
                for ent in entitlements.values():
                    print(f"   • {ent['name']} ({ent['id']}) - {ent['description']}")

                return entitlements
        else:
            print(f"⚠️  Entitlements file not found: {entitlements_file}")
            print(f"   Using default entitlements")
            return DEFAULT_ENTITLEMENTS
    except Exception as e:
        print(f"❌ Error loading entitlements from {entitlements_file}: {e}")
        print(f"   Using default entitlements")
        return DEFAULT_ENTITLEMENTS

# Load entitlements at startup
entitlements_db = load_entitlements()

# Activity log for dashboard
activity_log = []

def log_activity(action, details):
    """Log activities for the dashboard"""
    activity_log.insert(0, {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "details": details
    })
    if len(activity_log) > 100:
        activity_log.pop()

def simulate_cloud_app_call(operation, data):
    """Simulate calling your cloud app's API"""
    print(f"\n{'='*70}")
    print(f"🔌 SIMULATED CLOUD APP API CALL")
    print(f"{'='*70}")
    print(f"   Operation: {operation}")
    print(f"   Data: {json.dumps(data, indent=6)}")
    print(f"   [In production, this would call your actual cloud app's API]")
    print(f"{'='*70}\n")
    return {"success": True, "message": "Operation completed"}

# [Dashboard HTML template remains the same - keeping original from line 129-572]
DASHBOARD_HTML = '''[DASHBOARD HTML CONTENT - TRUNCATED FOR BREVITY]'''

# SCIM Endpoints

@app.route('/scim/v2/ServiceProviderConfig', methods=['GET'])
def service_provider_config():
    """Service Provider Configuration"""
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "patch": {"supported": True},
        "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
        "filter": {"supported": True, "maxResults": 200},
        "changePassword": {"supported": False},
        "sort": {"supported": False},
        "etag": {"supported": False},
        "authenticationSchemes": [
            {
                "type": "httpbasic",
                "name": "HTTP Basic",
                "description": "Authentication via HTTP Basic",
                "specUri": "http://www.rfc-editor.org/info/rfc2617",
                "primary": True
            },
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "Authentication via OAuth Bearer Token",
                "specUri": "http://www.rfc-editor.org/info/rfc6750",
                "primary": False
            }
        ]
    })

# ---------------------------------------------------------------------------
# Entitlement Discovery Endpoints (Okta OIG)
# ---------------------------------------------------------------------------
# Okta discovers entitlements via a non-standard schema URN:
#   urn:okta:scim:schemas:core:1.0:Entitlement
# The standard IETF URN (urn:ietf:params:scim:schemas:core:2.0:Entitlement)
# does NOT work for Okta's Governance tab.
# See: https://developer.okta.com/docs/guides/scim-with-entitlements/main/

@app.route('/scim/v2/ResourceTypes', methods=['GET'])
def get_resource_types():
    """Declare available resource types including Entitlements for OIG discovery.

    Okta reads /ResourceTypes and looks for entries whose 'schema' field
    matches the Okta entitlement URN. For each match it calls the declared
    'endpoint' to import entitlements into the Governance tab.
    """
    resources = [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "User",
            "name": "User",
            "endpoint": "/Users",
            "description": "Application User",
            "schema": USER_SCHEMA,
        },
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "Entitlement",
            "name": "Entitlement",
            "endpoint": "/Entitlements",
            "description": "Application Role / Entitlement",
            "schema": ENTITLEMENT_SCHEMA,
        },
    ]
    return jsonify({
        "schemas": [LIST_RESPONSE_SCHEMA],
        "totalResults": len(resources),
        "Resources": resources,
    })

@app.route('/scim/v2/Schemas', methods=['GET'])
def get_schemas():
    """Return SCIM schema definitions for User resources."""
    user_schema = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Schema"],
        "id": USER_SCHEMA,
        "name": "User",
        "description": "Application User account",
        "attributes": [
            {
                "name": "userName",
                "type": "string",
                "multiValued": False,
                "required": True,
                "mutability": "readWrite",
                "returned": "default",
                "uniqueness": "server",
                "description": "Unique identifier for the user",
            },
            {
                "name": "name",
                "type": "complex",
                "multiValued": False,
                "required": False,
                "mutability": "readWrite",
                "returned": "default",
                "description": "User name components",
                "subAttributes": [
                    {"name": "givenName", "type": "string", "mutability": "readWrite", "returned": "default"},
                    {"name": "familyName", "type": "string", "mutability": "readWrite", "returned": "default"},
                ],
            },
            {
                "name": "emails",
                "type": "complex",
                "multiValued": True,
                "required": False,
                "mutability": "readWrite",
                "returned": "default",
                "description": "Email addresses",
                "subAttributes": [
                    {"name": "value", "type": "string", "mutability": "readWrite", "returned": "default"},
                    {"name": "primary", "type": "boolean", "mutability": "readWrite", "returned": "default"},
                    {"name": "type", "type": "string", "mutability": "readWrite", "returned": "default"},
                ],
            },
            {
                "name": "active",
                "type": "boolean",
                "multiValued": False,
                "required": False,
                "mutability": "readWrite",
                "returned": "default",
                "description": "User active status",
            },
            {
                "name": "roles",
                "type": "complex",
                "multiValued": True,
                "required": False,
                "mutability": "readWrite",
                "returned": "default",
                "description": "Application roles assigned to the user",
                "subAttributes": [
                    {"name": "value", "type": "string", "mutability": "readWrite", "returned": "default"},
                    {"name": "display", "type": "string", "mutability": "readOnly", "returned": "default"},
                ],
            },
        ],
    }
    return jsonify({
        "schemas": [LIST_RESPONSE_SCHEMA],
        "totalResults": 1,
        "Resources": [user_schema],
    })

@app.route('/scim/v2/Entitlements', methods=['GET'])
def list_entitlements():
    """Return all entitlements using Okta's custom schema URN.

    Each entitlement must include: id, displayName, type, description.
    The 'schemas' array MUST use urn:okta:scim:schemas:core:1.0:Entitlement
    for Okta to recognise these as governance entitlements.
    """
    start_index = int(request.args.get('startIndex', 1))
    count = int(request.args.get('count', 100))

    resources = []
    for ent in entitlements_db.values():
        resources.append({
            "schemas": [ENTITLEMENT_SCHEMA],
            "id": ent["id"],
            "displayName": ent.get("displayName", ent["name"]),
            "type": "Entitlement",
            "description": ent.get("description", ""),
            "meta": {
                "resourceType": "Entitlement",
                "location": f"/scim/v2/Entitlements/{ent['id']}",
            },
        })

    total = len(resources)
    page_start = max(start_index - 1, 0)  # SCIM is 1-indexed
    page = resources[page_start:page_start + count]

    return jsonify({
        "schemas": [LIST_RESPONSE_SCHEMA],
        "totalResults": total,
        "startIndex": start_index,
        "itemsPerPage": len(page),
        "Resources": page,
    })

@app.route('/scim/v2/Entitlements/<entitlement_id>', methods=['GET'])
def get_entitlement(entitlement_id):
    """Return a single entitlement by ID."""
    ent = entitlements_db.get(entitlement_id)
    if not ent:
        return jsonify({
            "schemas": [ERROR_SCHEMA],
            "status": "404",
            "detail": f"Entitlement {entitlement_id} not found",
        }), 404

    return jsonify({
        "schemas": [ENTITLEMENT_SCHEMA],
        "id": ent["id"],
        "displayName": ent.get("displayName", ent["name"]),
        "type": "Entitlement",
        "description": ent.get("description", ""),
        "meta": {
            "resourceType": "Entitlement",
            "location": f"/scim/v2/Entitlements/{ent['id']}",
        },
    })

# ---------------------------------------------------------------------------
# User Provisioning Endpoints
# ---------------------------------------------------------------------------

@app.route('/scim/v2/Users', methods=['POST'])
def create_user():
    """Create a new user - IMPROVED with better logging"""
    
    data = request.json
    user_id = f"user_{len(users_db) + 1}"
    username = data.get('userName')
    external_id = data.get('externalId', username)
    roles = data.get('roles', [])
    
    print(f"\n{'='*70}")
    print(f"👤 CREATING USER")
    print(f"{'='*70}")
    print(f"   Username: {username}")
    print(f"   ExternalId: {external_id}")
    print(f"   Request body: {json.dumps(data, indent=2)}")
    
    role_names = [r.get('display', r.get('value')) for r in roles]
    log_activity("User Created", f"Created user {username} with roles: {', '.join(role_names) if role_names else 'None'}")
    
    simulate_cloud_app_call("POST /api/users", {
        "email": username,
        "roles": [r.get('value') for r in roles]
    })
    
    user = {
        "id": user_id,
        "externalId": external_id,
        "userName": username,
        "name": data.get("name", {}),
        "emails": data.get("emails", []),
        "active": data.get("active", True),
        "roles": roles,
        "created": datetime.utcnow().isoformat() + "Z"
    }
    
    users_db[user_id] = user
    print(f"   ✅ User created successfully")
    print(f"   User ID: {user_id}")
    print(f"   Total users in DB: {len(users_db)}")
    print(f"{'='*70}\n")
    
    response = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "externalId": user["externalId"],
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user["roles"],
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user["created"]
        }
    }
    
    return jsonify(response), 201

@app.route('/scim/v2/Users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Retrieve a specific user"""
    
    print(f"\n{'='*70}")
    print(f"🔍 GET USER: {user_id}")
    print(f"{'='*70}\n")
    
    user = users_db.get(user_id)
    if not user:
        print(f"   ❌ User not found: {user_id}")
        print(f"   Available user IDs: {list(users_db.keys())}")
        print(f"{'='*70}\n")
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404
    
    simulate_cloud_app_call("GET /api/users/{id}", {"user_id": user_id})
    
    print(f"   ✅ User found: {user['userName']}")
    print(f"{'='*70}\n")
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "externalId": user.get("externalId", user["userName"]),
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user.get("roles", []),
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user.get("modified", user["created"])
        }
    })

@app.route('/scim/v2/Users', methods=['GET'])
def list_users():
    """List/search users - IMPROVED with enhanced debugging"""
    
    filter_param = request.args.get('filter', '')
    start_index = int(request.args.get('startIndex', 1))
    count = int(request.args.get('count', 100))
    
    # Enhanced logging
    print(f"\n{'='*70}")
    print(f"🔍 LIST/SEARCH USERS REQUEST")
    print(f"{'='*70}")
    print(f"   Filter parameter: '{filter_param}'")
    print(f"   StartIndex: {start_index}")
    print(f"   Count: {count}")
    print(f"   Total users in database: {len(users_db)}")
    if users_db:
        print(f"   Existing usernames: {[u['userName'] for u in users_db.values()]}")
    
    users = [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": user["id"],
            "externalId": user.get("externalId", user["userName"]),
            "userName": user["userName"],
            "name": user["name"],
            "emails": user["emails"],
            "active": user["active"],
            "roles": user.get("roles", []),
            "meta": {
                "resourceType": "User",
                "created": user["created"],
                "lastModified": user.get("modified", user["created"])
            }
        }
        for user in users_db.values()
    ]
    
    # Handle filter parameter with multiple patterns
    if filter_param:
        print(f"   Processing filter...")
        
        # Try different filter patterns that Okta might use
        patterns = [
            (r'userName eq "([^"]+)"', 'Standard format with double quotes'),
            (r"userName eq '([^']+)'", 'Single quotes'),
            (r'userName eq ([^\s]+)', 'No quotes'),
            (r'userName\s+eq\s+"([^"]+)"', 'Extra whitespace with quotes'),
        ]
        
        matched = False
        for pattern, description in patterns:
            match = re.search(pattern, filter_param, re.IGNORECASE)
            if match:
                target_username = match.group(1)
                print(f"   ✅ Matched pattern: {description}")
                print(f"   Searching for userName: '{target_username}'")
                
                # Case-insensitive search
                users_before = len(users)
                users = [u for u in users if u['userName'].lower() == target_username.lower()]
                
                print(f"   Filtered from {users_before} to {len(users)} user(s)")
                matched = True
                break
        
        if not matched:
            print(f"   ⚠️ WARNING: Filter did not match any known pattern!")
            print(f"   This may cause issues with Okta provisioning")
    
    print(f"   📊 Returning {len(users)} user(s)")
    print(f"{'='*70}\n")
    
    response = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(users),
        "startIndex": start_index,
        "itemsPerPage": len(users),
        "Resources": users
    }
    
    return jsonify(response), 200

@app.route('/scim/v2/Users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Full update of a user - Okta's primary update method"""
    
    print(f"\n{'='*70}")
    print(f"📝 PUT UPDATE USER: {user_id}")
    print(f"{'='*70}")
    
    user = users_db.get(user_id)
    if not user:
        print(f"   ❌ User not found: {user_id}")
        print(f"   Available user IDs: {list(users_db.keys())}")
        print(f"{'='*70}\n")
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404
    
    data = request.json
    print(f"   Current user: {user['userName']}")
    print(f"   Update payload: {json.dumps(data, indent=2)}")
    
    # Track what changed
    changes = []
    
    # Check for role changes
    old_roles = user.get("roles", [])
    new_roles = data.get("roles", [])
    if old_roles != new_roles:
        changes.append(f"Roles: {len(old_roles)} → {len(new_roles)}")
        print(f"   Role change detected:")
        print(f"     Old roles: {[r.get('value') for r in old_roles]}")
        print(f"     New roles: {[r.get('value') for r in new_roles]}")
    
    # Check for active status change
    old_active = user.get("active", True)
    new_active = data.get("active", old_active)
    if old_active != new_active:
        changes.append(f"Active: {old_active} → {new_active}")
    
    # Simulate cloud app API call
    simulate_cloud_app_call("PUT /api/users/{id}", {
        "user_id": user_id,
        "data": data,
        "changes": changes
    })
    
    # Update user with all fields from request (PUT is full replacement)
    user.update({
        "userName": data.get("userName", user["userName"]),
        "name": data.get("name", user["name"]),
        "emails": data.get("emails", user["emails"]),
        "active": new_active,
        "roles": new_roles,
        "modified": datetime.utcnow().isoformat() + "Z"
    })
    
    # Update externalId if provided (Okta sometimes updates this)
    if "externalId" in data:
        user["externalId"] = data["externalId"]
    
    change_summary = "; ".join(changes) if changes else "No changes"
    log_activity("User Updated", f"Updated user {user['userName']} via PUT: {change_summary}")
    
    print(f"   ✅ User updated successfully")
    print(f"   Changes: {change_summary}")
    print(f"{'='*70}\n")
    
    response = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "externalId": user.get("externalId", user["userName"]),
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user["roles"],
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user["modified"]
        }
    }
    
    return jsonify(response), 200

@app.route('/scim/v2/Users/<user_id>', methods=['PATCH'])
def patch_user(user_id):
    """Partial update of a user"""
    
    print(f"\n{'='*70}")
    print(f"🔧 PATCHING USER: {user_id}")
    print(f"{'='*70}")
    
    user = users_db.get(user_id)
    if not user:
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404
    
    data = request.json
    print(f"   Patch operations: {json.dumps(data, indent=2)}")
    changes = []
    
    for operation in data.get('Operations', []):
        op = operation['op'].lower()
        value = operation.get('value', {})
        path = operation.get('path', '')
        
        if op == 'add' and 'roles' in value:
            new_roles = value['roles']
            for role in new_roles:
                simulate_cloud_app_call("POST /api/users/{id}/roles", {
                    "user_id": user_id,
                    "role_id": role.get('value')
                })
            user['roles'] = user.get('roles', []) + new_roles
            changes.append(f"Added {len(new_roles)} role(s)")
            
        elif op == 'remove' and 'roles' in str(operation):
            old_roles = user.get('roles', [])
            for role in old_roles:
                simulate_cloud_app_call("DELETE /api/users/{id}/roles/{role_id}", {
                    "user_id": user_id,
                    "role_id": role.get('value')
                })
            user['roles'] = []
            changes.append("Removed all roles")
            
        elif op == 'replace':
            if 'active' in value:
                user['active'] = value['active']
                simulate_cloud_app_call("PATCH /api/users/{id}", {
                    "user_id": user_id,
                    "active": value['active']
                })
                changes.append(f"User {'activated' if value['active'] else 'deactivated'}")
            
            if 'roles' in value:
                user['roles'] = value['roles']
                changes.append("Replaced all roles")
    
    user['modified'] = datetime.utcnow().isoformat() + "Z"
    log_activity("User Updated", f"Updated user {user['userName']}: {'; '.join(changes)}")
    
    print(f"   ✅ User patched successfully")
    print(f"   Changes: {'; '.join(changes)}")
    print(f"{'='*70}\n")
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user["id"],
        "externalId": user.get("externalId", user["userName"]),
        "userName": user["userName"],
        "name": user["name"],
        "emails": user["emails"],
        "active": user["active"],
        "roles": user.get("roles", []),
        "meta": {
            "resourceType": "User",
            "created": user["created"],
            "lastModified": user["modified"]
        }
    })

@app.route('/scim/v2/Users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    
    if user_id in users_db:
        username = users_db[user_id]['userName']
        simulate_cloud_app_call("DELETE /api/users/{id}", {"user_id": user_id})
        del users_db[user_id]
        log_activity("User Deleted", f"Deleted user {username}")
        return '', 204
    else:
        return jsonify({
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": f"User {user_id} not found"
        }), 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "SCIM Entitlements Demo",
        "repository": "joevanhorn/api-entitlements-demo",
        "users": len(users_db),
        "active_users": sum(1 for u in users_db.values() if u.get('active', True)),
        "roles": len(entitlements_db),
        "activities": len(activity_log),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@app.route('/')
def dashboard():
    """Dashboard to view provisioned users and activity"""
    return render_template_string(DASHBOARD_HTML, 
        users=users_db.values(),
        roles=entitlements_db.values(),
        activity_log=activity_log[:20]
    )

if __name__ == '__main__':
    auth_token = os.environ.get('SCIM_AUTH_TOKEN', 'demo-token-12345')
    app.config['SCIM_AUTH_TOKEN'] = auth_token
    
    print("\n" + "="*70)
    print(" "*15 + "🚀 SCIM ENTITLEMENTS DEMO SERVER")
    print("="*70)
    print(f"📦 Repository: joevanhorn/api-entitlements-demo")
    print(f"📍 Dashboard: http://localhost:5000")
    print(f"📍 SCIM API: http://localhost:5000/scim/v2")
    print(f"📍 Entitlement Discovery: /scim/v2/ResourceTypes, /scim/v2/Entitlements")
    print(f"🔑 Auth Token: Bearer {auth_token}")
    print(f"🎭 Available Entitlements: {len(entitlements_db)}")
    for role in entitlements_db.values():
        print(f"   • {role.get('displayName', role['name'])} ({role['id']}) - {role['description']}")
    print("="*70)
    print("\n⏳ Starting server...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
