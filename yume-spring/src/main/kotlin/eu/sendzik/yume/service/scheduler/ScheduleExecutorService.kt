package eu.sendzik.yume.service.scheduler

import eu.sendzik.yume.service.router.RequestRouterService
import eu.sendzik.yume.service.scheduler.model.SchedulerExecutedEvent
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.context.ApplicationEventPublisher
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
    private val schedulerRunLogService: SchedulerRunLogService,
    private val requestRouterService: RequestRouterService,
    private val applicationEventPublisher: ApplicationEventPublisher,
) {
    private var nextAIRun: ScheduledFuture<*>? = null
    private val lock = ReentrantLock()

    fun scheduleNextRun(schedulerRunDetails: SchedulerRunDetails) {
        val run = schedulerRunLogService.logScheduledRun(schedulerRunDetails)
        
        lock.withLock {
            nextAIRun?.cancel(false)

            nextAIRun = taskScheduler.schedule(
                { executeScheduling(schedulerRunDetails, run.id) },
                schedulerRunDetails.nextRun.atZone(ZoneId.systemDefault()).toInstant()
            )
        }
    }

    private fun executeScheduling(schedulerRunDetails: SchedulerRunDetails, runId: String) {
        lock.withLock {
            nextAIRun = null
        }

        try {
            logger.info {"Executing scheduled run. Topic: ${schedulerRunDetails.topic}" }
            
            val startTime = System.currentTimeMillis()
            val executionSummary = requestRouterService.runFromScheduler(schedulerRunDetails)
            val duration = System.currentTimeMillis() - startTime
            
            schedulerRunLogService.markAsCompleted(runId, aiResponse = executionSummary, executionDurationMs = duration)
        } catch (e: Exception) {
            logger.error(e) { "Error executing scheduled run: ${e.message}" }
            schedulerRunLogService.markAsFailed(runId, e.message ?: "Unknown error")
        }

        applicationEventPublisher.publishEvent(SchedulerExecutedEvent())
    }
}