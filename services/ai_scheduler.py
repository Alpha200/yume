import asyncio
import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel

from aiagents.memory_manager import run_memory_janitor
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz, to_user_tz

logger = logging_manager

class NextRun(BaseModel):
    next_run_time: datetime.datetime
    reason: str

class AIScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.memory_reminder_job_id = "memory_reminder_job"
        self.memory_janitor_job_id = "memory_janitor_job"

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.log("AI Scheduler started")

            # Schedule recurring memory janitor job every 12 hours
            self._schedule_memory_janitor()

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.log("AI Scheduler stopped")

    def _schedule_memory_janitor(self):
        """Schedule the recurring memory janitor job to run every 12 hours"""

        try:
            # Remove existing job if it exists
            if self.scheduler.get_job(self.memory_janitor_job_id):
                self.scheduler.remove_job(self.memory_janitor_job_id)
                logger.log("Removed existing memory janitor job")

            # Add recurring job every 12 hours
            self.scheduler.add_job(
                func=self._trigger_memory_janitor,
                trigger=IntervalTrigger(hours=12),
                id=self.memory_janitor_job_id,
                name="Memory Janitor",
                replace_existing=True
            )

            logger.log("Scheduled memory janitor to run every 12 hours")

        except Exception as e:
            logger.log(f"Error scheduling memory janitor: {e}")

    def _trigger_memory_janitor(self):
        """Trigger the memory janitor in the AI engine"""
        try:
            logger.log("Triggering memory janitor")
            result = run_memory_janitor()
            logger.log(f"Memory janitor completed: {result}")
        except Exception as e:
            logger.log(f"Error triggering memory janitor: {e}")

    def schedule_next_run(self, next_run: NextRun):
        """Schedule the next run of the memory reminder"""
        self._schedule_memory_reminder(next_run.next_run_time, next_run.reason)

    def _schedule_memory_reminder(self, date_time: datetime.datetime, run_reason: str):
        """Schedule or update the memory reminder job"""
        try:
            # Remove existing job if it exists
            if self.scheduler.get_job(self.memory_reminder_job_id):
                self.scheduler.remove_job(self.memory_reminder_job_id)
                logger.log(f"Removed existing memory reminder job")

            # Add new job with the run reason
            self.scheduler.add_job(
                func=self._trigger_memory_reminder,
                trigger=DateTrigger(run_date=date_time),
                id=self.memory_reminder_job_id,
                name="Memory Reminder",
                replace_existing=True,
                kwargs={"run_reason": run_reason}
            )

            logger.log(f"Scheduled memory reminder for {date_time} with reason: {run_reason}")

        except Exception as e:
            logger.log(f"Error scheduling memory reminder: {e}")

    def _trigger_memory_reminder(self, run_reason: str = "Scheduled memory reminder"):
        """Trigger the memory reminder in the AI engine"""
        try:
            event_data = {
                "type": "memory_reminder",
                "timestamp": now_user_tz(),
                "reason": run_reason,
                "message": f"Memory reminder triggered: {run_reason}"
            }
            from services.ai_engine import handle_memory_reminder
            result = handle_memory_reminder(event_data)

            logger.log(f"Memory reminder triggered with reason '{run_reason}': {result}")
        except Exception as e:
            logger.log(f"Error triggering memory reminder: {e}")

    def cancel_memory_reminder(self):
        """Cancel the scheduled memory reminder"""
        try:
            if self.scheduler.get_job(self.memory_reminder_job_id):
                self.scheduler.remove_job(self.memory_reminder_job_id)
                logger.log("Memory reminder cancelled")
                return True
            else:
                logger.log("No memory reminder to cancel")
                return False
        except Exception as e:
            logger.log(f"Error cancelling memory reminder: {e}")
            return False

    def cancel_memory_janitor(self):
        """Cancel the recurring memory janitor job"""
        try:
            if self.scheduler.get_job(self.memory_janitor_job_id):
                self.scheduler.remove_job(self.memory_janitor_job_id)
                logger.log("Memory janitor cancelled")
                return True
            else:
                logger.log("No memory janitor to cancel")
                return False
        except Exception as e:
            logger.log(f"Error cancelling memory janitor: {e}")
            return False

    def get_next_memory_reminder(self) -> Optional[datetime.datetime]:
        """Get the next scheduled memory reminder time"""
        try:
            job = self.scheduler.get_job(self.memory_reminder_job_id)
            if job and job.next_run_time:
                return to_user_tz(job.next_run_time.replace(tzinfo=None) if job.next_run_time.tzinfo is None else job.next_run_time)
            return None
        except Exception as e:
            logger.log(f"Error getting next memory reminder: {e}")
            return None

ai_scheduler = AIScheduler()