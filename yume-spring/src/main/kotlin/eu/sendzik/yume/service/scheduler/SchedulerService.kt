package eu.sendzik.yume.service.scheduler

import eu.sendzik.yume.agent.SchedulerAgent
import eu.sendzik.yume.agent.model.YumeChatResource
import eu.sendzik.yume.configuration.SchedulerConfiguration
import eu.sendzik.yume.service.dayplan.model.DayPlanUpdatedEvent
import eu.sendzik.yume.service.provider.ResourceProviderService
import eu.sendzik.yume.service.provider.model.YumeResource
import eu.sendzik.yume.service.scheduler.model.SchedulerExecutedEvent
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import jakarta.annotation.PostConstruct
import org.springframework.context.event.EventListener
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler
import org.springframework.stereotype.Service
import java.time.Duration
import java.time.Instant
import java.time.LocalDate
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

    fun triggerRun(duration: Duration? = null) {
        val duration = duration ?: Duration.ofSeconds(schedulerConfiguration.delaySeconds)
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
        triggerRun(Duration.ofMinutes(1))
    }

    @EventListener
    fun dayPlanUpdatedEventListener(event: DayPlanUpdatedEvent) {
        if (event.dayPlan.date == LocalDate.now() || event.dayPlan.date == LocalDateTime.now().plusDays(1)) {
            logger.info { "Day plan updated event received for current or next day, triggering scheduler run." }
            triggerRun()
        }
    }

    @EventListener
    fun schedulerExecutedEventListener(event: SchedulerExecutedEvent) {
        logger.info { "Scheduler executed event received, triggering next scheduler run." }
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
            YumeResource.RECENT_SCHEDULER_EXECUTIONS,
            YumeResource.RECENT_GEOFENCE_EVENTS,
            YumeResource.RECENT_USER_INTERACTION,
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
