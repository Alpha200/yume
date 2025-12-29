package eu.sendzik.yume.client

import eu.sendzik.yume.service.kitchenowl.model.Recipe
import eu.sendzik.yume.service.kitchenowl.model.ShoppingList
import eu.sendzik.yume.service.kitchenowl.model.ShoppingListEntry
import org.springframework.web.service.annotation.DeleteExchange
import org.springframework.web.service.annotation.GetExchange
import org.springframework.web.service.annotation.PostExchange
import org.springframework.web.service.annotation.PutExchange

interface KitchenOwlClient {

    @GetExchange("/household/{householdId}/shoppinglist")
    fun fetchShoppingLists(householdId: String): List<ShoppingList>?

    @PostExchange("/shoppinglist/{householdId}/add-item-by-name")
    fun createShoppingListEntry(
        householdId: String,
        body: CreateShoppingListEntryRequest
    ): ShoppingListEntry?

    @PutExchange("/shoppinglist/{householdId}/item/{itemId}")
    fun updateShoppingListEntry(
        householdId: String,
        itemId: String,
        body: UpdateShoppingListEntryRequest
    ): ShoppingListEntry?

    @DeleteExchange("/item/{itemId}")
    fun removeShoppingListEntry(itemId: String): Void?

    @GetExchange("/household/{householdId}/recipe")
    fun fetchRecipes(householdId: String): List<Recipe>?

    data class CreateShoppingListEntryRequest(
        val name: String,
        val description: String = ""
    )

    data class UpdateShoppingListEntryRequest(
        val description: String
    )
}