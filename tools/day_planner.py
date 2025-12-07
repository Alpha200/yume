import datetime
import json
from typing import Optional

from agents import function_tool
from services.day_planner import day_planner_service, DayPlanItem
from components.timezone_utils import from_isoformat_user_tz, now_user_tz


@function_tool
def get_day_plan(date: Optional[str] = None) -> str:
    """Get the day plan for a specific date (YYYY-MM-DD) or today if not specified"""
    if date:
        try:
            plan_date = datetime.date.fromisoformat(date)
        except ValueError:
            return f"Error: Invalid date format '{date}'. Please use YYYY-MM-DD format."
    else:
        plan_date = now_user_tz().date()
    
    return day_planner_service.get_formatted_plan(plan_date)


@function_tool
def update_day_plan(
    date: str,
    activities_json: str,
    summary: str
) -> str:
    """
    Create or update a complete day plan for a specific date with predicted activities.
    
    Args:
        date: Date in YYYY-MM-DD format
        activities_json: JSON string containing list of activities. Each activity should have:
            - title (required): Activity name
            - description (optional): Additional details
            - start_time (optional): ISO format YYYY-MM-DD HH:MM:SS
            - end_time (optional): ISO format YYYY-MM-DD HH:MM:SS
            - source: "memory", "calendar", or "user_input"
            - confidence: "low", "medium", or "high"
            - location (optional): Where the activity takes place
            - tags (optional): List of category strings
            - metadata (optional): Dictionary of additional info
        summary: Brief natural language overview of the day (2-3 sentences)
    
    Returns:
        Success or error message
    """
    try:
        plan_date = datetime.date.fromisoformat(date)
    except ValueError:
        return f"Error: Invalid date format '{date}'. Please use YYYY-MM-DD format."
    
    # Parse activities JSON
    try:
        activities = json.loads(activities_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON format for activities: {e}"
    
    if not isinstance(activities, list):
        return "Error: activities_json must be a JSON array"
    
    # Convert activities to DayPlanItem objects
    items = []
    import uuid
    
    for idx, activity in enumerate(activities):
        if not isinstance(activity, dict):
            return f"Error: Activity at index {idx} must be a dictionary"
        
        if "title" not in activity:
            return f"Error: Activity at index {idx} missing required 'title' field"
        
        # Parse times if provided
        parsed_start = None
        parsed_end = None
        
        if activity.get("start_time"):
            try:
                parsed_start = from_isoformat_user_tz(activity["start_time"])
            except (ValueError, TypeError) as e:
                return f"Error: Invalid start_time in activity {idx}: {e}"
        
        if activity.get("end_time"):
            try:
                parsed_end = from_isoformat_user_tz(activity["end_time"])
            except (ValueError, TypeError) as e:
                return f"Error: Invalid end_time in activity {idx}: {e}"
        
        # Validate source
        source = activity.get("source", "user_input")
        if source not in ["memory", "calendar", "user_input"]:
            return f"Error: Invalid source '{source}' in activity {idx}"
        
        # Validate confidence
        confidence = activity.get("confidence", "medium")
        if confidence not in ["low", "medium", "high"]:
            return f"Error: Invalid confidence '{confidence}' in activity {idx}"
        
        item = DayPlanItem(
            id=str(uuid.uuid4()),
            title=activity["title"],
            description=activity.get("description"),
            start_time=parsed_start,
            end_time=parsed_end,
            source=source,
            confidence=confidence,
            location=activity.get("location"),
            tags=activity.get("tags", []),
            metadata=activity.get("metadata", {})
        )
        items.append(item)
    
    # Create or update the plan
    plan_id = day_planner_service.create_or_update_plan(
        date=plan_date,
        items=items,
        summary=summary
    )
    
    
    return f"Successfully updated day plan for {date} with {len(items)} activities (plan ID: {plan_id})"
