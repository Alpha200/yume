import datetime
from typing import Optional, Deque, List
from collections import deque

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel

from aiagents.memory_manager import run_memory_janitor
from components.logging_manager import logging_manager
from components.timezone_utils import to_user_tz

logger = logging_manager

class NextRun(BaseModel):
    next_run_time: datetime.datetime
    reason: str
    topic: str

class ExecutedReminder(BaseModel):
    executed_at: datetime.datetime
    topic: str

class AIScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.memory_reminder_job_id = "memory_reminder_job"
        self.memory_janitor_job_id = "memory_janitor_job"
        # Store the last scheduled NextRun (time + reason) so it can be queried by the API/UI
        self.last_next_run: NextRun | None = None
        # Deque to keep recent executed memory reminder jobs (most recent last)
        self.executed_memory_reminders: Deque[ExecutedReminder] = deque(maxlen=10)

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
        # Persist the next_run so callers (API/UI) can retrieve the scheduled time and reason
        self.last_next_run = next_run
        self._schedule_memory_reminder(next_run.next_run_time, next_run.reason, next_run.topic)

    def _schedule_memory_reminder(self, date_time: datetime.datetime, run_reason: str, topic: str | None = None):
        """Schedule or update the memory reminder job"""
        try:
            # Remove existing job if it exists
            if self.scheduler.get_job(self.memory_reminder_job_id):
                self.scheduler.remove_job(self.memory_reminder_job_id)
                logger.log(f"Removed existing memory reminder job")

            # Add new job with the run reason
            job_kwargs = {"run_reason": run_reason, "topic": topic}

            self.scheduler.add_job(
                func=self._trigger_memory_reminder,
                trigger=DateTrigger(run_date=date_time),
                id=self.memory_reminder_job_id,
                name="Memory Reminder",
                replace_existing=True,
                kwargs=job_kwargs
            )

            logger.log(f"Scheduled memory reminder for {date_time} with reason: {run_reason} and topic: {topic}")

        except Exception as e:
            logger.log(f"Error scheduling memory reminder: {e}")

    async def _trigger_memory_reminder(self, run_reason: str, topic: str):
        """Trigger the memory reminder in the AI engine"""
        try:
            from services.ai_engine import handle_memory_reminder

            entry = ExecutedReminder(
                executed_at=datetime.datetime.now(datetime.timezone.utc),
                topic=topic,
            )
            self.executed_memory_reminders.append(entry)
            logger.log(f"Memory reminder triggered with reason '{run_reason}' for topic {topic}")

            ai_input = topic if topic is not None else run_reason
            result = await handle_memory_reminder(ai_input)

            return result

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

    def get_next_memory_reminder(self) -> Optional[NextRun]:
        """Get the next scheduled memory reminder time"""
        try:
            # Prefer the stored last_next_run which contains both time and reason
            job = self.scheduler.get_job(self.memory_reminder_job_id)
            if job and job.next_run_time:
                next_run_time = to_user_tz(job.next_run_time.replace(tzinfo=None) if job.next_run_time.tzinfo is None else job.next_run_time)

                # Attempt to get reason from stored last_next_run if it matches the time
                reason = None
                topic = None
                if self.last_next_run and abs((self.last_next_run.next_run_time - next_run_time).total_seconds()) < 1:
                    reason = self.last_next_run.reason
                    topic = self.last_next_run.topic
                else:
                    try:
                        reason = job.kwargs.get("run_reason")
                        topic = job.kwargs.get("topic") if isinstance(job.kwargs, dict) else None
                    except Exception:
                        reason = None
                        topic = None

                return NextRun(next_run_time=next_run_time, reason=reason or "", topic=topic)

            # Fallback to any previously stored NextRun
            return self.last_next_run
        except Exception as e:
            logger.log(f"Error getting next memory reminder: {e}")
            return None

    def get_recent_executed_reminders(self, limit: int | None = None) -> List[ExecutedReminder]:
        """Return a list of recent executed memory reminders (most recent last). If limit is provided, return at most that many entries."""
        try:
            items = list(self.executed_memory_reminders)
            if limit is not None:
                return items[-limit:]
            return items
        except Exception as e:
            logger.log(f"Error getting recent executed reminders: {e}")
            return []


ai_scheduler = AIScheduler()