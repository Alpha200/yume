package eu.sendzik.yume.service.strava

import eu.sendzik.yume.client.StravaClient
import eu.sendzik.yume.repository.strava.StravaCredentialsRepository
import eu.sendzik.yume.service.strava.model.StravaConnectionStatus
import eu.sendzik.yume.service.strava.model.StravaCredentials
import eu.sendzik.yume.service.strava.model.toCredentials
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class StravaAuthService(
    private val stravaClient: StravaClient,
    private val credentialsRepository: StravaCredentialsRepository,
    private val logger: KLogger,
    @param:Value("\${yume.strava.client-id:}")
    private val clientId: String,
    @param:Value("\${yume.strava.client-secret:}")
    private val clientSecret: String,
    @param:Value("\${yume.strava.oauth-redirect-url:http://localhost:8079/api/strava/oauth/callback}")
    private val oauthRedirectUrl: String,
) {
    fun exchangeAuthorizationCode(code: String): Result<StravaCredentials> {
        return runCatching {
            logger.info { "Exchanging authorization code for access token" }
            val tokenResponse = stravaClient.exchangeAuthorizationCode(
                clientId = clientId,
                clientSecret = clientSecret,
                code = code,
            )
            val credentials = tokenResponse.toCredentials()
            credentialsRepository.save(credentials)
            logger.info { "Successfully stored Strava credentials for athlete ${credentials.athleteId}" }
            credentials
        }.onFailure { e ->
            logger.error(e) { "Failed to exchange authorization code: ${e.message}" }
        }
    }

    fun getValidCredentials(): Result<StravaCredentials> {
        return runCatching {
            credentialsRepository.findById("default").orElse(null)
                ?: throw IllegalStateException("No Strava credentials found")
        }.mapCatching { credentials ->
            if (credentials.isTokenExpired()) {
                logger.info { "Access token expired, refreshing..." }
                refreshAccessToken(credentials.refreshToken).getOrThrow()
            } else {
                credentials
            }
        }.onFailure { e ->
            logger.error(e) { "Failed to get valid credentials: ${e.message}" }
        }
    }

    fun refreshAccessToken(refreshToken: String): Result<StravaCredentials> {
        return runCatching {
            logger.info { "Refreshing Strava access token" }

            // Get existing credentials to preserve athleteId and athleteName
            val existingCredentials = credentialsRepository.findById("default").orElse(null)

            val tokenResponse = stravaClient.refreshAccessToken(
                clientId = clientId,
                clientSecret = clientSecret,
                refreshToken = refreshToken,
            )
            val credentials = tokenResponse.toCredentials(
                existingAthleteId = existingCredentials?.athleteId,
                existingAthleteName = existingCredentials?.athleteName
            )
            credentialsRepository.save(credentials)
            logger.info { "Successfully refreshed access token for athlete ${credentials.athleteId}" }
            credentials
        }.onFailure { e ->
            logger.error(e) { "Failed to refresh access token: ${e.message}" }
        }
    }

    fun hasValidCredentials(): Boolean {
        return credentialsRepository.findById("default").isPresent
    }

    fun getConnectionStatus(): Result<StravaConnectionStatus> {
        return runCatching {
            val credentials = credentialsRepository.findById("default").orElse(null)
            if (credentials != null) {
                StravaConnectionStatus(
                    connected = true,
                    athleteId = credentials.athleteId,
                    athleteName = credentials.athleteName,
                    tokenExpired = credentials.isTokenExpired()
                )
            } else {
                StravaConnectionStatus(connected = false)
            }
        }
    }

    fun disconnect(): Result<Unit> {
        return runCatching {
            credentialsRepository.deleteById("default")
            logger.info { "Strava credentials removed" }
        }.onFailure { e ->
            logger.error(e) { "Failed to disconnect Strava: ${e.message}" }
        }
    }

    fun getAuthorizeUrl(): Result<String> {
        if (clientId.isBlank()) {
            return Result.failure(IllegalStateException("Strava client_id is not configured"))
        }

        return runCatching {
            val scope = "activity:read_all"
            val authUrl = "https://www.strava.com/oauth/authorize?client_id=$clientId&redirect_uri=${java.net.URLEncoder.encode(oauthRedirectUrl, "UTF-8")}&response_type=code&scope=$scope"
            logger.debug { "Generated Strava authorize URL" }
            authUrl
        }
    }
}
