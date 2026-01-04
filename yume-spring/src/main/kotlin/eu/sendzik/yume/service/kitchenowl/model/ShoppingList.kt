package eu.sendzik.yume.service.kitchenowl.model

import com.fasterxml.jackson.annotation.JsonProperty

data class ShoppingList(
    @JsonProperty("id")
    val id: String,
    @JsonProperty("name")
    val name: String,
    @JsonProperty("items")
    val items: List<ShoppingListEntry>? = null,
    @JsonProperty("recentItems")
    val recentItems: List<ShoppingListEntry>? = null
)

