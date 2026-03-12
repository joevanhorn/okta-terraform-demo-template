# SCIM Entitlement Discovery for Okta Identity Governance

This guide explains how to surface application entitlements in Okta's **Governance tab** using a SCIM 2.0 server. It covers the non-standard schema URN that Okta requires, the discovery flow, required response fields, and common gotchas.

## The Problem: Standard SCIM URN Doesn't Work

The IETF-standard SCIM entitlement schema URN is:

```
urn:ietf:params:scim:schemas:core:2.0:Entitlement
```

**This does NOT work with Okta.** Okta Identity Governance uses a custom, non-standard URN:

```
urn:okta:scim:schemas:core:1.0:Entitlement
```

If you use the standard URN, Okta will import users and groups but will **never discover your entitlements** — the Governance tab will remain empty.

**Reference:** [Okta SCIM with Entitlements Guide](https://developer.okta.com/docs/guides/scim-with-entitlements/main/)

## How Okta Discovers Entitlements

Okta follows a two-step discovery process:

### Step 1: Read `/ResourceTypes`

Okta calls `GET /scim/v2/ResourceTypes` and scans each entry's `schema` field. It looks for entries whose schema matches `urn:okta:scim:schemas:core:1.0:Entitlement`.

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 2,
  "Resources": [
    {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
      "id": "User",
      "name": "User",
      "endpoint": "/Users",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
    },
    {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
      "id": "Entitlement",
      "name": "Entitlement",
      "endpoint": "/Entitlements",
      "description": "Application Role / Entitlement",
      "schema": "urn:okta:scim:schemas:core:1.0:Entitlement"
    }
  ]
}
```

### Step 2: Fetch Entitlements from Declared Endpoint

For each matching ResourceType, Okta calls the declared `endpoint` (e.g., `GET /scim/v2/Entitlements`). Each entitlement resource must include these fields:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier for the entitlement |
| `displayName` | Yes | Human-readable name shown in Governance UI |
| `type` | Yes | Category/type (matches the ResourceType `id`) |
| `description` | No | Description shown in Governance UI |
| `schemas` | Yes | Must be `["urn:okta:scim:schemas:core:1.0:Entitlement"]` |

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 5,
  "startIndex": 1,
  "itemsPerPage": 5,
  "Resources": [
    {
      "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
      "id": "role_admin",
      "displayName": "Administrator",
      "type": "Entitlement",
      "description": "Full system access",
      "meta": {
        "resourceType": "Entitlement",
        "location": "/scim/v2/Entitlements/role_admin"
      }
    }
  ]
}
```

## Bearer Token Prefix Quirk

When using Okta's **SCIM 2.0 Test App (Header Auth)** (`scim2headerauth`), Okta sends the bearer token **without** the `Bearer ` prefix in the `Authorization` header.

**Fix:** When configuring the token in Okta, enter it **with** the `Bearer ` prefix:

```
Bearer your-actual-token-here
```

Without the prefix, the SCIM server receives just the raw token value, and standard `Authorization: Bearer <token>` parsing fails with a 401.

This applies to both the OPP Agent and direct SCIM connections from Okta.

## User Profile Requirements

For entitlement assignment to work, Okta expects user resources to include:

- `userName` (unique identifier)
- `name` with `givenName` and `familyName`
- `emails` with at least one entry
- `externalId` (Okta sets this to the Okta user ID)
- `active` boolean

## The "No Schema Refresh" Gotcha

**Okta imports the entitlement schema once — when the SCIM app is first created.** If you:

1. Deploy the SCIM server without entitlement endpoints
2. Add entitlement endpoints later
3. Try to "refresh" the schema in Okta

...Okta will **not** pick up the new entitlements. There is no "re-import schema" button.

**Workaround:** Delete and recreate the Okta SCIM application. On creation, Okta will call `/ResourceTypes` and discover the entitlements.

## Implementation Checklist

- [ ] Add `GET /scim/v2/ResourceTypes` endpoint returning an Entitlement entry with `schema: "urn:okta:scim:schemas:core:1.0:Entitlement"`
- [ ] Add `GET /scim/v2/Entitlements` endpoint returning all entitlements with the Okta URN
- [ ] Add `GET /scim/v2/Entitlements/<id>` endpoint for single lookups
- [ ] Each entitlement includes `id`, `displayName`, `type`, `description`
- [ ] Each entitlement's `schemas` array uses `urn:okta:scim:schemas:core:1.0:Entitlement`
- [ ] Bearer token configured with `Bearer ` prefix in Okta
- [ ] SCIM app created **after** entitlement endpoints are deployed (or recreated)

## Testing Locally

```bash
# Start the server
export SCIM_AUTH_TOKEN="test-token"
python3 demo_scim_server.py

# Verify ResourceTypes declares entitlements
curl -s http://localhost:5000/scim/v2/ResourceTypes \
  -H "Authorization: Bearer test-token" | python3 -m json.tool

# Verify Entitlements endpoint returns Okta URN
curl -s http://localhost:5000/scim/v2/Entitlements \
  -H "Authorization: Bearer test-token" | python3 -m json.tool

# Verify single entitlement lookup
curl -s http://localhost:5000/scim/v2/Entitlements/role_admin \
  -H "Authorization: Bearer test-token" | python3 -m json.tool
```

## Reference

- [Okta SCIM with Entitlements](https://developer.okta.com/docs/guides/scim-with-entitlements/main/)
- [SCIM 2.0 RFC 7644](https://datatracker.ietf.org/doc/html/rfc7644)
- [Okta Identity Governance](https://help.okta.com/oie/en-us/content/topics/identity-governance/iga-main.htm)
