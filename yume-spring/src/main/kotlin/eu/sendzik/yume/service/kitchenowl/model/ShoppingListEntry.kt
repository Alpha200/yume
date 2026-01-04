package eu.sendzik.yume.service.kitchenowl.model

import com.fasterxml.jackson.annotation.JsonProperty

data class ShoppingListEntry(
    @JsonProperty("id")
    val id: String,
    @JsonProperty("name")
    val name: String,
    @JsonProperty("description")
    val description: String? = null
)

