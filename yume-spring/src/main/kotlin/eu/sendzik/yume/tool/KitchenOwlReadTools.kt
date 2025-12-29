package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.service.kitchenowl.KitchenOwlService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component

@Component
class KitchenOwlReadTools(
    private val kitchenOwlService: KitchenOwlService,
    private val logger: KLogger,
) {

    /**
     * Fetch the current shopping list with all items
     */
    @Suppress("UNUSED")
    @Tool("Fetch the current shopping list with all items")
    fun fetchShoppingList(): String = runCatching {
        val shoppingList = kitchenOwlService.fetchShoppingList()
        if (shoppingList != null) {
            val items = shoppingList.items ?: emptyList()
            val result = StringBuilder("Current shopping list: ${items.size} items\n")
            items.forEach { item ->
                result.append("- ${item.name} (ID: ${item.id}): ${item.description ?: "no description"}\n")
            }
            result.toString()
        } else {
            "No shopping list found"
        }
    }.getOrElse {
        logger.error(it) { "Error fetching shopping list" }
        "Error: ${it.message}"
    }

    /**
     * Fetch all available recipe names and IDs
     */
    @Suppress("UNUSED")
    @Tool("Fetch all available recipe names and IDs")
    fun fetchRecipeNames(): String = runCatching {
        val recipes = kitchenOwlService.fetchRecipeNames()
        if (recipes.isNotEmpty()) {
            val result = StringBuilder("Available recipes (${recipes.size} total):\n")
            recipes.forEach { recipe ->
                result.append("- ${recipe["name"]} (ID: ${recipe["id"]})\n")
            }
            result.toString()
        } else {
            "No recipes found"
        }
    }.getOrElse {
        logger.error(it) { "Error fetching recipe names" }
        "Error: ${it.message}"
    }

    /**
     * Fetch a full recipe by ID including ingredients
     */
    @Suppress("UNUSED")
    @Tool("Fetch a full recipe by ID including ingredients")
    fun fetchRecipe(
        @P("Recipe ID")
        recipeId: Int
    ): String = runCatching {
        val recipe = kitchenOwlService.fetchRecipe(recipeId)
        if (recipe != null) {
            val result = StringBuilder("Recipe: ${recipe.name}\n")
            if (!recipe.description.isNullOrBlank()) {
                result.append("Instructions: ${recipe.description}\n")
            }
            result.append("Yields: ${recipe.yields}\n")
            if (!recipe.items.isNullOrEmpty()) {
                result.append("Ingredients (${recipe.items.size}):\n")
                recipe.items.forEach { item ->
                    val optionalStr = if (item.optional) " (optional)" else ""
                    val descStr = item.description?.let { " - $it" } ?: ""
                    result.append("- ${item.name}$descStr$optionalStr\n")
                }
            }
            result.toString()
        } else {
            "Recipe with ID $recipeId not found"
        }
    }.getOrElse {
        logger.error(it) { "Error fetching recipe" }
        "Error: ${it.message}"
    }
}