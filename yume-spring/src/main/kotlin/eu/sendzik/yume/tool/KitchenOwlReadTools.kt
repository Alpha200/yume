package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.service.kitchenowl.KitchenOwlService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component

@Component
@Suppress("unused")
class KitchenOwlReadTools(
    private val kitchenOwlService: KitchenOwlService,
    private val logger: KLogger,
) {
    @Suppress("UNUSED")
    @Tool("Fetch the current shopping list with all items")
    fun fetchShoppingList(): String {
        return kitchenOwlService.fetchShoppingList().onFailure {
            logger.error(it) { "Error fetching shopping list" }
        }.map { shoppingList ->
            if (shoppingList != null) {
                val items = shoppingList.items ?: emptyList()
                buildString {
                    appendLine("Current shopping list: ${items.size} items")
                    items.forEach { item ->
                        appendLine("- ${item.name} (ID: ${item.id}): ${item.description ?: "no description"}")
                    }
                }
            } else {
                "No shopping list found"
            }
        }.getOrElse {
            "Failed to fetch shopping list"
        }
    }

    @Suppress("UNUSED")
    @Tool("Fetch all available recipe names and IDs")
    fun fetchRecipeNames(): String {
        return kitchenOwlService.fetchRecipeNames().onFailure {
            logger.error(it) { "Error fetching recipe names" }
        }.map {
            if (it.isNotEmpty()) {
                buildString {
                    appendLine("Available recipes (${it.size} total):")
                    it.forEach { recipe ->
                        appendLine("- ${recipe["name"]} (ID: ${recipe["id"]})")
                    }
                }
            } else {
                "No recipes found"
            }
        }.getOrElse {
            "Failed to fetch recipe names"
        }
    }

    @Suppress("UNUSED")
    @Tool("Fetch a full recipe by ID including ingredients")
    fun fetchRecipe(
        @P("Recipe ID")
        recipeId: Int
    ): String {
        return kitchenOwlService.fetchRecipe(recipeId).onFailure {
            logger.error(it) { "Error fetching recipe" }
        }.map {
            if (it == null) {
                "Recipe with ID $recipeId not found"
            } else {
                buildString {
                    appendLine("Recipe: ${it.name}")

                    if (!it.description.isNullOrBlank()) {
                        appendLine("Instructions:")
                        appendLine(it.description)
                        appendLine("--------------------")
                    }

                    appendLine("Yields: ${it.yields}")

                    if (!it.items.isNullOrEmpty()) {
                        appendLine("Ingredients:")

                        it.items.forEach { item ->
                            val descStr = item.description?.let { " - $it" } ?: ""
                            appendLine("- ${item.name}$descStr")
                        }
                    }
                }
            }
        }.getOrElse {
            "Failed to fetch recipe with ID $recipeId"
        }
    }
}