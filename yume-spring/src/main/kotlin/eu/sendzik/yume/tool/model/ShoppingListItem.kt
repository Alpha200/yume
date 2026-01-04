package eu.sendzik.yume.tool.model

import com.fasterxml.jackson.annotation.JsonProperty

data class ShoppingListItem(
    @JsonProperty("name")
    val name: String,
    @JsonProperty("description")
    val description: String? = null
)

