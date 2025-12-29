package eu.sendzik.yume.service.kitchenowl.model

import com.fasterxml.jackson.annotation.JsonProperty

data class RecipeItem(
    @JsonProperty("id")
    val id: Int,
    @JsonProperty("name")
    val name: String,
    @JsonProperty("description")
    val description: String? = null,
    @JsonProperty("optional")
    val optional: Boolean = false
)

