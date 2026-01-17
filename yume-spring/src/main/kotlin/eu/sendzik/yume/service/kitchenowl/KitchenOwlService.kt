package eu.sendzik.yume.service.kitchenowl

import eu.sendzik.yume.client.KitchenOwlClient
import eu.sendzik.yume.service.kitchenowl.model.Recipe
import eu.sendzik.yume.service.kitchenowl.model.ShoppingList
import eu.sendzik.yume.service.kitchenowl.model.ShoppingListEntry
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class KitchenOwlService(
    private val kitchenOwlClient: KitchenOwlClient,
    private val logger: KLogger,
    @Value("\${yume.kitchenowl.household-id:1}")
    private val householdId: String,
) {

    /**
     * Fetch the current shopping list with all its items
     *
     * @return ShoppingList if found, null otherwise
     */
    fun fetchShoppingList(): Result<ShoppingList?> {
        return runCatching {
            kitchenOwlClient.fetchShoppingLists(householdId).firstOrNull()
        }
    }

    /**
     * Create a new shopping list entry
     *
     * @param name Name of the item
     * @param description Description of the item (e.g., amount information)
     * @return ShoppingListEntry if successful, null otherwise
     */
    fun createShoppingListEntry(
        name: String,
        description: String? = null
    ): Result<ShoppingListEntry> {
        return runCatching {
            val request = KitchenOwlClient.CreateShoppingListEntryRequest(
                name = name,
                description = description ?: ""
            )
            kitchenOwlClient.createShoppingListEntry(householdId, request)
        }
    }

    /**
     * Update an existing shopping list entry (description only)
     *
     * @param entryId ID of the entry to update
     * @param description New description
     * @return Updated ShoppingListEntry if successful, null otherwise
     */
    fun updateShoppingListEntry(
        entryId: String,
        description: String
    ): Result<ShoppingListEntry> {
        return runCatching {
            val request = KitchenOwlClient.UpdateShoppingListEntryRequest(
                description = description
            )
            kitchenOwlClient.updateShoppingListEntry(householdId, entryId, request)
        }
    }

    /**
     * Remove a shopping list entry
     *
     * @param entryId ID of the entry to remove
     */
    fun removeShoppingListEntry(entryId: String): Result<Unit> {
        return runCatching {
            kitchenOwlClient.removeShoppingListEntry(entryId)
        }
    }

    /**
     * Create multiple shopping list entries in batch
     *
     * @param items List of maps with 'name' and optional 'description' keys
     * @return List of created ShoppingListEntry objects
     */
    fun batchCreateShoppingListEntries(
        items: List<Map<String, String?>>
    ): List<ShoppingListEntry> {
        val createdEntries = mutableListOf<ShoppingListEntry>()
        for (item in items) {
            val entry = createShoppingListEntry(
                name = item["name"] ?: "",
                description = item["description"]
            )
            entry.onSuccess {
                createdEntries.add(it)
            }.onFailure {
                logger.error(it) { "Error creating entry: $item" }
            }
        }
        return createdEntries
    }

    /**
     * Update multiple shopping list entries in batch (description only)
     *
     * @param updates List of maps with 'id' and 'description' keys
     * @return List of updated ShoppingListEntry objects
     */
    fun batchUpdateShoppingListEntries(
        updates: List<Map<String, String?>>
    ): List<ShoppingListEntry> {
        val updatedEntries = mutableListOf<ShoppingListEntry>()
        for (update in updates) {
            val entryId = update["id"]
            val description = update["description"]

            if (entryId == null) {
                logger.warn { "Update missing required 'id' key" }
                continue
            }
            if (description == null) {
                logger.warn { "Update for $entryId missing required 'description' key" }
                continue
            }

            updateShoppingListEntry(entryId, description).onSuccess {
                updatedEntries.add(it)
            }.onFailure {
                logger.error(it) { "Error updating entry: $update" }
            }
        }
        return updatedEntries
    }

    /**
     * Fetch all recipe names and IDs
     *
     * @return List of maps with recipe id and name
     */
    fun fetchRecipeNames(): Result<List<Map<String, Any>>> {
        return runCatching {
            kitchenOwlClient.fetchRecipes(householdId)
        }.map {
            it.map { recipe ->
                mapOf(
                    "id" to recipe.id,
                    "name" to recipe.name
                )
            }
        }
    }

    /**
     * Fetch a full recipe by ID
     *
     * @param recipeId ID of the recipe to fetch
     * @return Recipe object if found, null otherwise
     */
    fun fetchRecipe(recipeId: Int): Result<Recipe?> {
        return runCatching {
            kitchenOwlClient.fetchRecipes(householdId)
        }.map {
            it.find { recipe -> recipe.id == recipeId }
        }
    }
}

