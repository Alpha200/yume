package eu.sendzik.yume.service.kitchenowl.model

import com.fasterxml.jackson.annotation.JsonProperty

data class Recipe(
    @JsonProperty("id")
    val id: Int,
    @JsonProperty("name")
    val name: String,
    @JsonProperty("description")
    val description: String? = null,
    @JsonProperty("items")
    val items: List<RecipeItem>? = null,
    @JsonProperty("cook_time")
    val cookTime: Int = 0,
    @JsonProperty("prep_time")
    val prepTime: Int = 0,
    @JsonProperty("time")
    val time: Int = 0,
    @JsonProperty("yields")
    val yields: Int? = null
)

