import datetime
import os
import uuid
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from components.timezone_utils import now_user_tz, from_isoformat_user_tz
from components.logging_manager import logging_manager

logger = logging_manager


@dataclass
class DayPlanItem:
    """A single item/activity in the day plan"""
    id: str
    title: str
    description: Optional[str]
    start_time: Optional[datetime.datetime]  # Expected start time
    end_time: Optional[datetime.datetime]  # Expected end time
    source: Literal["memory", "calendar", "user_input"]  # Where this prediction came from
    confidence: Literal["low", "medium", "high"]  # Confidence level
    location: Optional[str]  # Expected location
    tags: List[str]  # Categories like "work", "personal", "exercise", etc.
    metadata: Dict  # Additional source-specific data


@dataclass
class DayPlan:
    """Complete plan for a single day"""
    id: str
    date: datetime.date  # The date this plan is for
    items: List[DayPlanItem]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    summary: Optional[str]  # AI-generated summary of the day


class DayPlannerService:
    """Service for managing daily plans and predictions"""
    
    def __init__(self, 
                 mongo_uri: str = None,
                 db_name: str = "yume",
                 collection_name: str = "day_plans"):
        """
        Initialize day planner service with MongoDB.
        
        Args:
            mongo_uri: MongoDB connection string (default: env var MONGODB_URI or local)
            db_name: Database name
            collection_name: Collection name for day plans
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.log("Day planner connected to MongoDB successfully")
        except ServerSelectionTimeoutError:
            logger.log(f"Day planner failed to connect to MongoDB at {self.mongo_uri}")
            raise
    
    def _item_to_dict(self, item: DayPlanItem) -> dict:
        """Convert DayPlanItem to dictionary for MongoDB"""
        return {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "start_time": item.start_time.isoformat() if item.start_time else None,
            "end_time": item.end_time.isoformat() if item.end_time else None,
            "source": item.source,
            "confidence": item.confidence,
            "location": item.location,
            "tags": item.tags,
            "metadata": item.metadata
        }
    
    def _dict_to_item(self, data: dict) -> DayPlanItem:
        """Convert dictionary to DayPlanItem"""
        return DayPlanItem(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            start_time=from_isoformat_user_tz(data["start_time"]) if data.get("start_time") else None,
            end_time=from_isoformat_user_tz(data["end_time"]) if data.get("end_time") else None,
            source=data["source"],
            confidence=data.get("confidence", 0.5),
            location=data.get("location"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
    
    def _plan_to_document(self, plan: DayPlan) -> dict:
        """Convert DayPlan to MongoDB document"""
        return {
            "_id": plan.id,
            "date": plan.date.isoformat(),
            "items": [self._item_to_dict(item) for item in plan.items],
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
            "summary": plan.summary
        }
    
    def _document_to_plan(self, doc: dict) -> DayPlan:
        """Convert MongoDB document to DayPlan"""
        return DayPlan(
            id=doc["_id"],
            date=datetime.date.fromisoformat(doc["date"]),
            items=[self._dict_to_item(item_data) for item_data in doc.get("items", [])],
            created_at=from_isoformat_user_tz(doc["created_at"]),
            updated_at=from_isoformat_user_tz(doc["updated_at"]),
            summary=doc.get("summary")
        )
    
    def get_plan_for_date(self, date: datetime.date) -> Optional[DayPlan]:
        """Get the day plan for a specific date"""
        try:
            doc = self.collection.find_one({"date": date.isoformat()})
            if doc:
                return self._document_to_plan(doc)
            return None
        except Exception as e:
            logger.log(f"Error fetching day plan for {date}: {e}")
            return None
    
    def get_plan_for_today(self) -> Optional[DayPlan]:
        """Get the day plan for today"""
        today = now_user_tz().date()
        return self.get_plan_for_date(today)
    
    def save_plan(self, plan: DayPlan):
        """Save or update a day plan"""
        try:
            doc = self._plan_to_document(plan)
            self.collection.replace_one({"_id": plan.id}, doc, upsert=True)
            logger.log(f"Saved day plan for {plan.date}")
        except Exception as e:
            logger.log(f"Error saving day plan: {e}")
            raise
    
    def create_or_update_plan(
        self,
        date: datetime.date,
        items: List[DayPlanItem],
        summary: Optional[str] = None,
        plan_id: Optional[str] = None
    ) -> str:
        """Create a new plan or update an existing one for a specific date"""
        
        # Check if plan already exists for this date
        existing_plan = self.get_plan_for_date(date)
        
        if existing_plan:
            plan_id = existing_plan.id
            created_at = existing_plan.created_at
        else:
            plan_id = plan_id or str(uuid.uuid4())
            created_at = now_user_tz()
        
        plan = DayPlan(
            id=plan_id,
            date=date,
            items=items,
            created_at=created_at,
            updated_at=now_user_tz(),
            summary=summary
        )
        
        self.save_plan(plan)
        return plan_id
    
    def add_item_to_plan(
        self,
        date: datetime.date,
        item: DayPlanItem
    ) -> str:
        """Add a single item to an existing plan or create a new plan"""
        existing_plan = self.get_plan_for_date(date)
        
        if existing_plan:
            # Add to existing items
            existing_plan.items.append(item)
            existing_plan.updated_at = now_user_tz()
            self.save_plan(existing_plan)
            return existing_plan.id
        else:
            # Create new plan with this item
            return self.create_or_update_plan(date, [item])
    
    def remove_item_from_plan(
        self,
        date: datetime.date,
        item_id: str
    ) -> bool:
        """Remove a specific item from a day plan"""
        existing_plan = self.get_plan_for_date(date)
        
        if not existing_plan:
            return False
        
        # Filter out the item
        original_count = len(existing_plan.items)
        existing_plan.items = [item for item in existing_plan.items if item.id != item_id]
        
        if len(existing_plan.items) < original_count:
            existing_plan.updated_at = now_user_tz()
            self.save_plan(existing_plan)
            return True
        
        return False
    
    def update_item_in_plan(
        self,
        date: datetime.date,
        item_id: str,
        updated_item: DayPlanItem
    ) -> bool:
        """Update a specific item in a day plan"""
        existing_plan = self.get_plan_for_date(date)
        
        if not existing_plan:
            return False
        
        # Find and update the item
        for i, item in enumerate(existing_plan.items):
            if item.id == item_id:
                existing_plan.items[i] = updated_item
                existing_plan.updated_at = now_user_tz()
                self.save_plan(existing_plan)
                return True
        
        return False
    
    def get_plans_for_date_range(
        self,
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[DayPlan]:
        """Get all day plans within a date range"""
        try:
            docs = self.collection.find({
                "date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }).sort("date", 1)
            
            return [self._document_to_plan(doc) for doc in docs]
        except Exception as e:
            logger.log(f"Error fetching day plans for range {start_date} to {end_date}: {e}")
            return []
    
    def delete_plan(self, date: datetime.date) -> bool:
        """Delete a day plan for a specific date"""
        try:
            result = self.collection.delete_one({"date": date.isoformat()})
            return result.deleted_count > 0
        except Exception as e:
            logger.log(f"Error deleting day plan for {date}: {e}")
            return False
    
    def get_formatted_plan(self, date: datetime.date) -> str:
        """Get a formatted string representation of a day plan"""
        plan = self.get_plan_for_date(date)
        
        if not plan:
            return f"No plan found for {date.strftime('%Y-%m-%d')}"
        
        output = f"Day Plan for {date.strftime('%A, %B %d, %Y')}\n"
        output += "=" * 50 + "\n\n"
        
        if plan.summary:
            output += f"Summary: {plan.summary}\n\n"
        
        if not plan.items:
            output += "No activities planned.\n"
        else:
            # Sort items by start time
            sorted_items = sorted(
                plan.items,
                key=lambda x: x.start_time if x.start_time else datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)
            )
            
            for item in sorted_items:
                output += f"• {item.title}\n"
                if item.description:
                    output += f"  Description: {item.description}\n"
                if item.start_time:
                    time_str = item.start_time.strftime('%H:%M')
                    if item.end_time:
                        time_str += f" - {item.end_time.strftime('%H:%M')}"
                    output += f"  Time: {time_str}\n"
                if item.location:
                    output += f"  Location: {item.location}\n"
                output += f"  Source: {item.source}"
                if item.confidence < 1.0:
                    output += f" (confidence: {item.confidence:.0%})"
                output += "\n"
                if item.tags:
                    output += f"  Tags: {', '.join(item.tags)}\n"
                output += "\n"
        
        output += f"\nLast updated: {plan.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return output
    
    async def update_plan_from_agent_result(
        self,
        date: datetime.date,
        agent_result
    ) -> tuple[str, bool]:
        """
        Update a day plan from a day planner agent result.
        Handles conversion of activities to DayPlanItem objects.
        
        Args:
            date: The date to update the plan for
            agent_result: DayPlannerResult from the agent
            
        Returns:
            Tuple of (plan_id, changed) where changed indicates if the plan was modified
        """
        # Get existing plan to compare
        existing_plan = self.get_plan_for_date(date)
        
        items = []
        for activity in agent_result.activities:
            item = DayPlanItem(
                id=str(uuid.uuid4()),
                title=activity.get("title", "Untitled"),
                description=activity.get("description"),
                start_time=from_isoformat_user_tz(activity["start_time"]) if activity.get("start_time") else None,
                end_time=from_isoformat_user_tz(activity["end_time"]) if activity.get("end_time") else None,
                source=activity.get("source", "user_input"),
                confidence=activity.get("confidence", "medium"),
                location=activity.get("location"),
                tags=activity.get("tags", []),
                metadata=activity.get("metadata", {})
            )
            items.append(item)
        
        # Determine if plan changed
        changed = self._plan_has_changed(existing_plan, items, agent_result.summary)
        
        # Save the updated plan
        plan_id = self.create_or_update_plan(
            date=date,
            items=items,
            summary=agent_result.summary
        )
        
        logger.log(f"Updated day plan for {date} from agent result with {len(items)} activities (changed: {changed})")
        return plan_id, changed
    
    def _plan_has_changed(
        self,
        existing_plan: Optional[DayPlan],
        new_items: List[DayPlanItem],
        new_summary: Optional[str]
    ) -> bool:
        """Check if the new plan differs from the existing one"""
        if not existing_plan:
            return len(new_items) > 0  # Changed if new plan has items
        
        # Compare number of items
        if len(existing_plan.items) != len(new_items):
            return True
        
        # Compare summary
        if existing_plan.summary != new_summary:
            return True
        
        # Compare items (simplified check - just titles and times)
        existing_titles = sorted([item.title for item in existing_plan.items])
        new_titles = sorted([item.title for item in new_items])
        if existing_titles != new_titles:
            return True
        
        # Check start times
        existing_times = sorted([item.start_time.isoformat() if item.start_time else "" for item in existing_plan.items])
        new_times = sorted([item.start_time.isoformat() if item.start_time else "" for item in new_items])
        if existing_times != new_times:
            return True
        
        return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


# Global instance
day_planner_service = DayPlannerService()
