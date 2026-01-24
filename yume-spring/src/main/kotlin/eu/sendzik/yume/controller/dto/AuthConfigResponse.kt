package eu.sendzik.yume.controller.dto

data class AuthConfigResponse(
    val authorizationEndpoint: String,
    val tokenEndpoint: String,
    val endSessionEndpoint: String,
    val jwksUri: String,
    val clientId: String,
    val issuer: String
)