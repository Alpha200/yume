import logging
from msgspec import Struct

from litestar import Controller, get

from services.auth import oidc_config, initialize_oidc

logger = logging.getLogger(__name__)


class AuthConfigResponse(Struct):
    """OIDC configuration for frontend OAuth flow"""
    authorization_endpoint: str
    token_endpoint: str
    end_session_endpoint: str
    jwks_uri: str
    client_id: str
    issuer: str


class AuthController(Controller):
    """Provides OIDC configuration to frontend for public OAuth client flow"""
    path = "/auth"

    @get("/config")
    async def get_auth_config(self) -> AuthConfigResponse:
        """Return OIDC endpoints and client ID for frontend to handle OAuth flow"""
        # Ensure endpoints are discovered
        if not oidc_config.authorization_endpoint:
            try:
                logger.info("OIDC endpoints not initialized, discovering now...")
                await initialize_oidc()
                logger.info(f"OIDC discovery completed. Authorization endpoint: {oidc_config.authorization_endpoint}")
            except Exception as e:
                logger.error(f"Failed to discover OIDC endpoints: {str(e)}")
                raise
        
        return AuthConfigResponse(
            authorization_endpoint=oidc_config.authorization_endpoint or "",
            token_endpoint=oidc_config.token_endpoint or "",
            end_session_endpoint=oidc_config.end_session_endpoint or "",
            jwks_uri=oidc_config.jwks_uri or "",
            client_id=oidc_config.client_id or "",
            issuer=oidc_config.issuer or ""
        )
