"""
Okta Access Gateway API Client

Provides JWT-based authentication and REST API operations for OAG.
Requires OAG version 2025.10.0 or later.
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import requests
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class OAGClient:
    """
    Client for Okta Access Gateway API with JWT authentication.

    Usage:
        client = OAGClient(
            hostname="oag.example.com",
            client_id="your_client_id",
            private_key_path="/path/to/private_key.pem"
        )

        # Get all applications
        apps = client.get("/api/v2/apps")
    """

    # Available API scopes
    SCOPES = {
        'app_manage': 'okta.oag.app.manage',
        'app_read': 'okta.oag.app.read',
        'cert_read': 'okta.oag.cert.read',
        'idp_manage': 'okta.oag.idp.manage',
        'idp_read': 'okta.oag.idp.read',
    }

    def __init__(
        self,
        hostname: str,
        client_id: str,
        private_key_path: Optional[str] = None,
        private_key: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        verify_ssl: bool = True
    ):
        """
        Initialize OAG API client.

        Args:
            hostname: OAG hostname (e.g., "oag.example.com")
            client_id: Client ID from OAG Admin Console
            private_key_path: Path to private key PEM file
            private_key: Private key PEM string (alternative to path)
            scopes: List of scopes to request (defaults to all)
            verify_ssl: Verify SSL certificates (disable for self-signed)
        """
        self.hostname = hostname.rstrip('/')
        self.base_url = f"https://{self.hostname}"
        self.client_id = client_id
        self.verify_ssl = verify_ssl

        # Load private key
        if private_key_path:
            with open(os.path.expanduser(private_key_path), 'rb') as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
        elif private_key:
            self._private_key = serialization.load_pem_private_key(
                private_key.encode() if isinstance(private_key, str) else private_key,
                password=None,
                backend=default_backend()
            )
        else:
            raise ValueError("Either private_key_path or private_key must be provided")

        # Set scopes
        if scopes:
            self.scopes = scopes
        else:
            # Default to all scopes
            self.scopes = list(self.SCOPES.values())

        # Token management
        self._access_token = None
        self._token_expiry = 0

        # Session for connection pooling
        self._session = requests.Session()

    def _generate_jwt(self) -> str:
        """
        Generate a signed JWT for client credentials authentication.

        Returns:
            Signed JWT string
        """
        now = int(time.time())

        # JWT payload
        payload = {
            'iss': self.client_id,
            'sub': self.client_id,
            'aud': self.base_url,
            'exp': now + 300,  # 5 minutes
            'iat': now,
            'scope': ' '.join(self.scopes)
        }

        # Sign with RS256
        token = jwt.encode(
            payload,
            self._private_key,
            algorithm='RS256',
            headers={'typ': 'JWT', 'alg': 'RS256'}
        )

        return token

    def _get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get or refresh the access token.

        Args:
            force_refresh: Force token refresh even if not expired

        Returns:
            Access token string
        """
        # Check if current token is still valid
        if not force_refresh and self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        logger.debug("Requesting new access token")

        # Generate signed JWT
        client_assertion = self._generate_jwt()

        # Request access token
        token_url = f"{self.base_url}/api/v2/oauth/token"

        data = {
            'grant_type': 'client_credentials',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion': client_assertion,
            'scope': ' '.join(self.scopes)
        }

        response = self._session.post(
            token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            verify=self.verify_ssl
        )

        if response.status_code != 200:
            logger.error(f"Token request failed: {response.status_code} - {response.text}")
            raise OAGAuthenticationError(
                f"Failed to obtain access token: {response.status_code} - {response.text}"
            )

        token_data = response.json()
        self._access_token = token_data.get('access_token')

        # Calculate expiry (default to 1 hour if not specified)
        expires_in = token_data.get('expires_in', 3600)
        self._token_expiry = time.time() + expires_in

        logger.debug(f"Obtained access token, expires in {expires_in}s")

        return self._access_token

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_on_401: bool = True
    ) -> requests.Response:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/v2/apps")
            data: Request body data
            params: Query parameters
            retry_on_401: Retry with refreshed token on 401

        Returns:
            Response object
        """
        url = urljoin(self.base_url, endpoint)
        token = self._get_access_token()

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        response = self._session.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            verify=self.verify_ssl
        )

        # Handle token expiration
        if response.status_code == 401 and retry_on_401:
            logger.debug("Token expired, refreshing and retrying")
            self._get_access_token(force_refresh=True)
            return self._request(method, endpoint, data, params, retry_on_401=False)

        return response

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response data
        """
        response = self._request('GET', endpoint, params=params)
        response.raise_for_status()
        return response.json() if response.text else {}

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint
            data: Request body

        Returns:
            JSON response data
        """
        response = self._request('POST', endpoint, data=data)
        response.raise_for_status()
        return response.json() if response.text else {}

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint
            data: Request body

        Returns:
            JSON response data
        """
        response = self._request('PUT', endpoint, data=data)
        response.raise_for_status()
        return response.json() if response.text else {}

    def delete(self, endpoint: str) -> bool:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint

        Returns:
            True if successful
        """
        response = self._request('DELETE', endpoint)
        response.raise_for_status()
        return True

    def health_check(self) -> Dict[str, Any]:
        """
        Check OAG API health status.

        Returns:
            Health status information
        """
        try:
            # Try to get token to verify authentication
            self._get_access_token()
            return {
                'status': 'healthy',
                'hostname': self.hostname,
                'authenticated': True
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'hostname': self.hostname,
                'authenticated': False,
                'error': str(e)
            }

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'OAGClient':
        """
        Create client from configuration dictionary.

        Args:
            config: Configuration with hostname, client_id, private_key_path

        Returns:
            OAGClient instance
        """
        return cls(
            hostname=config['hostname'],
            client_id=config['client_id'],
            private_key_path=config.get('private_key_path'),
            private_key=config.get('private_key'),
            scopes=config.get('scopes'),
            verify_ssl=config.get('verify_ssl', True)
        )

    @classmethod
    def from_environment(cls) -> 'OAGClient':
        """
        Create client from environment variables.

        Environment variables:
            OAG_HOSTNAME: OAG hostname
            OAG_CLIENT_ID: Client ID
            OAG_PRIVATE_KEY_PATH: Path to private key
            OAG_PRIVATE_KEY: Private key content (alternative)
            OAG_VERIFY_SSL: Verify SSL (default: true)

        Returns:
            OAGClient instance
        """
        hostname = os.environ.get('OAG_HOSTNAME')
        client_id = os.environ.get('OAG_CLIENT_ID')
        private_key_path = os.environ.get('OAG_PRIVATE_KEY_PATH')
        private_key = os.environ.get('OAG_PRIVATE_KEY')
        verify_ssl = os.environ.get('OAG_VERIFY_SSL', 'true').lower() == 'true'

        if not hostname:
            raise ValueError("OAG_HOSTNAME environment variable is required")
        if not client_id:
            raise ValueError("OAG_CLIENT_ID environment variable is required")
        if not private_key_path and not private_key:
            raise ValueError("OAG_PRIVATE_KEY_PATH or OAG_PRIVATE_KEY environment variable is required")

        return cls(
            hostname=hostname,
            client_id=client_id,
            private_key_path=private_key_path,
            private_key=private_key,
            verify_ssl=verify_ssl
        )


class OAGAuthenticationError(Exception):
    """Raised when OAG authentication fails."""
    pass


class OAGAPIError(Exception):
    """Raised when OAG API returns an error."""

    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
