package eu.sendzik.yume.service.scheduler

import eu.sendzik.yume.agent.SchedulerAgent
import eu.sendzik.yume.agent.model.YumeChatResource
import eu.sendzik.yume.configuration.SchedulerConfiguration
import eu.sendzik.yume.service.provider.ResourceProviderService
import eu.sendzik.yume.service.provider.model.YumeResource
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import eu.sendzik.yume.utils.formatTimestampForLLM
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
    private val resourceProviderService: ResourceProviderService,
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
        val additionalInformation = resourceProviderService.provideResources(listOf(
            YumeResource.DAY_PLAN_TODAY,
            YumeResource.DAY_PLAN_TOMORROW,
            YumeResource.LOCATION,
            YumeResource.CURRENT_DATE_TIME,
            YumeResource.USER_LANGUAGE,
            YumeResource.SUMMARIZED_REMINDERS,
            YumeResource.SUMMARIZED_OBSERVATIONS,
            YumeResource.SUMMARIZED_PREFERENCES,
        ))

        val result = schedulerAgent.determineNextRun(
            additionalInformation = additionalInformation,
        )

        if (result.nextRun < LocalDateTime.now().plus(Duration.ofMinutes(schedulerConfiguration.minTemporalDistanceMinutes))) {
            logger.warn { "Scheduler agent result was not at least ${schedulerConfiguration.minTemporalDistanceMinutes} minutes in the future! Will be adjusted. Result was: ${result.nextRun}" }
            result.nextRun = LocalDateTime.now().plus(Duration.ofMinutes(schedulerConfiguration.minTemporalDistanceMinutes))
        }

        scheduleExecutorService.scheduleNextRun(
            SchedulerRunDetails.fromSchedulerAgentResult(result)
        )
    }
}
