package eu.sendzik.yume.service.kitchenowl.model

import com.fasterxml.jackson.annotation.JsonProperty

data class RecipeNameResponse(
    @JsonProperty("id")
    val id: Int,
    @JsonProperty("name")
    val name: String
)

