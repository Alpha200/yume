package eu.sendzik.yume.service.provider

import eu.sendzik.yume.configuration.AgentConfiguration
import eu.sendzik.yume.service.calendar.CalendarService
import eu.sendzik.yume.service.dayplan.DayPlanService
import eu.sendzik.yume.service.location.LocationService
import eu.sendzik.yume.service.memory.MemorySummarizerService
import eu.sendzik.yume.service.memory.model.MemoryType
import eu.sendzik.yume.service.provider.model.YumeResource
import eu.sendzik.yume.service.scheduler.SchedulerRunLogService
import eu.sendzik.yume.service.weather.WeatherService
import eu.sendzik.yume.utils.formatTimestampForLLM
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
) {
    fun provideResources(resources: List<YumeResource>): String = buildString {
        resources.forEach {
            when (it) {
                YumeResource.WEATHER_FORECAST -> {
                    weatherService.getWeatherForecast()?.let { forecast -> appendLine(forecast) }
                }
                YumeResource.DAY_PLAN_TODAY -> {
                    appendLine(dayPlanService.getFormattedPlan(LocalDate.now()))
                }
                YumeResource.DAY_PLAN_TOMORROW -> {
                    appendLine(dayPlanService.getFormattedPlan(LocalDate.now().plusDays(1)))
                }
                YumeResource.LOCATION -> {
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
                    appendLine("Memorized user preferences:\n$summary")
                }
                YumeResource.SUMMARIZED_OBSERVATIONS -> {
                    val summary = memorySummarizerService.getMemorySummary(MemoryType.OBSERVATION)
                    appendLine("Memorized user obseravtions:\n$summary")
                }
                YumeResource.SUMMARIZED_REMINDERS -> {
                    val summary = memorySummarizerService.getMemorySummary(MemoryType.REMINDER)
                    appendLine("Memorized reminders:\n$summary")
                }
                YumeResource.CALENDAR_NEXT_2_DAYS -> {
                    val start = LocalDate.now().atStartOfDay()
                    val end = start.plusDays(2)
                    val calendarEntries = calendarService.getFormattedCalendarEntries(start, end)

                    appendLine("Upcoming calendar events for the next two days:")
                    appendLine(calendarEntries)
                }
                YumeResource.RECENT_SCHEDULER_EXECUTIONS -> {
                    val executions = schedulerRunLogService.getRecentExecutedRunsFormatted(5)
                    appendLine("Recently executed scheduler runs:")
                    appendLine(executions)
                }
            }

            appendLine()
        }
    }
}