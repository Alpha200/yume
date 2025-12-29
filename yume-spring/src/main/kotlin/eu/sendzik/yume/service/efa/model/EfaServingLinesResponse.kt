package eu.sendzik.yume.service.efa.model

import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.annotation.JsonIgnoreProperties

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaServingLinesResponse(
    @JsonProperty("lines")
    val lines: List<EfaLine> = emptyList()
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaLine(
    @JsonProperty("id")
    val id: String? = null,
    @JsonProperty("name")
    val name: String? = null,
    @JsonProperty("number")
    val number: String? = null,
    @JsonProperty("disassembledName")
    val disassembledName: String? = null,
    @JsonProperty("product")
    val product: EfaProduct? = null
)

@JsonIgnoreProperties(ignoreUnknown = true)
data class EfaProduct(
    @JsonProperty("name")
    val name: String? = null,
    @JsonProperty("class")
    val clazz: Int? = null
)

