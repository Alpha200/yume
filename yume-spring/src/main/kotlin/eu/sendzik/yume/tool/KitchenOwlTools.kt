package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.service.kitchenowl.KitchenOwlService
import eu.sendzik.yume.tool.model.ShoppingListItem
import eu.sendzik.yume.tool.model.ShoppingListItemUpdate
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component

@Component
@Suppress("unused")
class KitchenOwlTools(
    private val kitchenOwlService: KitchenOwlService,
    private val logger: KLogger,
) {
    @Suppress("UNUSED")
    @Tool("Add a new item to the shopping list")
    fun addShoppingListItem(
        @P("Name of the item to add")
        name: String,
        @P("Optional description for the item (e.g., quantity or details)")
        description: String? = null
    ): String {
        return kitchenOwlService.createShoppingListEntry(name, description).map {
            "Added '${it.name}' to shopping list (ID: ${it.id})"
        }.onFailure {
            logger.error(it) { "Error adding shopping list item" }
        }.getOrElse {
            "Failed to add item to shopping list"
        }
    }

    @Suppress("UNUSED")
    @Tool("Update a shopping list item's description")
    fun updateShoppingListItem(
        @P("ID of the item to update")
        itemId: String,
        @P("New description for the item")
        description: String
    ): String {
        return kitchenOwlService.updateShoppingListEntry(itemId, description).onFailure {
            logger.error(it) { "Error updating shopping list item" }
        }.map { entry ->
            if (entry != null) {
                "Updated '${entry.name}' description to '${entry.description}'"
            } else {
                "Failed to update item $itemId"
            }
        }.getOrElse {
            "Failed to update shopping list item description"
        }
    }

    @Suppress("UNUSED")
    @Tool("Remove an item from the shopping list")
    fun removeShoppingListItem(
        @P("ID of the item to remove")
        itemId: String
    ): String {
        return kitchenOwlService.removeShoppingListEntry(itemId).onFailure {
            logger.error(it) { "Error removing shopping list item" }
        }.map {
            "Removed item $itemId from shopping list"
        }.getOrElse {
            "Failed to remove item $itemId"
        }
    }

    @Suppress("UNUSED")
    @Tool("Add multiple items to the shopping list at once (Use this for more than one item to save time)")
    fun addShoppingListItemsBatch(
        @P("List of items to add to the shopping list")
        items: List<ShoppingListItem>
    ): String {
        val itemsDicts = items.map { item ->
            mapOf(
                "name" to item.name,
                "description" to item.description
            )
        }

        val entries = kitchenOwlService.batchCreateShoppingListEntries(itemsDicts)

        return if (entries.isNotEmpty()) {
            buildString {
                appendLine("Added ${entries.size} items to shopping list:")
                entries.forEach { entry ->
                    appendLine("- ${entry.name}")
                }
            }
        } else {
            "Failed to add items to shopping list"
        }
    }

    @Suppress("UNUSED")
    @Tool("Update multiple shopping list items at once (Use this for more than one item to save time)")
    fun updateShoppingListItemsBatch(
        @P("List of items to update in the shopping list")
        updates: List<ShoppingListItemUpdate>
    ): String {
        val updatesDicts = updates.map { update ->
            mapOf(
                "id" to update.id,
                "description" to update.description
            )
        }

        val entries = kitchenOwlService.batchUpdateShoppingListEntries(updatesDicts)

        return if (entries.isNotEmpty()) {
            buildString {
                appendLine("Updated ${entries.size} items in shopping list:")
                entries.forEach { entry ->
                    appendLine("- ${entry.name}: ${entry.description}")
                }
            }
        } else {
            "Failed to update items in shopping list"
        }
    }
}