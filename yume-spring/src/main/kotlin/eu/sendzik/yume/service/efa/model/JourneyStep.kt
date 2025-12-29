package eu.sendzik.yume.service.efa.model

import com.fasterxml.jackson.annotation.JsonProperty

data class JourneyStep(
    @JsonProperty("mode")
    val mode: String,
    @JsonProperty("line")
    val line: String? = null,
    @JsonProperty("origin")
    val origin: String,
    @JsonProperty("destination")
    val destination: String,
    @JsonProperty("departure_planned")
    val departurePlanned: String? = null,
    @JsonProperty("departure_estimated")
    val departureEstimated: String? = null,
    @JsonProperty("arrival_planned")
    val arrivalPlanned: String? = null,
    @JsonProperty("arrival_estimated")
    val arrivalEstimated: String? = null,
    @JsonProperty("platform_origin")
    val platformOrigin: String? = null,
    @JsonProperty("platform_destination")
    val platformDestination: String? = null,
    @JsonProperty("departure_delay_minutes")
    val departureDelayMinutes: Int? = null,
    @JsonProperty("arrival_delay_minutes")
    val arrivalDelayMinutes: Int? = null,
    @JsonProperty("duration_minutes")
    val durationMinutes: Int
)

