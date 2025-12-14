import logging
from agents import function_tool
from typing import Optional, List
from pydantic import BaseModel
from services.kitchenowl import kitchenowl_service

logger = logging.getLogger(__name__)


class ShoppingListItem(BaseModel):
    """Model for shopping list item input"""
    name: str
    description: Optional[str] = None


class ShoppingListItemUpdate(BaseModel):
    """Model for shopping list item update"""
    id: str
    description: str


@function_tool
async def fetch_shopping_list() -> str:
    """Fetch the current shopping list with all items"""
    try:
        shopping_list = await kitchenowl_service.fetch_shopping_list()
        if shopping_list:
            items = shopping_list.get('items', [])
            result = f"Current shopping list: {len(items)} items\n"
            for item in items:
                result += f"- {item['name']} (ID: {item['id']}): {item.get('description', 'no description')}\n"
            return result
        else:
            return "No shopping list found"
    except Exception as e:
        logger.error(f"Error fetching shopping list: {e}")
        return f"Error: {str(e)}"


@function_tool
async def fetch_recipe_names() -> str:
    """Fetch all available recipe names and IDs"""
    try:
        recipes = await kitchenowl_service.fetch_recipe_names()
        if recipes:
            result = f"Available recipes ({len(recipes)} total):\n"
            for recipe in recipes:
                result += f"- {recipe['name']} (ID: {recipe['id']})\n"
            return result
        else:
            return "No recipes found"
    except Exception as e:
        logger.error(f"Error fetching recipe names: {e}")
        return f"Error: {str(e)}"


@function_tool
async def fetch_recipe(recipe_id: int) -> str:
    """Fetch a full recipe by ID including ingredients"""
    try:
        recipe = await kitchenowl_service.fetch_recipe(recipe_id)
        if recipe:
            result = f"Recipe: {recipe.name}\n"
            if recipe.description:
                result += f"Instructions: {recipe.description}\n"
            result += f"Yields: {recipe.yields}\n"
            if recipe.items:
                result += f"Ingredients ({len(recipe.items)}):\n"
                for item in recipe.items:
                    optional_str = " (optional)" if item.optional else ""
                    desc = f" - {item.description}" if item.description else ""
                    result += f"- {item.name}{desc}{optional_str}\n"
            return result
        else:
            return f"Recipe with ID {recipe_id} not found"
    except Exception as e:
        logger.error(f"Error fetching recipe: {e}")
        return f"Error: {str(e)}"


@function_tool
async def add_shopping_list_item(name: str, description: Optional[str] = None) -> str:
    """Add a new item to the shopping list"""
    try:
        entry = await kitchenowl_service.create_shopping_list_entry(name, description)
        if entry:
            return f"Added '{entry.name}' to shopping list (ID: {entry.id})"
        else:
            return f"Failed to add '{name}' to shopping list"
    except Exception as e:
        logger.error(f"Error adding shopping list item: {e}")
        return f"Error: {str(e)}"


@function_tool
async def update_shopping_list_item(item_id: str, description: str) -> str:
    """Update a shopping list item's description"""
    try:
        entry = await kitchenowl_service.update_shopping_list_entry(item_id, description)
        if entry:
            return f"Updated '{entry.name}' description to '{entry.description}'"
        else:
            return f"Failed to update item {item_id}"
    except Exception as e:
        logger.error(f"Error updating shopping list item: {e}")
        return f"Error: {str(e)}"


@function_tool
async def remove_shopping_list_item(item_id: str) -> str:
    """Remove an item from the shopping list"""
    try:
        success = await kitchenowl_service.remove_shopping_list_entry(item_id)
        if success:
            return f"Removed item {item_id} from shopping list"
        else:
            return f"Failed to remove item {item_id}"
    except Exception as e:
        logger.error(f"Error removing shopping list item: {e}")
        return f"Error: {str(e)}"


@function_tool
async def add_shopping_list_items_batch(items: List[ShoppingListItem]) -> str:
    """Add multiple items to the shopping list in batch"""
    try:
        # Convert Pydantic models to dicts for the service
        items_dicts = [{"name": item.name, "description": item.description} for item in items]
        entries = await kitchenowl_service.batch_create_shopping_list_entries(items_dicts)
        if entries:
            result = f"Added {len(entries)} items to shopping list:\n"
            for entry in entries:
                result += f"- {entry.name}\n"
            return result
        else:
            return "Failed to add items to shopping list"
    except Exception as e:
        logger.error(f"Error adding shopping list items in batch: {e}")
        return f"Error: {str(e)}"


@function_tool
async def update_shopping_list_items_batch(updates: List[ShoppingListItemUpdate]) -> str:
    """Update multiple shopping list items in batch (description only)"""
    try:
        # Convert Pydantic models to dicts for the service
        updates_dicts = [{"id": update.id, "description": update.description} for update in updates]
        entries = await kitchenowl_service.batch_update_shopping_list_entries(updates_dicts)
        if entries:
            result = f"Updated {len(entries)} items in shopping list:\n"
            for entry in entries:
                result += f"- {entry.name}: {entry.description}\n"
            return result
        else:
            return "Failed to update items in shopping list"
    except Exception as e:
        logger.error(f"Error updating shopping list items in batch: {e}")
        return f"Error: {str(e)}"

