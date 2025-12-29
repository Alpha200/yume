package eu.sendzik.yume.service.scheduler

import eu.sendzik.yume.agent.SchedulerAgent
import eu.sendzik.yume.configuration.SchedulerConfiguration
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import io.github.oshai.kotlinlogging.KLogger
import jakarta.annotation.PostConstruct
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler
import org.springframework.stereotype.Service
import java.time.Duration
import java.time.Instant
import java.time.LocalDateTime
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Service
class SchedulerService(
    private val scheduleExecutorService: ScheduleExecutorService,
    private val taskScheduler: ThreadPoolTaskScheduler,
    private val schedulerConfiguration: SchedulerConfiguration,
    private val schedulerAgent: SchedulerAgent,
    private val logger: KLogger,
) {
    private var scheduledTask: ScheduledFuture<*>? = null
    private val lock = ReentrantLock()

    fun triggerRun() {
        val duration = Duration.ofSeconds(schedulerConfiguration.delaySeconds)
        val minutes = duration.toMinutes().toString()
        val seconds = duration.toSecondsPart().toString().padStart(2, '0')

        logger.debug { "Scheduling next scheduler agent run in ${minutes}:${seconds} minutes" }

        lock.withLock {
            scheduledTask?.cancel(false)

            scheduledTask = taskScheduler.schedule(
                { executeScheduling() },
                Instant.now().plus(duration)
            )
        }
    }

    @PostConstruct
    fun init() {
        triggerRun()
    }

    private fun executeScheduling() {
        val result = schedulerAgent.determineNextRun()

        if (result.nextRun < LocalDateTime.now().plus(Duration.ofMinutes(schedulerConfiguration.minTemporalDistanceMinutes))) {
            logger.warn { "Scheduler agent result was not at least ${schedulerConfiguration.minTemporalDistanceMinutes} minutes in the future! Will be adjusted. Result was: ${result.nextRun}" }
            result.nextRun = LocalDateTime.now().plus(Duration.ofMinutes(schedulerConfiguration.minTemporalDistanceMinutes))
        }

        scheduleExecutorService.scheduleNextRun(
            SchedulerRunDetails.fromSchedulerAgentResult(result)
        )
    }
}
