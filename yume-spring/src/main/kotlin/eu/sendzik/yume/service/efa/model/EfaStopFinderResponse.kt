package eu.sendzik.yume.service.efa.model

import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.annotation.JsonIgnoreProperties

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaStopFinderResponse(
    @JsonProperty("locations")
    val locations: List<EfaLocation> = emptyList()
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaLocation(
    @JsonProperty("id")
    val id: String? = null,
    @JsonProperty("name")
    val name: String? = null,
    @JsonProperty("type")
    val type: String? = null,
    @JsonProperty("matchQuality")
    val matchQuality: Double? = null,
    @JsonProperty("properties")
    val properties: Map<String, Any>? = null,
    @JsonProperty("parent")
    val parent: EfaLocation? = null
)

