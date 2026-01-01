package eu.sendzik.yume.service.provider

import eu.sendzik.yume.agent.model.YumeChatResource
import eu.sendzik.yume.configuration.AgentConfiguration
import eu.sendzik.yume.service.dayplan.DayPlanService
import eu.sendzik.yume.service.location.LocationService
import eu.sendzik.yume.service.provider.model.YumeResource
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
) {
    fun provideResources(resources: List<YumeResource>): String = buildString {
        resources.forEach {
            when (it) {
                YumeResource.WEATHER_FORECAST -> {
                    weatherService.getWeatherForecast()?.let { appendLine(it) }
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
            }
        }
    }
}