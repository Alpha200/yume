package eu.sendzik.yume.service.kitchenowl.model

import com.fasterxml.jackson.annotation.JsonProperty

data class Recipe(
    val id: Int,
    val name: String,
    val description: String? = null,
    val items: List<RecipeItem>? = null,
    @JsonProperty("cook_time")
    val cookTime: Int = 0,
    @JsonProperty("prep_time")
    val prepTime: Int = 0,
    val time: Int = 0,
    val yields: Int? = null
)

