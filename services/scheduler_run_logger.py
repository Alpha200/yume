import logging
import datetime
import os
from typing import Optional, List, Literal
from dataclasses import dataclass, asdict
from enum import Enum

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from components.timezone_utils import now_user_tz, to_user_tz

logger = logging.getLogger(__name__)


class SchedulerRunStatus(str, Enum):
    """Status of a scheduler run"""
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SchedulerRunLog:
    """Log entry for a scheduler run"""
    id: str
    scheduled_time: datetime.datetime  # When the run was scheduled to occur
    actual_execution_time: Optional[datetime.datetime]  # When it actually ran (None if not yet executed)
    reason: str  # Why this run was scheduled
    topic: str  # Topic/subject of the interaction
    status: SchedulerRunStatus = SchedulerRunStatus.SCHEDULED
    error_message: Optional[str] = None  # Error details if status is FAILED
    execution_duration_ms: Optional[int] = None  # How long the execution took in milliseconds
    ai_response: Optional[str] = None  # The response/output from the AI engine
    details: Optional[str] = None  # Additional context/information provided by the scheduler
    metadata: Optional[dict] = None  # Additional context data
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None


class SchedulerRunLogger:
    """Logger for AI scheduler runs - persists to MongoDB"""
    
    def __init__(self, 
                 mongo_uri: str = None,
                 db_name: str = "yume",
                 collection_name: str = "scheduler_runs"):
        """
        Initialize MongoDB scheduler run logger.
        
        Args:
            mongo_uri: MongoDB connection string (default: env var MONGODB_URI or local)
            db_name: Database name
            collection_name: Collection name for scheduler runs
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
            # Create indexes for efficient querying
            self._create_indexes()
            logger.info("Connected to MongoDB scheduler run logger successfully")
        except ServerSelectionTimeoutError:
            logger.error(f"Failed to connect to MongoDB at {self.mongo_uri}")
            raise
    
    def _create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            # Index on updated_at for sorting recent runs
            self.collection.create_index("updated_at")
            # Index on status for filtering
            self.collection.create_index("status")
            # Index on created_at for temporal queries
            self.collection.create_index("created_at")
            # Compound index for recent runs by status
            self.collection.create_index([("status", 1), ("updated_at", -1)])
            logger.debug("Created indexes for scheduler run logs")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def _log_entry_to_document(self, log_entry: SchedulerRunLog) -> dict:
        """Convert scheduler run log to MongoDB document"""
        doc = asdict(log_entry)
        # Ensure enums are converted to strings
        if "status" in doc and isinstance(doc["status"], SchedulerRunStatus):
            doc["status"] = doc["status"].value
        return doc
    
    def _document_to_log_entry(self, doc: dict) -> SchedulerRunLog:
        """Convert MongoDB document to scheduler run log"""
        # Convert status string back to enum
        if "status" in doc and isinstance(doc["status"], str):
            doc["status"] = SchedulerRunStatus(doc["status"])
        # Remove MongoDB's _id field
        doc.pop("_id", None)
        return SchedulerRunLog(**doc)
    
    def log_scheduled_run(self, run_id: str, scheduled_time: datetime.datetime, 
                         reason: str, topic: str, metadata: dict = None, details: str = None) -> SchedulerRunLog:
        """
        Log a newly scheduled reminder run.
        
        Args:
            run_id: Unique identifier for this run
            scheduled_time: When the run is scheduled to execute
            reason: Why this run was scheduled (e.g., "User preference check-in")
            topic: Topic of the interaction (e.g., "daily_summary")
            metadata: Optional additional context data
            details: Optional detailed information about this run for the AI engine
        
        Returns:
            The created SchedulerRunLog entry
        """
        now = now_user_tz()
        log_entry = SchedulerRunLog(
            id=run_id,
            scheduled_time=to_user_tz(scheduled_time),
            actual_execution_time=None,
            reason=reason,
            topic=topic,
            status=SchedulerRunStatus.SCHEDULED,
            details=details,
            metadata=metadata or {},
            created_at=now,
            updated_at=now
        )
        
        try:
            doc = self._log_entry_to_document(log_entry)
            result = self.collection.insert_one(doc)
            logger.info(f"Logged scheduled run {run_id}: {reason}")
            return log_entry
        except Exception as e:
            logger.error(f"Error logging scheduled run: {e}")
            raise
    
    def log_execution_start(self, run_id: str) -> Optional[SchedulerRunLog]:
        """
        Log the start of a scheduled run execution.
        
        Args:
            run_id: ID of the run being executed
        
        Returns:
            Updated SchedulerRunLog entry or None if not found
        """
        try:
            now = now_user_tz()
            result = self.collection.find_one_and_update(
                {"id": run_id},
                {
                    "$set": {
                        "status": SchedulerRunStatus.EXECUTING.value,
                        "actual_execution_time": now,
                        "updated_at": now
                    }
                },
                return_document=True
            )
            if result:
                logger.info(f"Logged execution start for run {run_id}")
                return self._document_to_log_entry(result)
            else:
                logger.warning(f"Run {run_id} not found in logs")
                return None
        except Exception as e:
            logger.error(f"Error logging execution start: {e}")
            return None
    
    def log_execution_completion(self, run_id: str, duration_ms: int, 
                                ai_response: str = None) -> Optional[SchedulerRunLog]:
        """
        Log successful completion of a run.
        
        Args:
            run_id: ID of the completed run
            duration_ms: How long execution took in milliseconds
            ai_response: Optional response/output from the AI engine
        
        Returns:
            Updated SchedulerRunLog entry or None if not found
        """
        try:
            now = now_user_tz()
            update_data = {
                "status": SchedulerRunStatus.COMPLETED.value,
                "execution_duration_ms": duration_ms,
                "updated_at": now
            }
            if ai_response:
                update_data["ai_response"] = ai_response
            
            result = self.collection.find_one_and_update(
                {"id": run_id},
                {"$set": update_data},
                return_document=True
            )
            if result:
                logger.info(f"Logged successful completion for run {run_id} ({duration_ms}ms)")
                return self._document_to_log_entry(result)
            else:
                logger.warning(f"Run {run_id} not found in logs")
                return None
        except Exception as e:
            logger.error(f"Error logging execution completion: {e}")
            return None
    
    def log_execution_failure(self, run_id: str, error_message: str, 
                             duration_ms: int = None) -> Optional[SchedulerRunLog]:
        """
        Log failed execution of a run.
        
        Args:
            run_id: ID of the failed run
            error_message: Description of the error
            duration_ms: Optional how long the failed execution took
        
        Returns:
            Updated SchedulerRunLog entry or None if not found
        """
        try:
            now = now_user_tz()
            update_data = {
                "status": SchedulerRunStatus.FAILED.value,
                "error_message": error_message,
                "updated_at": now
            }
            if duration_ms is not None:
                update_data["execution_duration_ms"] = duration_ms
            
            result = self.collection.find_one_and_update(
                {"id": run_id},
                {"$set": update_data},
                return_document=True
            )
            if result:
                logger.warning(f"Logged failure for run {run_id}: {error_message}")
                return self._document_to_log_entry(result)
            else:
                logger.warning(f"Run {run_id} not found in logs")
                return None
        except Exception as e:
            logger.error(f"Error logging execution failure: {e}")
            return None
    
    def get_run(self, run_id: str) -> Optional[SchedulerRunLog]:
        """Get a specific run log by ID"""
        try:
            doc = self.collection.find_one({"id": run_id})
            if doc:
                return self._document_to_log_entry(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting run {run_id}: {e}")
            return None
    
    def cancel_previous_scheduled_runs(self) -> int:
        """
        Cancel all currently scheduled runs (those with status=scheduled).
        This ensures only one scheduled reminder can exist at a time.
        
        Returns:
            Number of runs cancelled
        """
        try:
            now = now_user_tz()
            result = self.collection.update_many(
                {"status": SchedulerRunStatus.SCHEDULED.value},
                {
                    "$set": {
                        "status": SchedulerRunStatus.CANCELLED.value,
                        "updated_at": now
                    }
                }
            )
            if result.modified_count > 0:
                logger.info(f"Cancelled {result.modified_count} previously scheduled runs")
            return result.modified_count
        except Exception as e:
            logger.error(f"Error cancelling previous scheduled runs: {e}")
            return 0
    
    def get_recent_runs(self, limit: int = 20, status: SchedulerRunStatus | List[SchedulerRunStatus] = None) -> List[SchedulerRunLog]:
        """
        Get recent scheduler runs.
        
        Args:
            limit: Maximum number of runs to return
            status: Optional filter by status (single SchedulerRunStatus or list of statuses)
                   Supported: SCHEDULED, EXECUTING, COMPLETED, FAILED
        
        Returns:
            List of SchedulerRunLog entries, most recent first
        """
        try:
            query = {}
            if status:
                # Handle both single status and list of statuses
                if isinstance(status, list):
                    status_values = [s.value if isinstance(s, SchedulerRunStatus) else s for s in status]
                    query["status"] = {"$in": status_values}
                else:
                    query["status"] = status.value if isinstance(status, SchedulerRunStatus) else status
            
            docs = self.collection.find(query).sort("updated_at", -1).limit(limit)
            return [self._document_to_log_entry(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting recent runs: {e}")
            return []
    
    def get_runs_by_topic(self, topic: str, limit: int = 20) -> List[SchedulerRunLog]:
        """Get recent runs for a specific topic"""
        try:
            docs = self.collection.find({"topic": topic}).sort("created_at", -1).limit(limit)
            return [self._document_to_log_entry(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting runs by topic: {e}")
            return []
    
    def get_completed_runs_count(self, days: int = 7) -> int:
        """Get count of completed runs in the last N days"""
        try:
            cutoff_date = now_user_tz() - datetime.timedelta(days=days)
            count = self.collection.count_documents({
                "status": SchedulerRunStatus.COMPLETED.value,
                "created_at": {"$gte": cutoff_date}
            })
            return count
        except Exception as e:
            logger.error(f"Error getting completed runs count: {e}")
            return 0
    
    def get_failed_runs(self, limit: int = 20) -> List[SchedulerRunLog]:
        """Get recent failed runs for debugging"""
        try:
            docs = self.collection.find({"status": SchedulerRunStatus.FAILED.value}).sort("created_at", -1).limit(limit)
            return [self._document_to_log_entry(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting failed runs: {e}")
            return []
    
    def get_run_statistics(self, days: int = 7) -> dict:
        """Get statistics about scheduler runs over a period"""
        try:
            cutoff_date = now_user_tz() - datetime.timedelta(days=days)
            
            total_runs = self.collection.count_documents({
                "created_at": {"$gte": cutoff_date}
            })
            
            completed_runs = self.collection.count_documents({
                "status": SchedulerRunStatus.COMPLETED.value,
                "created_at": {"$gte": cutoff_date}
            })
            
            failed_runs = self.collection.count_documents({
                "status": SchedulerRunStatus.FAILED.value,
                "created_at": {"$gte": cutoff_date}
            })
            
            scheduled_runs = self.collection.count_documents({
                "status": SchedulerRunStatus.SCHEDULED.value,
                "created_at": {"$gte": cutoff_date}
            })
            
            # Calculate average execution duration (excluding failed runs without duration)
            avg_duration_pipeline = [
                {
                    "$match": {
                        "status": SchedulerRunStatus.COMPLETED.value,
                        "execution_duration_ms": {"$exists": True, "$ne": None},
                        "created_at": {"$gte": cutoff_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_duration": {"$avg": "$execution_duration_ms"}
                    }
                }
            ]
            
            avg_result = list(self.collection.aggregate(avg_duration_pipeline))
            avg_duration = avg_result[0]["avg_duration"] if avg_result else 0
            
            return {
                "period_days": days,
                "total_runs": total_runs,
                "completed_runs": completed_runs,
                "failed_runs": failed_runs,
                "scheduled_runs": scheduled_runs,
                "success_rate": (completed_runs / total_runs * 100) if total_runs > 0 else 0,
                "average_execution_duration_ms": int(avg_duration)
            }
        except Exception as e:
            logger.error(f"Error getting run statistics: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Clean up old scheduler run logs older than specified days.
        Useful for maintaining database size.
        
        Args:
            days: Delete logs older than this many days
        
        Returns:
            Number of documents deleted
        """
        try:
            cutoff_date = now_user_tz() - datetime.timedelta(days=days)
            result = self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            logger.info(f"Cleaned up {result.deleted_count} scheduler run logs older than {days} days")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0


# Global singleton instance
_scheduler_run_logger = None


def get_scheduler_run_logger() -> SchedulerRunLogger:
    """Get or create the global scheduler run logger instance"""
    global _scheduler_run_logger
    if _scheduler_run_logger is None:
        _scheduler_run_logger = SchedulerRunLogger()
    return _scheduler_run_logger


# For convenience, create a default instance
scheduler_run_logger = SchedulerRunLogger()
