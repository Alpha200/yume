import logging
import os
import aiohttp
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# KitchenOwl API configuration
KITCHENOWL_API_URL = os.getenv("KITCHENOWL_API_URL", "http://localhost:8080/api")
KITCHENOWL_API_KEY = os.getenv("KITCHENOWL_API_KEY", "")
KITCHENOWL_HOUSEHOLD_ID = os.getenv("KITCHENOWL_HOUSEHOLD_ID", "1")


@dataclass
class ShoppingListEntry:
    """A shopping list entry"""
    id: str
    name: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }


@dataclass
class RecipeItem:
    """An ingredient/item in a recipe"""
    id: int
    name: str
    description: Optional[str] = None
    optional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "optional": self.optional
        }


@dataclass
class Recipe:
    """A recipe from KitchenOwl"""
    id: int
    name: str
    description: Optional[str] = None
    items: Optional[List[RecipeItem]] = None
    cook_time: int = 0
    prep_time: int = 0
    time: int = 0
    yields: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "items": [item.to_dict() for item in self.items] if self.items else None,
            "cook_time": self.cook_time,
            "prep_time": self.prep_time,
            "time": self.time,
            "yields": self.yields
        }


class KitchenOwlService:
    """Service for interacting with KitchenOwl API"""

    def __init__(self):
        self.base_url = KITCHENOWL_API_URL
        self.api_key = KITCHENOWL_API_KEY
        self.household_id = KITCHENOWL_HOUSEHOLD_ID

    async def fetch_shopping_list(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the current shopping list with all its items

        Returns:
            Dict with shopping list data (id, name, items, recentItems, etc.) if found, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.get(
                    f"{self.base_url}/household/{self.household_id}/shoppinglist",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        shopping_lists = await response.json()
                        if shopping_lists:
                            # Return the first (default) shopping list
                            return shopping_lists[0]
                        else:
                            logger.warning("No shopping lists found")
                            return None
                    else:
                        logger.error(f"Failed to fetch shopping list: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching shopping list: {e}")
            return None

    async def create_shopping_list_entry(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Optional[ShoppingListEntry]:
        """
        Create a new shopping list entry

        Args:
            name: Name of the item
            description: Description of the item (e.g., amount information)

        Returns:
            ShoppingListEntry if successful, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                payload = {
                    "name": name,
                    "description": description or ""
                }

                async with session.post(
                    f"{self.base_url}/shoppinglist/{self.household_id}/add-item-by-name",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return ShoppingListEntry(
                            id=str(data.get("id")),
                            name=data.get("name"),
                            description=data.get("description")
                        )
                    else:
                        logger.error(f"Failed to create shopping list entry: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error creating shopping list entry: {e}")
            return None

    async def update_shopping_list_entry(
        self,
        entry_id: str,
        description: str
    ) -> Optional[ShoppingListEntry]:
        """
        Update an existing shopping list entry (description only)

        Args:
            entry_id: ID of the entry to update
            description: New description

        Returns:
            Updated ShoppingListEntry if successful, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                payload = {"description": description}

                async with session.put(
                    f"{self.base_url}/shoppinglist/{self.household_id}/item/{entry_id}",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ShoppingListEntry(
                            id=str(data.get("id")),
                            name=data.get("name"),
                            description=data.get("description")
                        )
                    else:
                        logger.error(f"Failed to update shopping list entry: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error updating shopping list entry: {e}")
            return None

    async def remove_shopping_list_entry(self, entry_id: str) -> bool:
        """
        Remove a shopping list entry

        Args:
            entry_id: ID of the entry to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.delete(
                    f"{self.base_url}/shoppinglist/{self.household_id}/item/{entry_id}",
                    headers=headers
                ) as response:
                    if response.status in [200, 204]:
                        return True
                    else:
                        logger.error(f"Failed to remove shopping list entry: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error removing shopping list entry: {e}")
            return False

    async def batch_create_shopping_list_entries(
        self,
        items: List[Dict[str, Optional[str]]]
    ) -> List[ShoppingListEntry]:
        """
        Create multiple shopping list entries in batch

        Args:
            items: List of dicts with 'name' and optional 'description' keys

        Returns:
            List of created ShoppingListEntry objects (empty list if all fail)
        """
        created_entries = []
        for item in items:
            entry = await self.create_shopping_list_entry(
                name=item.get("name", ""),
                description=item.get("description")
            )
            if entry:
                created_entries.append(entry)
            else:
                logger.warning(f"Failed to create entry: {item}")

        return created_entries

    async def batch_update_shopping_list_entries(
        self,
        updates: List[Dict[str, Optional[str]]]
    ) -> List[ShoppingListEntry]:
        """
        Update multiple shopping list entries in batch (description only)

        Args:
            updates: List of dicts with 'id' and 'description' keys

        Returns:
            List of updated ShoppingListEntry objects (empty list if all fail)
        """
        updated_entries = []
        for update in updates:
            entry_id = update.get("id")
            description = update.get("description")
            if not entry_id:
                logger.warning("Update missing required 'id' key")
                continue
            if description is None:
                logger.warning(f"Update for {entry_id} missing required 'description' key")
                continue

            entry = await self.update_shopping_list_entry(
                entry_id=entry_id,
                description=description
            )
            if entry:
                updated_entries.append(entry)
            else:
                logger.warning(f"Failed to update entry: {update}")

        return updated_entries

    async def fetch_recipe_names(self) -> List[Dict[str, Any]]:
        """
        Fetch all recipe names and IDs

        Returns:
            List of dicts with recipe id and name
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.get(
                    f"{self.base_url}/household/{self.household_id}/recipe",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        recipes = await response.json()
                        return [
                            {"id": recipe["id"], "name": recipe["name"]}
                            for recipe in recipes
                        ]
                    else:
                        logger.error(f"Failed to fetch recipe names: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching recipe names: {e}")
            return []

    async def fetch_recipe(self, recipe_id: int) -> Optional[Recipe]:
        """
        Fetch a full recipe by ID

        Args:
            recipe_id: ID of the recipe to fetch

        Returns:
            Recipe object if found, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.get(
                    f"{self.base_url}/household/{self.household_id}/recipe",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        recipes = await response.json()
                        for recipe_data in recipes:
                            if recipe_data["id"] == recipe_id:
                                items = None
                                if recipe_data.get("items"):
                                    items = [
                                        RecipeItem(
                                            id=item["id"],
                                            name=item["name"],
                                            description=item.get("description"),
                                            optional=item.get("optional", False)
                                        )
                                        for item in recipe_data["items"]
                                    ]

                                return Recipe(
                                    id=recipe_data["id"],
                                    name=recipe_data["name"],
                                    description=recipe_data.get("description"),
                                    items=items,
                                    cook_time=recipe_data.get("cook_time", 0),
                                    prep_time=recipe_data.get("prep_time", 0),
                                    time=recipe_data.get("time", 0),
                                    yields=recipe_data.get("yields")
                                )
                        logger.warning(f"Recipe with ID {recipe_id} not found")
                        return None
                    else:
                        logger.error(f"Failed to fetch recipe: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching recipe: {e}")
            return None


# Create a singleton instance
kitchenowl_service = KitchenOwlService()

