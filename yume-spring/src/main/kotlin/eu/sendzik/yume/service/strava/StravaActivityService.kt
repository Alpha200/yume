package eu.sendzik.yume.service.strava

import eu.sendzik.yume.client.StravaClient
import eu.sendzik.yume.service.strava.model.StravaActivity
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Service

@Service
class StravaActivityService(
    private val stravaClient: StravaClient,
    private val stravaAuthService: StravaAuthService,
    private val logger: KLogger,
) {
    fun fetchActivityIfCycling(activityId: Long): Result<StravaActivity?> {

        return stravaAuthService.getValidCredentials().mapCatching { _ ->
            val activity = stravaClient.getActivity(activityId)

            if (activity.isCyclingActivity()) {
                logger.info { "Fetched cycling activity: ${activity.name} (${activity.getDistanceInKm().toInt()}km, ${activity.getDurationInMinutes()}min)" }
                activity
            } else {
                logger.debug { "Activity is not a cycling activity: ${activity.type}" }
                null
            }
        }.onFailure { e ->
            logger.error(e) { "Failed to fetch activity $activityId from Strava: ${e.message}" }
        }
    }

    fun fetchActivity(activityId: Long): Result<StravaActivity> {
        return stravaAuthService.getValidCredentials().mapCatching { _ ->
            val activity = stravaClient.getActivity(activityId)
            logger.info { "Fetched activity: ${activity.name}" }
            activity
        }.onFailure { e ->
            logger.error(e) { "Failed to fetch activity $activityId from Strava: ${e.message}" }
        }
    }

    fun getRecentActivities(limit: Int = 10): Result<String> {

        return stravaAuthService.getValidCredentials().mapCatching { _ ->
            val activities = stravaClient.getAthleteActivities(perPage = limit, page = 1)
                .take(limit)

            if (activities.isEmpty()) {
                logger.info { "No recent activities found" }
                "No recent activities found"
            } else {
                logger.info { "Found ${activities.size} recent activities" }
                formatActivitiesForAgent(activities)
            }
        }.onFailure { e ->
            logger.error(e) { "Failed to fetch recent activities: ${e.message}" }
        }
    }

    fun formatActivityDetails(activity: StravaActivity): String {
        return buildString {
            appendLine("New sports activity completed:")
            appendLine("Activity: ${activity.name}")
            appendLine("Distance: ${String.format("%.2f", activity.getDistanceInKm())} km")
            appendLine("Duration: ${activity.getDurationInMinutes()} minutes")
            appendLine("Average Speed: ${String.format("%.1f", activity.getAverageSpeedInKmh())} km/h")
            appendLine("Max Speed: ${String.format("%.1f", activity.getMaxSpeedInKmh())} km/h")
            appendLine("Elevation Gain: ${String.format("%.0f", activity.elevationGain)} m")
            activity.averageHeartrate?.let { appendLine("Average Heart Rate: ${it.toInt()} bpm") }
            activity.averageWatts?.let { appendLine("Average Power: ${it.toInt()} watts") }
            activity.calories?.let { appendLine("Calories: ${it.toInt()} kcal") }
            if (activity.commute) appendLine("Type: Commute")
            activity.description?.let { if (it.isNotBlank()) appendLine("Description: $it") }
        }
    }

    private fun formatActivitiesForAgent(activities: List<StravaActivity>): String {
        return buildString {
            appendLine("Recent activities:")
            appendLine()
            activities.forEachIndexed { index, activity ->
                appendLine("${index + 1}. ${activity.name}")
                appendLine("   Type: ${activity.type}")
                appendLine("   Distance: ${activity.getDistanceInKm()}km")
                appendLine("   Duration: ${activity.getDurationInMinutes()}min")
                appendLine("   Avg Speed: ${String.format("%.1f", activity.getAverageSpeedInKmh())}km/h")
                appendLine("   Elevation: ${activity.elevationGain.toInt()}m")
                appendLine("   Date: ${activity.startDate}")
                if (activity.averageHeartrate != null) {
                    appendLine("   Avg HR: ${activity.averageHeartrate.toInt()}bpm")
                }
                appendLine()
            }
        }
    }
}

