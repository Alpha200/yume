package eu.sendzik.yume.service.efa.model

import com.fasterxml.jackson.annotation.JsonProperty

data class PublicTransportDeparture(
    @JsonProperty("line")
    val line: String,
    @JsonProperty("destination")
    val destination: String,
    @JsonProperty("planned_time")
    val plannedTime: String,
    @JsonProperty("estimated_time")
    val estimatedTime: String? = null,
    @JsonProperty("delay_minutes")
    val delayMinutes: Int? = null,
    @JsonProperty("transport_type")
    val transportType: String,
    @JsonProperty("platform")
    val platform: String? = null,
    @JsonProperty("realtime")
    val realtime: Boolean = false
)

