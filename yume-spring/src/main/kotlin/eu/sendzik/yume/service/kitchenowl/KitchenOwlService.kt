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
    fun fetchShoppingList(): ShoppingList? {
        return try {
            val shoppingLists = kitchenOwlClient.fetchShoppingLists(householdId)
            if (!shoppingLists.isNullOrEmpty()) {
                // Return the first (default) shopping list
                shoppingLists.first()
            } else {
                logger.warn { "No shopping lists found" }
                null
            }
        } catch (e: Exception) {
            logger.error(e) { "Error fetching shopping list" }
            null
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
    ): ShoppingListEntry? {
        return try {
            val request = KitchenOwlClient.CreateShoppingListEntryRequest(
                name = name,
                description = description ?: ""
            )
            kitchenOwlClient.createShoppingListEntry(householdId, request)
        } catch (e: Exception) {
            logger.error(e) { "Error creating shopping list entry" }
            null
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
    ): ShoppingListEntry? {
        return try {
            val request = KitchenOwlClient.UpdateShoppingListEntryRequest(
                description = description
            )
            kitchenOwlClient.updateShoppingListEntry(householdId, entryId, request)
        } catch (e: Exception) {
            logger.error(e) { "Error updating shopping list entry" }
            null
        }
    }

    /**
     * Remove a shopping list entry
     *
     * @param entryId ID of the entry to remove
     * @return True if successful, False otherwise
     */
    fun removeShoppingListEntry(entryId: String): Boolean {
        return try {
            kitchenOwlClient.removeShoppingListEntry(entryId)
            true
        } catch (e: Exception) {
            logger.error(e) { "Error removing shopping list entry" }
            false
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
            if (entry != null) {
                createdEntries.add(entry)
            } else {
                logger.warn { "Failed to create entry: $item" }
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

            val entry = updateShoppingListEntry(entryId, description)
            if (entry != null) {
                updatedEntries.add(entry)
            } else {
                logger.warn { "Failed to update entry: $update" }
            }
        }
        return updatedEntries
    }

    /**
     * Fetch all recipe names and IDs
     *
     * @return List of maps with recipe id and name
     */
    fun fetchRecipeNames(): List<Map<String, Any>> {
        return try {
            val recipes = kitchenOwlClient.fetchRecipes(householdId)
            recipes?.map { recipe ->
                mapOf(
                    "id" to recipe.id,
                    "name" to recipe.name
                )
            } ?: emptyList()
        } catch (e: Exception) {
            logger.error(e) { "Error fetching recipe names" }
            emptyList()
        }
    }

    /**
     * Fetch a full recipe by ID
     *
     * @param recipeId ID of the recipe to fetch
     * @return Recipe object if found, null otherwise
     */
    fun fetchRecipe(recipeId: Int): Recipe? {
        return try {
            val recipes = kitchenOwlClient.fetchRecipes(householdId)
            recipes?.find { it.id == recipeId }.also {
                if (it == null) {
                    logger.warn { "Recipe with ID $recipeId not found" }
                }
            }
        } catch (e: Exception) {
            logger.error(e) { "Error fetching recipe" }
            null
        }
    }
}

