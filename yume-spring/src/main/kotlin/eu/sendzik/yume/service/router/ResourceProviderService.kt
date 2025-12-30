package eu.sendzik.yume.service.router

import eu.sendzik.yume.agent.model.YumeAgentResource
import eu.sendzik.yume.service.dayplan.DayPlanService
import eu.sendzik.yume.service.weather.WeatherService
import org.springframework.stereotype.Service
import java.time.LocalDate

@Service
class ResourceProviderService(
    private val weatherService: WeatherService,
    private val dayPlanService: DayPlanService,
) {
    fun provideResources(resources: List<YumeAgentResource>): String = buildString {
        resources.forEach {
            when (it) {
                YumeAgentResource.WEATHER -> {
                    appendLine(weatherService.getWeatherForecast())
                }
                YumeAgentResource.DAY_PLAN_TODAY -> {
                    appendLine(dayPlanService.getFormattedPlan(LocalDate.now()))
                }
                YumeAgentResource.DAY_PLAN_TOMORROW -> {
                    appendLine(dayPlanService.getFormattedPlan(LocalDate.now().plusDays(1)))
                }
            }
        }
    }
}