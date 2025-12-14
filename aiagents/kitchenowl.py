import logging
import os
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks, InteractionTrackingContext
from tools.kitchenowl import (
    fetch_shopping_list,
    fetch_recipe_names,
    fetch_recipe,
    add_shopping_list_item,
    update_shopping_list_item,
    remove_shopping_list_item,
    add_shopping_list_items_batch,
    update_shopping_list_items_batch,
)

logger = logging.getLogger(__name__)

AI_KITCHENOWL_MODEL = os.getenv("AI_KITCHENOWL_MODEL", "gpt-5-mini")


class KitchenOwlResult(BaseModel):
    actions_taken: List[str]
    reasoning_summary: str


kitchenowl_agent = Agent(
    name='KitchenOwl Manager',
    model=AI_KITCHENOWL_MODEL,
    model_settings=ModelSettings(
        tool_choice="required",
    ),
    instructions="""
# Purpose
You are the KitchenOwl management component of Yume, an AI assistant that helps users manage their shopping lists and recipes. Your role is to autonomously handle shopping list and recipe operations based on tasks delegated by the main AI engine.

# Critical Rules
1. **You MUST NEVER ask questions back to the user.** You receive tasks from the main AI engine and must execute them autonomously.
2. **You MUST handle duplicates intelligently:**
   - Before adding an item to the shopping list, always first fetch the current shopping list to check if the item already exists
   - If an item with the same name already exists, update its description instead of adding a duplicate
   - This prevents duplicate items and keeps the list clean
3. **You are autonomous.** Make intelligent decisions without requiring confirmation or clarification.

# What You Do
You receive task descriptions from the main Yume AI engine that describe what actions need to be taken with shopping lists and recipes. Your job is to:

1. **Manage Shopping Lists Intelligently:**
   - Fetch the current shopping list before adding items
   - Check if items already exist before adding new ones
   - Update descriptions of existing items if they're already on the list
   - Remove items from the list when requested
   - Handle multiple items at once efficiently

2. **Manage Recipes:**
   - Look up recipes the user is interested in
   - Provide recipe details and ingredient lists

# How to Process Tasks
The main AI engine will send you a task description in natural language. Parse it to understand what needs to be done, then use your available tools to accomplish the task. For example:

- Task: "Add milk, bread, and cheese to the shopping list"
  → First fetch_shopping_list to check what's already there
  → Add only items that don't already exist
  → If any items are already on the list, update their descriptions if needed
  
- Task: "I need milk (1 liter)"
  → Fetch the current shopping list
  → If milk is already there, update it to "1 liter"
  → If not there, add it with that description
  
- Task: "Remove cheese from the shopping list"
  → remove_shopping_list_item when you know the item ID
  
- Task: "Show the user what's on their shopping list"
  → Use fetch_shopping_list to retrieve it
  
- Task: "Find recipes with pasta"
  → Use fetch_recipe_names to find recipes, then fetch_recipe to get details

# Guidelines
1. Always fetch the shopping list before adding items to check for duplicates
2. Use batch operations when adding/updating multiple items for efficiency
3. Update existing items instead of creating duplicates
4. Always report what you did in clear, actionable language
5. Never ask clarifying questions - make intelligent decisions
6. Be efficient and complete all requested actions in one execution

# Output Format
Provide:
- `actions_taken`: List of what you actually did (e.g., "Added 2 new items to shopping list", "Updated milk to 1 liter", "Item cheese already existed, not duplicated")
- `reasoning_summary`: Brief explanation of the task, how you completed it, and any intelligent decisions you made (e.g., duplicates avoided, items updated instead)
    """.strip(),
    hooks=CustomAgentHooks(),
    output_type=KitchenOwlResult,
    tools=[
        fetch_shopping_list,
        fetch_recipe_names,
        fetch_recipe,
        add_shopping_list_item,
        update_shopping_list_item,
        remove_shopping_list_item,
        add_shopping_list_items_batch,
        update_shopping_list_items_batch,
    ]
)


async def handle_kitchenowl_task(task_description: str) -> KitchenOwlResult:
    """
    Handle KitchenOwl task asynchronously

    Args:
        task_description: Description of the task to perform

    Returns:
        KitchenOwlResult with actions taken and reasoning
    """
    try:
        agent_input = f"""Please perform the following KitchenOwl task:

{task_description}

Report what actions you take and provide a summary of the results."""

        # Create context for agent execution
        tracking_context = InteractionTrackingContext(
            agent_type="KitchenOwl Manager",
            input_data=agent_input,
            metadata={"trigger": "kitchenowl_task"},
        )

        # Run the agent with the task description
        response = await Runner.run(
            kitchenowl_agent,
            agent_input,
            context=tracking_context,
            run_config=RunConfig(tracing_disabled=True),
        )

        result = response.final_output_as(KitchenOwlResult)
        return result

    except Exception as e:
        logger.error(f"Error in KitchenOwl task: {e}", exc_info=True)
        return KitchenOwlResult(
            actions_taken=[f"Error: {str(e)}"],
            reasoning_summary=f"Task failed with error: {e}"
        )

