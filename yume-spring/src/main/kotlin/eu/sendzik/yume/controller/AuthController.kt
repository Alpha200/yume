package eu.sendzik.yume.controller

import org.springframework.beans.factory.annotation.Value
import org.springframework.security.oauth2.core.oidc.OidcIdToken
import org.springframework.security.oauth2.core.oidc.user.OidcUser
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

data class AuthConfigResponse(
    val authorizationEndpoint: String,
    val tokenEndpoint: String,
    val endSessionEndpoint: String,
    val jwksUri: String,
    val clientId: String,
    val issuer: String
)

@RestController
@RequestMapping("auth")
class AuthController(
    @Value("\${spring.security.oauth2.resourceserver.jwt.issuer-uri}")
    private val issuerUri: String,
    @Value("\${yume.oauth2.client-id}")
    private val clientId: String,
) {
    @GetMapping("config")
    fun getAuthConfig(): AuthConfigResponse {
        return AuthConfigResponse(
            authorizationEndpoint = "$issuerUri/protocol/openid-connect/auth",
            tokenEndpoint = "$issuerUri/protocol/openid-connect/token",
            endSessionEndpoint = "$issuerUri/protocol/openid-connect/logout",
            jwksUri = "$issuerUri/protocol/openid-connect/certs",
            clientId = clientId,
            issuer = issuerUri
        )
    }
}
