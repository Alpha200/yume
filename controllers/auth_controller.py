from msgspec import Struct

from litestar import Controller, get

from services.auth import oidc_config


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
            from services.auth import initialize_oidc
            from components.logging_manager import logging_manager
            try:
                logging_manager.log("OIDC endpoints not initialized, discovering now...")
                await initialize_oidc()
                logging_manager.log(f"OIDC discovery completed. Authorization endpoint: {oidc_config.authorization_endpoint}")
            except Exception as e:
                logging_manager.log(f"Failed to discover OIDC endpoints: {str(e)}", level="ERROR")
                raise
        
        return AuthConfigResponse(
            authorization_endpoint=oidc_config.authorization_endpoint or "",
            token_endpoint=oidc_config.token_endpoint or "",
            end_session_endpoint=oidc_config.end_session_endpoint or "",
            jwks_uri=oidc_config.jwks_uri or "",
            client_id=oidc_config.client_id or "",
            issuer=oidc_config.issuer or ""
        )
