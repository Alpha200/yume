package eu.sendzik.yume.service.dayplan

import eu.sendzik.yume.agent.DayPlanAgent
import eu.sendzik.yume.service.scheduler.SchedulerService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.scheduling.annotation.Async
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Service
class DayPlanExecutorService(
    private val dayPlanAgent: DayPlanAgent,
    private val schedulerService: SchedulerService,
    private val logger: KLogger,
) {
    private val lock = ReentrantLock()

    @Scheduled(cron = "\${yume.day-plan.update-cron}")
    fun executeDayPlanUpdates() {
        // TODO: Check if update is needed and execute
        //dayPlanAgent.updateDayPlansWithTask("")
    }

    @Async
    fun updateDayPlansWithTask(dayPlannerUpdateTask: String) {
        lock.withLock {
            logger.info { "Updating day plans with task: $dayPlannerUpdateTask" }
            val result = dayPlanAgent.updateDayPlansWithTask(dayPlannerUpdateTask)

            if (!result.actionsTaken.isNullOrEmpty()) {
                schedulerService.triggerRun()
            }
        }
    }
}