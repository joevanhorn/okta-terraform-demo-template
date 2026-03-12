"""
SSF (Shared Signals Framework) Provider for Okta ITP Demo

Manages SSF security events provider registration and signal sending.
Sends Security Event Tokens (SETs) to Okta to trigger "Security events
provider reported risk" system log entries.

Usage as module:
    from itp.ssf_provider import SSFProvider

    provider = SSFProvider(org_name="myorg", base_url="okta.com",
                           api_token="...", issuer="https://my-issuer",
                           private_key_pem="...", key_id="my-key-id")
    result = provider.send_risk_signal("user@example.com", risk_level="HIGH")
"""

import json
import time
import uuid
import requests

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class SSFProvider:
    """Manages SSF security events provider registration and signal sending."""

    # Okta's SET event type for user risk changes
    RISK_EVENT_TYPE = "https://schemas.okta.com/secevent/okta/event-type/user-risk-change"

    def __init__(self, org_name: str, base_url: str, api_token: str,
                 issuer: str = None, private_key_pem: str = None,
                 key_id: str = None):
        self.org_name = org_name
        self.base_url = base_url
        self.okta_url = f"https://{org_name}.{base_url}"
        self.api_base = f"{self.okta_url}/api/v1"
        self.api_token = api_token
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # SSF-specific config (set after setup or loaded from SSM)
        self.issuer = issuer
        self.private_key_pem = private_key_pem
        self.key_id = key_id

    # --- Key Generation ---

    @staticmethod
    def generate_keypair():
        """Generate RSA 2048-bit key pair for JWT signing.

        Returns:
            tuple: (private_key_pem: str, public_jwks: dict, key_id: str)
        """
        key_id = f"ssf-demo-{uuid.uuid4().hex[:8]}"

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Export private key as PEM
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        # Build JWKS from public key
        public_key = private_key.public_key()
        public_numbers = public_key.public_numbers()

        def _int_to_base64url(n, length=None):
            """Convert integer to base64url-encoded bytes."""
            import base64
            byte_length = length or (n.bit_length() + 7) // 8
            n_bytes = n.to_bytes(byte_length, byteorder="big")
            return base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode("ascii")

        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": key_id,
                    "n": _int_to_base64url(public_numbers.n, 256),
                    "e": _int_to_base64url(public_numbers.e),
                }
            ]
        }

        return private_key_pem, jwks, key_id

    # --- Provider Registration ---

    def register_provider(self, name: str, issuer: str, jwks_url: str):
        """Register a security events provider with Okta.

        Args:
            name: Display name for the provider
            issuer: Issuer URI (must match 'iss' in SETs)
            jwks_url: Public URL to JWKS endpoint

        Returns:
            dict: Provider registration response from Okta
        """
        url = f"{self.api_base}/security-events-providers"
        payload = {
            "name": name,
            "type": "ssf",
            "settings": {
                "issuer": issuer,
                "jwks_url": jwks_url,
            },
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def list_providers(self):
        """List all registered security events providers."""
        url = f"{self.api_base}/security-events-providers"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def delete_provider(self, provider_id: str):
        """Delete a security events provider."""
        url = f"{self.api_base}/security-events-providers/{provider_id}"
        response = self.session.delete(url)
        response.raise_for_status()

    # --- SET (Security Event Token) Building ---

    def build_set(self, subject_email: str, risk_level: str = "HIGH",
                  reason: str = "Critical security activity detected"):
        """Build a Security Event Token (SET) payload.

        Uses the RFC 8417 SET format with events wrapper, plus Okta-required
        fields (event_timestamp, initiating_entity, reason_admin).

        Reference: https://help.okta.com/oie/en-us/content/topics/itp/configure-shared-signal-provider.htm

        Args:
            subject_email: Email of the user to set risk for
            risk_level: Risk level — HIGH or LOW
            reason: Human-readable reason for the risk change

        Returns:
            dict: SET payload (not yet signed)
        """
        now = int(time.time())
        previous_level = "low" if risk_level.upper() == "HIGH" else "high"

        payload = {
            "iss": self.issuer,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "aud": self.okta_url,
            "events": {
                self.RISK_EVENT_TYPE: {
                    "subject": {
                        "user": {
                            "format": "email",
                            "email": subject_email,
                        }
                    },
                    "event_timestamp": now,
                    "initiating_entity": "admin",
                    "reason_admin": {
                        "en": reason,
                    },
                    "current_level": risk_level.lower(),
                    "previous_level": previous_level,
                }
            },
        }
        return payload

    def sign_set(self, payload: dict) -> str:
        """Sign a SET payload as a JWT.

        Args:
            payload: SET payload dict

        Returns:
            str: Signed JWT string
        """
        headers = {
            "typ": "secevent+jwt",
            "kid": self.key_id,
        }
        return jwt.encode(
            payload,
            self.private_key_pem,
            algorithm="RS256",
            headers=headers,
        )

    # --- Signal Sending ---

    def send_signal(self, set_jwt: str):
        """Send a signed SET to Okta's security events endpoint.

        This endpoint is self-authenticating — the JWT signature is the
        authentication. No SSWS token needed.

        Args:
            set_jwt: Signed SET JWT string

        Returns:
            dict: {"status": "success"} or {"status": "error", "error": ...}
        """
        url = f"{self.okta_url}/security/api/v1/security-events"
        headers = {
            "Content-Type": "application/secevent+jwt",
            "Accept": "application/json",
        }

        response = requests.post(url, data=set_jwt, headers=headers)

        if response.status_code == 202 or response.status_code == 200:
            return {"status": "success", "http_code": response.status_code}

        # Parse error
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = error_json.get("errorSummary", error_detail)
        except Exception:
            pass

        return {
            "status": "error",
            "http_code": response.status_code,
            "error": error_detail,
        }

    def send_risk_signal(self, subject_email: str, risk_level: str = "HIGH"):
        """Build, sign, and send a user risk change signal.

        Convenience method combining build_set + sign_set + send_signal.

        Args:
            subject_email: User email
            risk_level: HIGH or LOW

        Returns:
            dict: Result with status and details
        """
        payload = self.build_set(subject_email, risk_level)
        set_jwt = self.sign_set(payload)
        result = self.send_signal(set_jwt)
        result["jti"] = payload["jti"]
        return result

    # --- One-Time Setup ---

    def setup(self, name: str, s3_bucket: str,
              s3_key_prefix: str = "ssf-demo",
              aws_region: str = "us-east-1",
              aws_profile: str = None,
              ssm_prefix: str = None):
        """Full one-time setup: generate keys, upload JWKS, register provider, store in SSM.

        Args:
            name: Provider display name
            s3_bucket: S3 bucket for JWKS hosting
            s3_key_prefix: S3 key prefix (default: ssf-demo)
            aws_region: AWS region for S3 and SSM
            aws_profile: AWS CLI profile name
            ssm_prefix: SSM parameter path prefix

        Returns:
            dict: Setup results including provider_id, issuer, jwks_url
        """
        import boto3

        session_kwargs = {"region_name": aws_region}
        if aws_profile:
            session_kwargs["profile_name"] = aws_profile
        boto_session = boto3.Session(**session_kwargs)

        # Step 1: Generate key pair
        print("\n  [1/4] Generating RSA key pair...")
        private_key_pem, jwks, key_id = self.generate_keypair()
        print(f"         Key ID: {key_id}")

        # Step 2: Upload JWKS to S3
        print(f"\n  [2/4] Uploading JWKS to s3://{s3_bucket}/{s3_key_prefix}/jwks.json...")
        s3_client = boto_session.client("s3")
        s3_key = f"{s3_key_prefix}/jwks.json"
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=json.dumps(jwks, indent=2),
            ContentType="application/json",
        )
        jwks_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
        print(f"         JWKS URL: {jwks_url}")

        # Step 3: Register provider with Okta
        issuer = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key_prefix}"
        print(f"\n  [3/4] Registering security events provider...")
        print(f"         Name: {name}")
        print(f"         Issuer: {issuer}")
        provider = self.register_provider(name, issuer, jwks_url)
        provider_id = provider.get("id")
        print(f"         Provider ID: {provider_id}")

        # Step 4: Store config in SSM
        print(f"\n  [4/4] Storing configuration in SSM...")
        ssm_client = boto_session.client("ssm")

        # Store private key
        ssm_client.put_parameter(
            Name=f"{ssm_prefix}/private-key",
            Description="SSF Demo - RSA private key for SET signing",
            Value=private_key_pem,
            Type="SecureString",
            Overwrite=True,
        )
        print(f"         Private key: {ssm_prefix}/private-key")

        # Store provider config
        config = {
            "issuer": issuer,
            "provider_id": provider_id,
            "jwks_url": jwks_url,
            "key_id": key_id,
            "provider_name": name,
        }
        ssm_client.put_parameter(
            Name=f"{ssm_prefix}/provider-config",
            Description="SSF Demo - Provider configuration",
            Value=json.dumps(config),
            Type="String",
            Overwrite=True,
        )
        print(f"         Config: {ssm_prefix}/provider-config")

        # Update instance state
        self.issuer = issuer
        self.private_key_pem = private_key_pem
        self.key_id = key_id

        return {
            "provider_id": provider_id,
            "issuer": issuer,
            "jwks_url": jwks_url,
            "key_id": key_id,
            "ssm_prefix": ssm_prefix,
        }


def get_ssf_config_from_ssm(ssm_prefix: str = None,
                             region: str = None,
                             profile: str = None):
    """Load SSF provider config and private key from SSM Parameter Store.

    Args:
        ssm_prefix: SSM parameter path prefix
        region: AWS region
        profile: AWS CLI profile name

    Returns:
        tuple: (config_dict, private_key_pem)
    """
    import boto3

    session_kwargs = {}
    if region:
        session_kwargs["region_name"] = region
    if profile:
        session_kwargs["profile_name"] = profile
    boto_session = boto3.Session(**session_kwargs)
    ssm = boto_session.client("ssm")

    # Get provider config
    config_resp = ssm.get_parameter(
        Name=f"{ssm_prefix}/provider-config",
    )
    config = json.loads(config_resp["Parameter"]["Value"])

    # Get private key
    key_resp = ssm.get_parameter(
        Name=f"{ssm_prefix}/private-key",
        WithDecryption=True,
    )
    private_key_pem = key_resp["Parameter"]["Value"]

    return config, private_key_pem
