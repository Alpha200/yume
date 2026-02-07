package eu.sendzik.yume.service.strava.model

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.annotation.JsonProperty
import java.time.Instant

@JsonIgnoreProperties(ignoreUnknown = true)
data class StravaTokenResponse(
    @JsonProperty("token_type")
    val tokenType: String,
    @JsonProperty("expires_at")
    val expiresAt: Long,  // Unix timestamp
    @JsonProperty("expires_in")
    val expiresIn: Int,
    @JsonProperty("refresh_token")
    val refreshToken: String,
    @JsonProperty("access_token")
    val accessToken: String,
    @JsonProperty("athlete")
    val athlete: StravaAthlete? = null,
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class StravaAthlete(
    @JsonProperty("id")
    val id: Long,
    @JsonProperty("firstname")
    val firstname: String,
    @JsonProperty("lastname")
    val lastname: String,
)

fun StravaTokenResponse.toCredentials(
    existingAthleteId: Long? = null,
    existingAthleteName: String? = null
): StravaCredentials {
    val name = athlete?.let { "${it.firstname} ${it.lastname}".trim() } ?: existingAthleteName
    val athleteId = athlete?.id ?: existingAthleteId
        ?: throw IllegalArgumentException("Athlete ID is missing from token response and no existing ID provided")

    return StravaCredentials(
        athleteId = athleteId,
        athleteName = name,
        accessToken = accessToken,
        refreshToken = refreshToken,
        tokenExpiresAt = Instant.ofEpochSecond(expiresAt),
    )
}
