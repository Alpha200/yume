import logging
import datetime
import uuid
import time
from typing import Optional, List, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel

from aiagents.memory_manager import run_memory_janitor
from components.timezone_utils import to_user_tz, now_user_tz
from services.scheduler_run_logger import scheduler_run_logger

logger = logging.getLogger(__name__)

class NextRun(BaseModel):
    next_run_time: datetime.datetime
    reason: str
    topic: str
    details: str | None = None  # Additional context/information for the AI engine

class ExecutedReminder(BaseModel):
    executed_at: datetime.datetime
    topic: str

class AIScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.memory_reminder_job_id = "memory_reminder_job"
        self.memory_janitor_job_id = "memory_janitor_job"
        self.day_planner_job_id = "day_planner_job"
        self.deferred_run_job_id = "deferred_ai_run_job"
        # Store the last scheduled NextRun (time + reason) so it can be queried by the API/UI
        self.last_next_run: NextRun | None = None
        # Flag to request day planner execution from AI agent or memory updates
        self.request_day_planner_run: bool = False

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("AI Scheduler started")

            # Schedule recurring memory janitor job every 12 hours
            self._schedule_memory_janitor()
            
            # Schedule day planner updates
            #self._schedule_day_planner()
            
            # Run day planner immediately on startup for today and tomorrow
            #self._run_day_planner_on_startup()

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
            # Schedule unified day planner job to run every 15 minutes
            # This checks today and the next two days
            self.scheduler.add_job(
                func=self._update_all_day_plans,
                trigger=IntervalTrigger(minutes=15),
                id=self.day_planner_job_id,
                name="Day Planner - All Days",
                replace_existing=True
            )

            logger.info("Scheduled day planner: every 15min for today, tomorrow, and day after tomorrow")

        except Exception as e:
            logger.error(f"Error scheduling day planner: {e}")

    async def _update_day_plan(self, days_offset: int = 0, check_range_days: int = 1, trigger_scheduler: bool = False, force_execution: bool = False):
        """
        Generic method to update the day plan for a specified date.
        
        Args:
            days_offset: Number of days from today (0 = today, 1 = tomorrow)
            check_range_days: Number of days to check for calendar changes (1 = just this day, 2 = this day and next)
            trigger_scheduler: Whether to trigger the scheduler if the plan changes (only for today's plan)
            force_execution: If True, skip pre-checks and always execute the agent (for AI agent runs)
        """
        try:
            from components.timezone_utils import now_user_tz
            from aiagents.day_planner import generate_day_plan
            from aiagents.ai_scheduler import determine_next_run_by_memory
            from services.memory_manager import memory_manager
            from services.home_assistant import get_calendar_events_for_day
            from services.day_planner import day_planner_service
            import datetime

            today = now_user_tz().date()
            target_date = today + datetime.timedelta(days=days_offset)
            check_start_date = target_date
            check_end_date = target_date + datetime.timedelta(days=check_range_days - 1)
            
            date_label = "today" if days_offset == 0 else f"+{days_offset}d"
            logger.debug(f"Checking calendar changes for {date_label} ({check_start_date} to {check_end_date})")
            
            # If force_execution is True (AI agent run), skip pre-checks and always run
            if force_execution:
                has_changes = True
                logger.info(f"Force execution enabled for {target_date}, skipping pre-checks")
            else:
                # If no plan exists yet, always run the planner to create the initial plan
                existing_plan = day_planner_service.get_plan_for_date(target_date)
                if not existing_plan:
                    logger.info(f"No existing plan for {target_date}, will generate new plan")
                    has_changes = True
                else:
                    # Check if calendar has changed before running the expensive agent
                    has_changes = await day_planner_service.check_calendar_changes(check_start_date, check_end_date)
            
            if not has_changes:
                logger.debug(f"No calendar changes for {target_date}, skipping day planner agent run")
                return
            
            logger.info(f"Calendar changes detected for {target_date}, updating day plan")

            # Gather information
            memories = memory_manager.get_formatted_observations_and_reminders()
            calendar_events_list = await get_calendar_events_for_day(target_date)
            
            # Format calendar events with full details for the AI agent
            formatted_events = []
            for event in calendar_events_list:
                if event.is_all_day:
                    # All-day event
                    event_str = f"- {event.summary} (all-day)"
                    if event.end:
                        # Check if it extends beyond one day
                        try:
                            start_dt = datetime.datetime.fromisoformat(event.start.replace('Z', '+00:00'))
                            end_dt = datetime.datetime.fromisoformat(event.end.replace('Z', '+00:00'))
                            if (end_dt.date() - start_dt.date()).days > 0:
                                event_str += f" from {start_dt.date()} to {end_dt.date()}"
                        except:
                            pass
                else:
                    # Timed event
                    try:
                        start_dt = datetime.datetime.fromisoformat(event.start.replace('Z', '+00:00'))
                        end_dt = datetime.datetime.fromisoformat(event.end.replace('Z', '+00:00')) if event.end else None
                        
                        if end_dt and (end_dt.date() - start_dt.date()).days > 0:
                            # Multi-day event
                            event_str = f"- {event.summary} from {start_dt.strftime('%H:%M on %Y-%m-%d')} to {end_dt.strftime('%H:%M on %Y-%m-%d')}"
                        elif end_dt:
                            # Same day event
                            event_str = f"- {event.summary} {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                        else:
                            # No end time
                            event_str = f"- {event.summary} at {start_dt.strftime('%H:%M')}"
                    except:
                        event_str = f"- {event.summary}"
                
                if event.location:
                    event_str += f" @ {event.location}"
                formatted_events.append(event_str)
            
            calendar_events = "\n".join(formatted_events)

            # Generate the plan (agent uses tools to save directly)
            result = await generate_day_plan(target_date, memories, calendar_events)

            logger.info(f"Updated day plan for {target_date}: {len(result.actions_taken)} actions taken")
            
            # If the agent took actions (updated the plan), trigger the scheduler (only for today)
            if trigger_scheduler and result.actions_taken and len(result.actions_taken) > 0:
                logger.debug(f"Day plan for {target_date} changed, triggering scheduler")
                try:
                    await determine_next_run_by_memory()
                except Exception as e:
                    logger.error(f"Error triggering scheduler after day plan update: {e}")

        except Exception as e:
            logger.error(f"Error updating day plan (offset={days_offset}): {e}")

    def _run_day_planner_on_startup(self):
        """Run day planner immediately on startup for today, tomorrow, and day after tomorrow"""
        import asyncio
        
        # Schedule the async function to run immediately
        asyncio.create_task(self._update_all_day_plans())
        logger.info("Scheduled initial day plan generation for today, tomorrow, and day after tomorrow")

    async def _update_all_day_plans(self):
        """
        Update day plans for today, tomorrow, and day after tomorrow.
        Runs as a single unified job every 15 minutes.
        
        If day planner execution was explicitly requested (by memory updates or AI agent),
        runs all 3 day plans with force_execution=True, bypassing pre-checks.
        Otherwise, uses normal pre-checks (calendar change detection).
        """
        try:
            # Check if explicit request was made
            force_execute = self.request_day_planner_run
            if force_execute:
                self.request_day_planner_run = False  # Reset the flag
                logger.info("Executing day planner with force execution (memory or agent request)")
            
            # Update all three day plans
            await self._update_day_plan(days_offset=0, check_range_days=1, trigger_scheduler=True, force_execution=force_execute)
            await self._update_day_plan(days_offset=1, check_range_days=1, trigger_scheduler=False, force_execution=force_execute)
            await self._update_day_plan(days_offset=2, check_range_days=1, trigger_scheduler=False, force_execution=force_execute)
            
        except Exception as e:
            logger.error(f"Error in unified day planner update: {e}")

    def request_day_planner_execution(self):
        """Allow AI agent or other components to request day planner execution"""
        self.request_day_planner_run = True
        logger.debug("Day planner execution requested")

    def schedule_next_run(self, next_run: NextRun):
        """Schedule the next run of the memory reminder and log it"""
        # Persist the next_run so callers (API/UI) can retrieve the scheduled time and reason
        self.last_next_run = next_run
        
        # Cancel any previously scheduled runs (only one scheduled reminder at a time)
        scheduler_run_logger.cancel_previous_scheduled_runs()
        
        # Log the scheduled run to MongoDB
        run_id = str(uuid.uuid4())
        scheduler_run_logger.log_scheduled_run(
            run_id=run_id,
            scheduled_time=next_run.next_run_time,
            reason=next_run.reason,
            topic=next_run.topic,
            metadata={"version": "v2.0"},  # Version identifier for logging format
            details=next_run.details
        )
        
        self._schedule_memory_reminder(next_run.next_run_time, next_run.reason, next_run.topic, run_id, next_run.details)

    def _schedule_memory_reminder(self, date_time: datetime.datetime, run_reason: str, topic: str | None = None, run_id: str = None, details: str = None):
        """Schedule or update the memory reminder job"""
        try:
            # Generate run_id if not provided
            if not run_id:
                run_id = str(uuid.uuid4())
            
            # Remove existing job if it exists
            if self.scheduler.get_job(self.memory_reminder_job_id):
                self.scheduler.remove_job(self.memory_reminder_job_id)
                logger.debug(f"Removed existing memory reminder job")

            # Add new job with the run reason and run_id for logging
            job_kwargs = {"run_reason": run_reason, "topic": topic, "run_id": run_id, "details": details}

            self.scheduler.add_job(
                func=self._trigger_memory_reminder,
                trigger=DateTrigger(run_date=date_time),
                id=self.memory_reminder_job_id,
                name="Memory Reminder",
                replace_existing=True,
                kwargs=job_kwargs
            )

            logger.info(f"Scheduled memory reminder for {date_time} with reason: {run_reason} and topic: {topic} (run_id: {run_id})")

        except Exception as e:
            logger.error(f"Error scheduling memory reminder: {e}")

    async def _trigger_memory_reminder(self, run_reason: str, topic: str, run_id: str = None, details: str = None):
        """Trigger the memory reminder in the AI engine and log execution"""
        execution_start_time = time.time()
        
        # Generate run_id if not provided (shouldn't happen, but safety measure)
        if not run_id:
            run_id = str(uuid.uuid4())
        
        try:
            from services.ai_engine import handle_memory_reminder

            # Log execution start
            scheduler_run_logger.log_execution_start(run_id)

            logger.info(f"Memory reminder triggered with reason '{run_reason}' for topic {topic} (run_id: {run_id})")

            ai_input = topic if topic is not None else run_reason
            result = await handle_memory_reminder(ai_input, details=details)

            # Calculate execution duration
            execution_duration_ms = int((time.time() - execution_start_time) * 1000)
            
            # Log successful completion
            ai_response = str(result) if result else None
            scheduler_run_logger.log_execution_completion(
                run_id=run_id,
                duration_ms=execution_duration_ms,
                ai_response=ai_response
            )

            return result

        except Exception as e:
            # Calculate execution duration even for failed runs
            execution_duration_ms = int((time.time() - execution_start_time) * 1000)
            
            # Log failure
            scheduler_run_logger.log_execution_failure(
                run_id=run_id,
                error_message=str(e),
                duration_ms=execution_duration_ms
            )
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