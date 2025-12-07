import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

import httpx
import jwt
from litestar import Request
from litestar.connection import ASGIConnection
from litestar.middleware import AbstractMiddleware
from litestar.types import ASGIApp, Scope, Receive, Send
from litestar.exceptions import NotAuthorizedException


class OIDCConfig:
    """OpenID Connect configuration with automatic discovery"""

    def __init__(self):
        self.client_id = os.getenv("OIDC_CLIENT_ID")
        well_known_url = os.getenv("OIDC_WELL_KNOWN_URL")
        
        # Validate required settings
        if not self.client_id:
            raise ValueError("OIDC_CLIENT_ID environment variable is required")
        if not well_known_url:
            raise ValueError("OIDC_WELL_KNOWN_URL environment variable is required")
        
        # Auto-append .well-known/openid-configuration if not present
        if not well_known_url.endswith("/.well-known/openid-configuration"):
            if well_known_url.endswith("/"):
                self.well_known_url = f"{well_known_url}.well-known/openid-configuration"
            else:
                self.well_known_url = f"{well_known_url}/.well-known/openid-configuration"
        else:
            self.well_known_url = well_known_url
        
        # These will be populated from well-known endpoint
        self.authorization_endpoint: Optional[str] = None
        self.token_endpoint: Optional[str] = None
        self.userinfo_endpoint: Optional[str] = None
        self.end_session_endpoint: Optional[str] = None
        self.jwks_uri: Optional[str] = None
        self.issuer: Optional[str] = None

    async def discover_endpoints(self):
        """Fetch OIDC configuration from well-known endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.well_known_url)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch OIDC discovery document: {response.text}")
            
            config = response.json()
            self.authorization_endpoint = config.get("authorization_endpoint")
            self.token_endpoint = config.get("token_endpoint")
            self.userinfo_endpoint = config.get("userinfo_endpoint")
            self.end_session_endpoint = config.get("end_session_endpoint")
            self.jwks_uri = config.get("jwks_uri")
            self.issuer = config.get("issuer")


oidc_config = OIDCConfig()


class OIDCClient:
    """OpenID Connect client for token validation only"""

    def __init__(self, config: OIDCConfig):
        self.config = config
        self.http_client = httpx.AsyncClient()
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_time: Optional[datetime] = None

    async def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS (JSON Web Key Set) from Keycloak with caching"""
        # Cache JWKS for 1 hour
        if self._jwks_cache and self._jwks_cache_time:
            if datetime.now() - self._jwks_cache_time < timedelta(hours=1):
                return self._jwks_cache

        response = await self.http_client.get(self.config.jwks_uri)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch JWKS: {response.text}")

        self._jwks_cache = response.json()
        self._jwks_cache_time = datetime.now()
        return self._jwks_cache

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token using Keycloak's public keys"""
        jwks = await self.get_jwks()
        
        # Get the key ID from the token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        # Find the matching public key
        public_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            raise Exception("Public key not found in JWKS")
        
        # Verify and decode the token
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.config.client_id,
                issuer=self.config.issuer,
                options={"verify_exp": True, "verify_aud": True, "verify_iss": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid token: {str(e)}")

    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()


oidc_client = OIDCClient(oidc_config)


# Authentication middleware that validates Bearer tokens with Keycloak
class AuthMiddleware(AbstractMiddleware):
    """
    Middleware that validates JWT Bearer tokens with Keycloak.
    Skips authentication for public endpoints.
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {"/health", "/auth/config", "/schema", "/"}
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and validate authentication"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope)
        
        # Check if path is public or static asset
        if (request.url.path in self.PUBLIC_PATHS or 
            request.url.path.startswith("/assets/")):
            await self.app(scope, receive, send)
            return
        
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise NotAuthorizedException("Missing or invalid Authorization header")
        
        token = auth_header.replace("Bearer ", "")
        
        try:
            # Verify token with Keycloak's public keys
            payload = await oidc_client.verify_token(token)
            
            # Store user info in scope state for use in handlers
            if "state" not in scope:
                scope["state"] = {}
            scope["state"]["user"] = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "preferred_username": payload.get("preferred_username"),
                "name": payload.get("name"),
            }
        except Exception as e:
            raise NotAuthorizedException(f"Invalid token: {str(e)}")
        
        await self.app(scope, receive, send)


async def initialize_oidc():
    """Initialize OIDC configuration by discovering endpoints"""
    await oidc_config.discover_endpoints()
