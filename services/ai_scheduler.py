import logging
import datetime
from typing import Optional, Deque, List, Callable
from collections import deque

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel

from aiagents.memory_manager import run_memory_janitor
from components.timezone_utils import to_user_tz

logger = logging.getLogger(__name__)

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
        self.day_planner_today_job_id = "day_planner_today_job"
        self.day_planner_tomorrow_job_id = "day_planner_tomorrow_job"
        self.deferred_run_job_id = "deferred_ai_run_job"
        # Store the last scheduled NextRun (time + reason) so it can be queried by the API/UI
        self.last_next_run: NextRun | None = None
        # Deque to keep recent executed memory reminder jobs (most recent last)
        self.executed_memory_reminders: Deque[ExecutedReminder] = deque(maxlen=10)

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("AI Scheduler started")

            # Schedule recurring memory janitor job every 12 hours
            self._schedule_memory_janitor()
            
            # Schedule day planner updates
            self._schedule_day_planner()
            
            # Run day planner immediately on startup for today and tomorrow
            self._run_day_planner_on_startup()

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("AI Scheduler stopped")

    def _schedule_memory_janitor(self):
        """Schedule the recurring memory janitor job to run every 12 hours"""
        try:
            # Remove existing job if it exists
            if self.scheduler.get_job(self.memory_janitor_job_id):
                self.scheduler.remove_job(self.memory_janitor_job_id)
                logger.debug("Removed existing memory janitor job")

            # Add recurring job every 12 hours
            self.scheduler.add_job(
                func=self._trigger_memory_janitor,
                trigger=IntervalTrigger(hours=12),
                id=self.memory_janitor_job_id,
                name="Memory Janitor",
                replace_existing=True
            )

            logger.info("Scheduled memory janitor to run every 12 hours")

        except Exception as e:
            logger.error(f"Error scheduling memory janitor: {e}")

    async def _trigger_memory_janitor(self):
        """Trigger the memory janitor and communicate results to user via AI engine"""
        try:
            logger.debug("Triggering memory janitor")
            result = await run_memory_janitor()
            logger.info(f"Memory janitor completed: {result}")

            # If the janitor took any actions, notify the user via AI engine
            if result and result.actions_taken and len(result.actions_taken) > 0:
                try:
                    # Import here to avoid circular dependency
                    from services.ai_engine import handle_memory_janitor_result
                    await handle_memory_janitor_result(result)
                except Exception as e:
                    logger.error(f"Error communicating janitor results to user: {e}")

        except Exception as e:
            logger.error(f"Error triggering memory janitor: {e}")

    def _schedule_day_planner(self):
        """Schedule recurring day planner updates"""
        try:
            # Remove existing jobs if they exist
            if self.scheduler.get_job(self.day_planner_today_job_id):
                self.scheduler.remove_job(self.day_planner_today_job_id)
            if self.scheduler.get_job(self.day_planner_tomorrow_job_id):
                self.scheduler.remove_job(self.day_planner_tomorrow_job_id)

            # Schedule today's plan to update every hour
            self.scheduler.add_job(
                func=self._update_today_plan,
                trigger=IntervalTrigger(hours=1),
                id=self.day_planner_today_job_id,
                name="Day Planner - Today",
                replace_existing=True
            )

            # Schedule tomorrow's plan to update every 8 hours
            self.scheduler.add_job(
                func=self._update_tomorrow_plan,
                trigger=IntervalTrigger(hours=8),
                id=self.day_planner_tomorrow_job_id,
                name="Day Planner - Tomorrow",
                replace_existing=True
            )

            logger.info("Scheduled day planner: every 1h for today, every 8h for tomorrow")

        except Exception as e:
            logger.error(f"Error scheduling day planner: {e}")

    async def _update_today_plan(self):
        """Update the day plan for today"""
        try:
            from components.timezone_utils import now_user_tz
            from aiagents.day_planner import generate_day_plan
            from aiagents.ai_scheduler import determine_next_run_by_memory
            from services.memory_manager import memory_manager
            from services.home_assistant import get_calendar_events_for_day

            today = now_user_tz().date()
            logger.debug(f"Updating day plan for today: {today}")

            # Gather information
            memories = memory_manager.get_formatted_observations_and_reminders()
            calendar_events_list = await get_calendar_events_for_day(today)
            calendar_events = "\n".join([
                f"- {event.summary} at {event.start.strftime('%H:%M')}"
                for event in calendar_events_list
            ])

            # Generate the plan (agent uses tools to save directly)
            result = await generate_day_plan(today, memories, calendar_events)

            logger.info(f"Updated day plan for today: {len(result.actions_taken)} actions taken")
            
            # If the agent took actions (updated the plan), trigger the scheduler
            if result.actions_taken and len(result.actions_taken) > 0:
                logger.debug("Day plan for today changed, triggering scheduler")
                try:
                    await determine_next_run_by_memory()
                except Exception as e:
                    logger.error(f"Error triggering scheduler after day plan update: {e}")

        except Exception as e:
            logger.error(f"Error updating today's day plan: {e}")

    async def _update_tomorrow_plan(self):
        """Update the day plan for tomorrow"""
        try:
            from components.timezone_utils import now_user_tz
            from aiagents.day_planner import generate_day_plan
            from services.memory_manager import memory_manager
            from services.home_assistant import get_calendar_events_for_day
            import datetime

            tomorrow = now_user_tz().date() + datetime.timedelta(days=1)
            logger.debug(f"Updating day plan for tomorrow: {tomorrow}")

            # Gather information
            memories = memory_manager.get_formatted_observations_and_reminders()
            calendar_events_list = await get_calendar_events_for_day(tomorrow)
            calendar_events = "\n".join([
                f"- {event.summary} at {event.start.strftime('%H:%M')}"
                for event in calendar_events_list
            ])

            # Generate the plan (agent uses tools to save directly)
            result = await generate_day_plan(tomorrow, memories, calendar_events)

            logger.info(f"Updated day plan for tomorrow: {len(result.actions_taken)} actions taken")

        except Exception as e:
            logger.error(f"Error updating tomorrow's day plan: {e}")

    def _run_day_planner_on_startup(self):
        """Run day planner immediately on startup for today and tomorrow"""
        import asyncio
        
        async def run_initial_plans():
            await self._update_today_plan()
            await self._update_tomorrow_plan()
        
        # Schedule the async function to run immediately
        asyncio.create_task(run_initial_plans())
        logger.info("Scheduled initial day plan generation for today and tomorrow")

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
                logger.debug(f"Removed existing memory reminder job")

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

            logger.info(f"Scheduled memory reminder for {date_time} with reason: {run_reason} and topic: {topic}")

        except Exception as e:
            logger.error(f"Error scheduling memory reminder: {e}")

    async def _trigger_memory_reminder(self, run_reason: str, topic: str):
        """Trigger the memory reminder in the AI engine"""
        try:
            from services.ai_engine import handle_memory_reminder

            entry = ExecutedReminder(
                executed_at=datetime.datetime.now(datetime.timezone.utc),
                topic=topic,
            )
            self.executed_memory_reminders.append(entry)
            logger.info(f"Memory reminder triggered with reason '{run_reason}' for topic {topic}")

            ai_input = topic if topic is not None else run_reason
            result = await handle_memory_reminder(ai_input)

            return result

        except Exception as e:
            logger.error(f"Error triggering memory reminder: {e}")

    def cancel_memory_reminder(self):
        """Cancel the scheduled memory reminder"""
        try:
            if self.scheduler.get_job(self.memory_reminder_job_id):
                self.scheduler.remove_job(self.memory_reminder_job_id)
                logger.debug("Memory reminder cancelled")
                return True
            else:
                logger.debug("No memory reminder to cancel")
                return False
        except Exception as e:
            logger.error(f"Error cancelling memory reminder: {e}")
            return False

    def cancel_memory_janitor(self):
        """Cancel the recurring memory janitor job"""
        try:
            if self.scheduler.get_job(self.memory_janitor_job_id):
                self.scheduler.remove_job(self.memory_janitor_job_id)
                logger.debug("Memory janitor cancelled")
                return True
            else:
                logger.debug("No memory janitor to cancel")
                return False
        except Exception as e:
            logger.error(f"Error cancelling memory janitor: {e}")
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
            logger.error(f"Error getting next memory reminder: {e}")
            return None

    def get_recent_executed_reminders(self, limit: int | None = None) -> List[ExecutedReminder]:
        """Return a list of recent executed memory reminders (most recent last). If limit is provided, return at most that many entries."""
        try:
            items = list(self.executed_memory_reminders)
            if limit is not None:
                return items[-limit:]
            return items
        except Exception as e:
            logger.error(f"Error getting recent executed reminders: {e}")
            return []

    def schedule_deferred_run(self, callback: Callable):
        """Schedule a deferred AI run to happen 60 seconds from now.

        If another deferred run is already scheduled, it will be cancelled and replaced.
        This prevents multiple runs from happening in quick succession.

        Args:
            callback: Async callable to execute
        """
        try:

            # Remove existing deferred job if it exists
            if self.scheduler.get_job(self.deferred_run_job_id):
                self.scheduler.remove_job(self.deferred_run_job_id)
                logger.debug("Cancelled previous deferred AI run, scheduling new one")

            # Schedule the job to run 60 seconds from now
            run_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=60)

            self.scheduler.add_job(
                func=self._execute_deferred_run,
                trigger=DateTrigger(run_date=run_time),
                id=self.deferred_run_job_id,
                name="Deferred AI Run",
                replace_existing=True,
                kwargs={"callback": callback}
            )

            logger.info(f"Scheduled deferred AI scheduler run in 60 seconds (at {run_time})")

        except Exception as e:
            logger.error(f"Error scheduling deferred run: {e}")

    async def _execute_deferred_run(self, callback: Callable):
        """Execute the deferred run callback"""
        try:
            logger.debug("Executing deferred AI run")
            await callback()
        except Exception as e:
            logger.error(f"Error executing deferred run: {e}")


ai_scheduler = AIScheduler()