package eu.sendzik.yume.service.garminconnect

import eu.sendzik.yume.service.garminconnect.model.GarminHealthStatus
import jakarta.annotation.PostConstruct
import org.springframework.stereotype.Service
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@Service
class GarminConnectService(
    private val garminConnectDataFetcherService: GarminConnectDataFetcherService,
) {
    private val dateTimeFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")

    fun getFormattedHealthSnapshot(): Result<String> {
        return garminConnectDataFetcherService.getSnapshot().map { healthStatus ->
            if (healthStatus != null) {
                formatHealthStatus(healthStatus)
            } else {
                "No health data available"
            }
        }
    }

    private fun formatHealthStatus(healthStatus: GarminHealthStatus): String = buildString {
        appendLine("=== Training Balance ===")
        appendLine("Status: ${healthStatus.trainingBalance.trainingBalanceFeedback}")
        appendLine()

        appendLine("=== Training Status ===")
        appendLine("Status: ${healthStatus.trainingStatus.trainingStatusFeedback}")
        appendLine("Acute Training Load: ${healthStatus.trainingStatus.acuteTrainingLoad}")
        appendLine()

        appendLine("=== Sleep Summary ===")
        appendLine("Overall Sleep Score: ${healthStatus.sleepStatus.overallSleepScore}/100")

        if (healthStatus.sleepStatus.sleepStartTimestampGMT != null && healthStatus.sleepStatus.sleepEndTimestampGMT != null) {
            val startTime = healthStatus.sleepStatus.sleepStartTimestampGMT
                .atZone(ZoneId.systemDefault())
                .format(dateTimeFormatter)
            val endTime = healthStatus.sleepStatus.sleepEndTimestampGMT
                .atZone(ZoneId.systemDefault())
                .format(dateTimeFormatter)
            appendLine("Sleep Period: $startTime to $endTime")
        }

        appendLine("Total Sleep Duration: ${healthStatus.sleepStatus.sleepScores.sleepTimeMinutes} minutes")
        appendLine("Sleep Duration Quality: ${healthStatus.sleepStatus.sleepScores.totalDuration}")
        appendLine("Deep Sleep: ${healthStatus.sleepStatus.sleepScores.deepPercentage}")
        appendLine("Light Sleep: ${healthStatus.sleepStatus.sleepScores.lightPercentage}")
        appendLine("REM Sleep: ${healthStatus.sleepStatus.sleepScores.remPercentage}")
        appendLine("Awake Count: ${healthStatus.sleepStatus.sleepScores.awakeCount}")
        appendLine("Sleep Stress: ${healthStatus.sleepStatus.sleepScores.stress}")
        appendLine("Sleep Restlessness: ${healthStatus.sleepStatus.sleepScores.restlessness}")

        if (healthStatus.sleepStatus.napTimeMinutes > 0) {
            appendLine()
            appendLine("Total Nap Time: ${healthStatus.sleepStatus.napTimeMinutes} minutes")
            if (healthStatus.sleepStatus.naps.isNotEmpty()) {
                appendLine("Naps:")
                healthStatus.sleepStatus.naps.forEachIndexed { index, nap ->
                    val napStart = nap.startTimestamp.format(dateTimeFormatter)
                    val napEnd = nap.endTimestamp.format(dateTimeFormatter)
                    appendLine("  ${index + 1}. $napStart to $napEnd (${nap.durationMinutes} minutes) - ${nap.feedback}")
                }
            }
        }
        appendLine()

        appendLine("=== Daily Activity Summary ===")
        appendLine("Total Steps: ${healthStatus.dailySummary.totalSteps}")
        appendLine("Moderate Intensity Minutes: ${healthStatus.dailySummary.moderateIntensityMinutes}")
        appendLine("Vigorous Intensity Minutes: ${healthStatus.dailySummary.vigorousIntensityMinutes}")
        appendLine("Body Battery (Most Recent): ${healthStatus.dailySummary.bodyBatteryMostRecentValue}/100")
        appendLine()

        appendLine("=== Heart Rate Variability ===")
        appendLine("HRV Status: ${healthStatus.heartRateVariability.heartRateVariabilityStatus}")
    }
}

