package eu.sendzik.yume.service.efa.model

import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.annotation.JsonIgnoreProperties

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaDeparturesResponse(
    @JsonProperty("stopEvents")
    val stopEvents: List<EfaStopEvent> = emptyList()
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaStopEvent(
    @JsonProperty("location")
    val location: EfaLocationInfo? = null,
    @JsonProperty("transportation")
    val transportation: EfaTransportation? = null,
    @JsonProperty("departureTimePlanned")
    val departureTimePlanned: String? = null,
    @JsonProperty("departureTimeEstimated")
    val departureTimeEstimated: String? = null,
    @JsonProperty("isRealtimeControlled")
    val isRealtimeControlled: Boolean = false
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaLocationInfo(
    @JsonProperty("properties")
    val properties: EfaLocationProperties? = null,
    @JsonProperty("id")
    val id: String? = null,
    @JsonProperty("name")
    val name: String? = null
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaLocationProperties(
    @JsonProperty("platform")
    val platform: String? = null
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaTransportation(
    @JsonProperty("number")
    val number: String? = null,
    @JsonProperty("name")
    val name: String? = null,
    @JsonProperty("destination")
    val destination: EfaDestination? = null,
    @JsonProperty("product")
    val product: EfaProduct? = null
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaDestination(
    @JsonProperty("name")
    val name: String? = null
)

