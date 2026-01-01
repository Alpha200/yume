package eu.sendzik.yume.service.dayplan

import eu.sendzik.yume.agent.DayPlanAgent
import eu.sendzik.yume.service.provider.ResourceProviderService
import eu.sendzik.yume.service.provider.model.YumeResource
import eu.sendzik.yume.service.scheduler.SchedulerService
import io.github.oshai.kotlinlogging.KLogger
import jakarta.annotation.PostConstruct
import org.springframework.scheduling.annotation.Async
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Service
class DayPlanExecutorService(
    private val dayPlanAgent: DayPlanAgent,
    private val schedulerService: SchedulerService,
    private val resourceProviderService: ResourceProviderService,
    private val logger: KLogger,
) {
    private val lock = ReentrantLock()

    @Scheduled(cron = "\${yume.day-plan.update-cron}")
    fun executeDayPlanUpdates() {
        lock.withLock {
            logger.info { "Executing scheduled day plan update" }

            val additionalInformation = resourceProviderService.provideResources(listOf(
                YumeResource.CURRENT_DATE_TIME,
                YumeResource.USER_LANGUAGE,
                YumeResource.CALENDAR_NEXT_2_DAYS,
            ))

            dayPlanAgent.updateDayPlansWithTask(
                "Check if a day plan for today and tomorrow exists and create or update them as necessary.",
                additionalInformation
            )
        }
    }

    @PostConstruct
    fun initializeDayPlanUpdates() {
        executeDayPlanUpdates()
    }

    @Async
    fun updateDayPlansWithTask(dayPlannerUpdateTask: String) {
        lock.withLock {
            logger.info { "Updating day plans with task: $dayPlannerUpdateTask" }

            val additionalInformation = resourceProviderService.provideResources(listOf(
                YumeResource.CURRENT_DATE_TIME,
                YumeResource.USER_LANGUAGE
            ))

            val result = dayPlanAgent.updateDayPlansWithTask(
                query = dayPlannerUpdateTask,
                additionalInformation =  additionalInformation
            )

            if (!result.actionsTaken.isNullOrEmpty()) {
                schedulerService.triggerRun()
            }
        }
    }
}