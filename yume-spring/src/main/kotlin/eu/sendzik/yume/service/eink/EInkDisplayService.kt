package eu.sendzik.yume.service.eink

import eu.sendzik.yume.agent.EInkDisplayAgent
import eu.sendzik.yume.service.provider.ResourceProviderService
import eu.sendzik.yume.service.provider.model.YumeResource
import org.springframework.stereotype.Service

@Service
class EInkDisplayService(
    private val eInkDisplayAgent: EInkDisplayAgent,
    private val resourceProviderService: ResourceProviderService,
) {
    fun getEInkDisplayContent(): String {
        val resources = resourceProviderService.provideResources(listOf(
            YumeResource.CURRENT_DATE_TIME,
            YumeResource.USER_LANGUAGE,
            YumeResource.WEATHER_FORECAST,
            YumeResource.DAY_PLAN_TODAY,
            YumeResource.DAY_PLAN_TOMORROW,
            YumeResource.SUMMARIZED_PREFERENCES,
            YumeResource.SUMMARIZED_OBSERVATIONS,
        ))

        val input = buildString {
            appendLine("Information to consider:")
            appendLine("BEGIN OF INFORMATION")
            appendLine(resources)
            appendLine("END OF INFORMATION")
            appendLine("Based on the above information, generate the content to be displayed on the e-ink display for the next hours.")
        }

        return eInkDisplayAgent.generateTextForEInkDisplay(input)
    }
}