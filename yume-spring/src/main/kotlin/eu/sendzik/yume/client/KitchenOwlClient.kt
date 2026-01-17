package eu.sendzik.yume.client

import eu.sendzik.yume.service.kitchenowl.model.Recipe
import eu.sendzik.yume.service.kitchenowl.model.ShoppingList
import eu.sendzik.yume.service.kitchenowl.model.ShoppingListEntry
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.service.annotation.DeleteExchange
import org.springframework.web.service.annotation.GetExchange
import org.springframework.web.service.annotation.PostExchange
import org.springframework.web.service.annotation.PutExchange

interface KitchenOwlClient {

    @GetExchange("/household/{householdId}/shoppinglist")
    fun fetchShoppingLists(@PathVariable householdId: String): List<ShoppingList>

    @PostExchange("/shoppinglist/{householdId}/add-item-by-name")
    fun createShoppingListEntry(
        @PathVariable householdId: String,
        @RequestBody body: CreateShoppingListEntryRequest
    ): ShoppingListEntry

    @PutExchange("/shoppinglist/{householdId}/item/{itemId}")
    fun updateShoppingListEntry(
        @PathVariable
        householdId: String,
        @PathVariable
        itemId: String,
        @RequestBody
        body: UpdateShoppingListEntryRequest
    ): ShoppingListEntry

    @DeleteExchange("/item/{itemId}")
    fun removeShoppingListEntry(@PathVariable itemId: String)

    @GetExchange("/household/{householdId}/recipe")
    fun fetchRecipes(@PathVariable householdId: String): List<Recipe>

    data class CreateShoppingListEntryRequest(
        val name: String,
        val description: String = ""
    )

    data class UpdateShoppingListEntryRequest(
        val description: String
    )
}