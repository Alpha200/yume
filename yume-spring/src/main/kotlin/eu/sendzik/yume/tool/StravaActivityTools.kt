package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.service.strava.StravaActivityService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component

@Component
@Suppress("unused")
class StravaActivityTools(
    private val stravaActivityService: StravaActivityService,
    private val logger: KLogger,
) {
    @Suppress("UNUSED")
    @Tool("Get recent activity records")
    fun getRecentActivities(
        @P("Maximum number of activities to return (default: 10)")
        limit: Int = 10
    ): String {
        return stravaActivityService.getRecentActivities(limit).getOrElse { error ->
            logger.error(error) { "Failed to fetch recent activities" }
            "Failed to fetch recent activities: ${error.message}"
        }
    }
}
