package eu.sendzik.yume.service.efa.model

import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.annotation.JsonIgnoreProperties

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaJourneyResponse(
    @JsonProperty("journeys")
    val journeys: List<EfaJourney> = emptyList()
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaJourney(
    @JsonProperty("legs")
    val legs: List<EfaLeg> = emptyList()
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaLeg(
    @JsonProperty("transportation")
    val transportation: EfaTransportation? = null,
    @JsonProperty("origin")
    val origin: EfaLegLocation? = null,
    @JsonProperty("destination")
    val destination: EfaLegLocation? = null,
    @JsonProperty("duration")
    val duration: Int? = null
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaLegLocation(
    @JsonProperty("name")
    val name: String? = null,
    @JsonProperty("disassembledName")
    val disassembledName: String? = null,
    @JsonProperty("departureTimePlanned")
    val departureTimePlanned: String? = null,
    @JsonProperty("departureTimeEstimated")
    val departureTimeEstimated: String? = null,
    @JsonProperty("departureTimeBaseTimetable")
    val departureTimeBaseTimetable: String? = null,
    @JsonProperty("arrivalTimePlanned")
    val arrivalTimePlanned: String? = null,
    @JsonProperty("arrivalTimeEstimated")
    val arrivalTimeEstimated: String? = null,
    @JsonProperty("arrivalTimeBaseTimetable")
    val arrivalTimeBaseTimetable: String? = null,
    @JsonProperty("properties")
    val properties: EfaLocationProperties? = null,
    @JsonProperty("parent")
    val parent: EfaLegLocation? = null
)

