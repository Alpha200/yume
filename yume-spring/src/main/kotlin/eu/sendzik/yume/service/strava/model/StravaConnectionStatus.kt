package eu.sendzik.yume.service.strava.model

import com.fasterxml.jackson.annotation.JsonProperty

data class StravaConnectionStatus(
    @JsonProperty("connected")
    val connected: Boolean,
    @JsonProperty("athleteId")
    val athleteId: Long? = null,
    @JsonProperty("athleteName")
    val athleteName: String? = null,
    @JsonProperty("tokenExpired")
    val tokenExpired: Boolean = false,
)
