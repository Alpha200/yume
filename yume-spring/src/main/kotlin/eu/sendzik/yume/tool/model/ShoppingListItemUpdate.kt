package eu.sendzik.yume.tool.model

import com.fasterxml.jackson.annotation.JsonProperty

data class ShoppingListItemUpdate(
    @JsonProperty("id")
    val id: String,
    @JsonProperty("description")
    val description: String
)

