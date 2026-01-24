package eu.sendzik.yume.controller

import eu.sendzik.yume.controller.dto.AuthConfigResponse
import org.springframework.beans.factory.annotation.Value
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

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
