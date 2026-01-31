package eu.sendzik.yume.service.provider

import eu.sendzik.yume.configuration.AgentConfiguration
import eu.sendzik.yume.service.calendar.CalendarService
import eu.sendzik.yume.service.conversation.ConversationHistoryManagerService
import eu.sendzik.yume.service.dayplan.DayPlanService
import eu.sendzik.yume.service.location.LocationService
import eu.sendzik.yume.service.memory.MemorySummarizerService
import eu.sendzik.yume.service.memory.model.MemoryType
import eu.sendzik.yume.service.provider.model.YumeResource
import eu.sendzik.yume.service.scheduler.SchedulerRunLogService
import eu.sendzik.yume.service.weather.WeatherService
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Service
import java.time.LocalDate
import java.time.LocalDateTime

@Service
class ResourceProviderService(
    private val weatherService: WeatherService,
    private val dayPlanService: DayPlanService,
    private val locationService: LocationService,
    private val agentConfiguration: AgentConfiguration,
    private val calendarService: CalendarService,
    private val memorySummarizerService: MemorySummarizerService,
    private val schedulerRunLogService: SchedulerRunLogService,
    private val conversationHistoryManagerService: ConversationHistoryManagerService,
    private val logger: KLogger,
) {
    fun provideResources(resources: List<YumeResource>): String = buildString {
        resources.forEach {
            when (it) {
                YumeResource.WEATHER_FORECAST -> {
                    appendLine("Weather forecast for current location:")
                    weatherService.getWeatherForecast().onSuccess { weather ->
                        appendLine(weather)
                    }.onFailure { err ->
                        logger.error(err) { "Failed to fetch weather forecast" }
                        appendLine("Unable to fetch weather forecast")
                    }
                }
                YumeResource.DAY_PLAN_TODAY -> {
                    appendLine(dayPlanService.getFormattedPlan(LocalDate.now()))
                }
                YumeResource.DAY_PLAN_TOMORROW -> {
                    appendLine(dayPlanService.getFormattedPlan(LocalDate.now().plusDays(1)))
                }
                YumeResource.LOCATION -> {
                    appendLine("Current location of user:")
                    appendLine(locationService.getCurrentLocationFormatted())
                }
                YumeResource.USER_LANGUAGE -> {
                    appendLine("Always use the user's preferred language: ${agentConfiguration.preferences.userLanguage}")
                }
                YumeResource.CURRENT_DATE_TIME -> {
                    appendLine("The current date and time is: ${formatTimestampForLLM(LocalDateTime.now())}")
                }
                YumeResource.SUMMARIZED_PREFERENCES -> {
                    val summary = memorySummarizerService.getMemorySummary(MemoryType.PREFERENCE)
                    appendLine("Memorized user preferences:")
                    appendLine(summary)
                }
                YumeResource.SUMMARIZED_OBSERVATIONS -> {
                    val summary = memorySummarizerService.getMemorySummary(MemoryType.OBSERVATION)
                    appendLine("Memorized user observations:")
                    appendLine(summary)
                }
                YumeResource.SUMMARIZED_REMINDERS -> {
                    val summary = memorySummarizerService.getMemorySummary(MemoryType.REMINDER)
                    appendLine("Memorized reminders:")
                    appendLine(summary)
                }
                YumeResource.CALENDAR_NEXT_2_DAYS -> {
                    val start = LocalDate.now().atStartOfDay()
                    val end = start.plusDays(2)
                    val calendarEntries = calendarService.getFormattedCalendarEntries(start, end)

                    appendLine("Upcoming calendar events for the next two days:")
                    appendLine("=== BEGIN CALENDAR ENTRIES ===")
                    appendLine(calendarEntries)
                    appendLine("=== END CALENDAR ENTRIES ===")
                }
                YumeResource.RECENT_SCHEDULER_EXECUTIONS -> {
                    val executions = schedulerRunLogService.getRecentExecutedRunsFormatted(5)
                    appendLine("Recently executed scheduler runs:")
                    appendLine("=== BEGIN SCHEDULER EXECUTIONS ===")
                    appendLine(executions)
                    appendLine("=== END SCHEDULER EXECUTIONS ===")
                }
                YumeResource.RECENT_USER_INTERACTION -> {
                    val interactions = conversationHistoryManagerService.getRecentHistoryFormatted()
                    appendLine("Recent user interactions:")
                    appendLine("=== BEGIN USER INTERACTIONS ===")
                    appendLine(interactions)
                    appendLine("=== END USER INTERACTIONS ===")
                }
            }

            appendLine()
        }
    }
}