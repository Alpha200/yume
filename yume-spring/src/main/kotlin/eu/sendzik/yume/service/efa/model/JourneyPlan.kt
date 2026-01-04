package eu.sendzik.yume.service.efa.model

import com.fasterxml.jackson.annotation.JsonProperty

data class JourneyPlan(
    @JsonProperty("length_minutes")
    val lengthMinutes: Int,
    @JsonProperty("steps")
    val steps: List<JourneyStep>
)

