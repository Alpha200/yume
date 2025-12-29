package eu.sendzik.yume.service.scheduler

import eu.sendzik.yume.service.chat.ChatInteractionService
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.context.annotation.Lazy
import org.springframework.scheduling.TaskScheduler
import org.springframework.stereotype.Service
import java.time.ZoneId
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Service
class ScheduleExecutorService(
    private val taskScheduler: TaskScheduler,
    private val logger: KLogger,
    @Lazy private val chatInteractionService: ChatInteractionService,
) {
    private var nextAIRun: ScheduledFuture<*>? = null
    private val lock = ReentrantLock()

    fun scheduleNextRun(schedulerRunDetails: SchedulerRunDetails) {
        lock.withLock {
            nextAIRun?.cancel(false)

            nextAIRun = taskScheduler.schedule(
                { executeScheduling(schedulerRunDetails) },
                schedulerRunDetails.nextRun.atZone(ZoneId.systemDefault()).toInstant()
            )
        }
    }

    private fun executeScheduling(schedulerRunDetails: SchedulerRunDetails) {
        lock.withLock {
            nextAIRun = null
        }

        logger.info {"Executing scheduled run. Topic: ${schedulerRunDetails.topic}" }
        // TODO: Fix
        //chatInteractionService.handleScheduledRun(schedulerRunDetails)
    }
}