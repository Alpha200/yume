package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.service.kitchenowl.KitchenOwlService
import eu.sendzik.yume.tool.model.ShoppingListItem
import eu.sendzik.yume.tool.model.ShoppingListItemUpdate
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component

@Component
class KitchenOwlTools(
    private val kitchenOwlService: KitchenOwlService,
    private val logger: KLogger,
) {

    /**
     * Add a new item to the shopping list
     */
    @Suppress("UNUSED")
    @Tool("Add a new item to the shopping list")
    fun addShoppingListItem(
        @P("Name of the item to add")
        name: String,
        @P("Optional description for the item (e.g., quantity or details)")
        description: String? = null
    ): String = runCatching {
        val entry = kitchenOwlService.createShoppingListEntry(name, description)
        if (entry != null) {
            "Added '${entry.name}' to shopping list (ID: ${entry.id})"
        } else {
            "Failed to add '$name' to shopping list"
        }
    }.getOrElse {
        logger.error(it) { "Error adding shopping list item" }
        "Error: ${it.message}"
    }

    /**
     * Update a shopping list item's description
     */
    @Suppress("UNUSED")
    @Tool("Update a shopping list item's description")
    fun updateShoppingListItem(
        @P("ID of the item to update")
        itemId: String,
        @P("New description for the item")
        description: String
    ): String = runCatching {
        val entry = kitchenOwlService.updateShoppingListEntry(itemId, description)
        if (entry != null) {
            "Updated '${entry.name}' description to '${entry.description}'"
        } else {
            "Failed to update item $itemId"
        }
    }.getOrElse {
        logger.error(it) { "Error updating shopping list item" }
        "Error: ${it.message}"
    }

    /**
     * Remove an item from the shopping list
     */
    @Suppress("UNUSED")
    @Tool("Remove an item from the shopping list")
    fun removeShoppingListItem(
        @P("ID of the item to remove")
        itemId: String
    ): String = runCatching {
        val success = kitchenOwlService.removeShoppingListEntry(itemId)
        if (success) {
            "Removed item $itemId from shopping list"
        } else {
            "Failed to remove item $itemId"
        }
    }.getOrElse {
        logger.error(it) { "Error removing shopping list item" }
        "Error: ${it.message}"
    }

    /**
     * Add multiple items to the shopping list in batch
     */
    @Suppress("UNUSED")
    @Tool("Add multiple items to the shopping list in batch")
    fun addShoppingListItemsBatch(
        @P("List of items to add to the shopping list")
        items: List<ShoppingListItem>
    ): String = runCatching {
        val itemsDicts = items.map { item ->
            mapOf(
                "name" to item.name,
                "description" to item.description
            )
        }
        val entries = kitchenOwlService.batchCreateShoppingListEntries(itemsDicts)
        if (entries.isNotEmpty()) {
            val result = StringBuilder("Added ${entries.size} items to shopping list:\n")
            entries.forEach { entry ->
                result.append("- ${entry.name}\n")
            }
            result.toString()
        } else {
            "Failed to add items to shopping list"
        }
    }.getOrElse {
        logger.error(it) { "Error adding shopping list items in batch" }
        "Error: ${it.message}"
    }

    /**
     * Update multiple shopping list items in batch (description only)
     */
    @Suppress("UNUSED")
    @Tool("Update multiple shopping list items in batch (description only)")
    fun updateShoppingListItemsBatch(
        @P("List of items to update in the shopping list")
        updates: List<ShoppingListItemUpdate>
    ): String = runCatching {
        val updatesDicts = updates.map { update ->
            mapOf(
                "id" to update.id,
                "description" to update.description
            )
        }
        val entries = kitchenOwlService.batchUpdateShoppingListEntries(updatesDicts)
        if (entries.isNotEmpty()) {
            val result = StringBuilder("Updated ${entries.size} items in shopping list:\n")
            entries.forEach { entry ->
                result.append("- ${entry.name}: ${entry.description}\n")
            }
            result.toString()
        } else {
            "Failed to update items in shopping list"
        }
    }.getOrElse {
        logger.error(it) { "Error updating shopping list items in batch" }
        "Error: ${it.message}"
    }
}