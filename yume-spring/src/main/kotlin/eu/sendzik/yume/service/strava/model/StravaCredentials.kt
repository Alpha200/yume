package eu.sendzik.yume.service.strava.model

import org.springframework.data.annotation.Id
import org.springframework.data.mongodb.core.mapping.Document
import java.time.Instant

@Document(collection = "strava_credentials")
data class StravaCredentials(
    @Id
    val id: String = "default",
    val athleteId: Long,
    val athleteName: String? = null,
    val accessToken: String,
    val refreshToken: String,
    val tokenExpiresAt: Instant,
    val createdAt: Instant = Instant.now(),
    val updatedAt: Instant = Instant.now(),
) {
    fun isTokenExpired(): Boolean = Instant.now().isAfter(tokenExpiresAt)
}
