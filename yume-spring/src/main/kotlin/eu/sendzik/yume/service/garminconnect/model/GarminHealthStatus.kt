package eu.sendzik.yume.service.garminconnect.model

import java.time.Instant
import java.time.LocalDateTime

data class GarminHealthStatus(
    val trainingBalance: TrainingBalance,
    val trainingStatus: TrainingStatus,
    val sleepStatus: SleepStatus,
    val dailySummary: DailySummary,
    val heartRateVariability: HeartRateVariability,
) {
    @Suppress("UNCHECKED_CAST")
    companion object {
        fun fromApi(result: Map<String, Any>): GarminHealthStatus {
            // Extract TrainingBalance from myDayTrainingStatus
            val trainingBalance = extractTrainingBalance(result)

            // Extract TrainingStatus from myDayTrainingStatus
            val trainingStatus = extractTrainingStatus(result)

            // Extract SleepStatus from DailySleeps
            val sleepStatus = extractSleepStatus(result)

            // Extract DailySummary from UserDailySummaryList
            val dailySummary = extractDailySummary(result)

            // Extract HeartRateVariability from HrvStatusSummary
            val heartRateVariability = extractHeartRateVariability(result)

            return GarminHealthStatus(
                trainingBalance = trainingBalance,
                trainingStatus = trainingStatus,
                sleepStatus = sleepStatus,
                dailySummary = dailySummary,
                heartRateVariability = heartRateVariability,
            )
        }

        private fun extractTrainingBalance(result: Map<String, Any>): TrainingBalance {
            val myDayTrainingStatus = result["myDayTrainingStatus"] as? Map<String, Any> ?: emptyMap()
            val payload = myDayTrainingStatus["payload"] as? Map<String, Any> ?: emptyMap()
            val mostRecentTrainingLoadBalance = payload["mostRecentTrainingLoadBalance"] as? Map<String, Any> ?: emptyMap()
            val metricsTrainingLoadBalanceDTOMap = mostRecentTrainingLoadBalance["metricsTrainingLoadBalanceDTOMap"] as? Map<String, Any> ?: emptyMap()

            val trainingBalanceFeedback = metricsTrainingLoadBalanceDTOMap.values.firstNotNullOfOrNull { device ->
                (device as? Map<String, Any>)?.get("trainingBalanceFeedbackPhrase") as? String
            } ?: "UNKNOWN"

            return TrainingBalance(trainingBalanceFeedback = trainingBalanceFeedback)
        }

        private fun extractTrainingStatus(result: Map<String, Any>): TrainingStatus {
            val myDayTrainingStatus = result["myDayTrainingStatus"] as? Map<String, Any> ?: emptyMap()
            val payload = myDayTrainingStatus["payload"] as? Map<String, Any> ?: emptyMap()
            val mostRecentTrainingStatus = payload["mostRecentTrainingStatus"] as? Map<String, Any> ?: emptyMap()
            val latestTrainingStatusData = mostRecentTrainingStatus["latestTrainingStatusData"] as? Map<String, Any> ?: emptyMap()

            val trainingStatusData = latestTrainingStatusData.values.firstNotNullOfOrNull { data ->
                data as? Map<String, Any>
            } ?: emptyMap()

            val trainingStatusFeedback = trainingStatusData["trainingStatusFeedbackPhrase"] as? String ?: "UNKNOWN"
            val acuteTrainingLoadDTO = trainingStatusData["acuteTrainingLoadDTO"] as? Map<String, Any> ?: emptyMap()
            val acuteTrainingLoad = acuteTrainingLoadDTO["acwrStatus"] as? String ?: "UNKNOWN"

            return TrainingStatus(
                trainingStatusFeedback = trainingStatusFeedback,
                acuteTrainingLoad = acuteTrainingLoad,
            )
        }

        private fun extractSleepStatus(result: Map<String, Any>): SleepStatus {
            val dailySleeps = result["DailySleeps"] as? Map<String, Any> ?: emptyMap()
            val payload = dailySleeps["payload"] as? List<Map<String, Any>> ?: emptyList()

            val sleepData = payload.firstOrNull() ?: emptyMap()

            val sleepScores = sleepData["sleepScores"] as? Map<String, Any> ?: emptyMap()
            val overall = (sleepScores["overall"] as? Map<String, Any>)?.get("value") as? Int ?: 0
            val totalDuration = (sleepScores["totalDuration"] as? Map<String, Any>)?.get("qualifierKey") as? String ?: "UNKNOWN"
            val deepPercentage = (sleepScores["deepPercentage"] as? Map<String, Any>)?.get("qualifierKey") as? String ?: "UNKNOWN"
            val lightPercentage = (sleepScores["lightPercentage"] as? Map<String, Any>)?.get("qualifierKey") as? String ?: "UNKNOWN"
            val remPercentage = (sleepScores["remPercentage"] as? Map<String, Any>)?.get("qualifierKey") as? String ?: "UNKNOWN"
            val awakeCount = (sleepScores["awakeCount"] as? Map<String, Any>)?.get("qualifierKey") as? String ?: "UNKNOWN"
            val stress = (sleepScores["stress"] as? Map<String, Any>)?.get("qualifierKey") as? String ?: "UNKNOWN"
            val restlessness = (sleepScores["restlessness"] as? Map<String, Any>)?.get("qualifierKey") as? String ?: "UNKNOWN"

            val sleepTimeSeconds = sleepData["sleepTimeSeconds"] as? Int ?: 0
            val sleepTimeMinutes = sleepTimeSeconds / 60

            // Extract sleep start and end timestamps (Unix milliseconds -> Instant)
            val sleepStartTimestampGMT = (sleepData["sleepStartTimestampGMT"] as? Long)?.let { Instant.ofEpochMilli(it) }
            val sleepEndTimestampGMT = (sleepData["sleepEndTimestampGMT"] as? Long)?.let { Instant.ofEpochMilli(it) }

            // Extract naps information
            val napTimeSeconds = sleepData["napTimeSeconds"] as? Int ?: 0
            val napTimeMinutes = napTimeSeconds / 60
            val dailyNapDTOS = sleepData["dailyNapDTOS"] as? List<Map<String, Any>> ?: emptyList()
            val naps = dailyNapDTOS.mapNotNull { napData ->
                val napStartTimestamp = napData["napStartTimestampGMT"] as? String
                val napEndTimestamp = napData["napEndTimestampGMT"] as? String
                val napDurationSeconds = napData["napTimeSec"] as? Int ?: 0
                val napFeedback = napData["napFeedback"] as? String ?: "UNKNOWN"

                if (napStartTimestamp != null && napEndTimestamp != null) {
                    // Parse ISO 8601 timestamps to LocalDateTime
                    val startDateTime = LocalDateTime.parse(napStartTimestamp)
                    val endDateTime = LocalDateTime.parse(napEndTimestamp)

                    Nap(
                        startTimestamp = startDateTime,
                        endTimestamp = endDateTime,
                        durationMinutes = napDurationSeconds / 60,
                        feedback = napFeedback,
                    )
                } else {
                    null
                }
            }

            return SleepStatus(
                overallSleepScore = overall,
                sleepStartTimestampGMT = sleepStartTimestampGMT,
                sleepEndTimestampGMT = sleepEndTimestampGMT,
                sleepScores = SleepScores(
                    overall = overall.toString(),
                    sleepTimeMinutes = sleepTimeMinutes,
                    deepPercentage = deepPercentage,
                    lightPercentage = lightPercentage,
                    remPercentage = remPercentage,
                    totalDuration = totalDuration,
                    awakeCount = awakeCount,
                    stress = stress,
                    restlessness = restlessness,
                ),
                napTimeMinutes = napTimeMinutes,
                naps = naps,
            )
        }

        private fun extractDailySummary(result: Map<String, Any>): DailySummary {
            val userDailySummaryList = result["UserDailySummaryList"] as? Map<String, Any> ?: emptyMap()
            val payload = userDailySummaryList["payload"] as? List<Map<String, Any>> ?: emptyList()

            val dailySummaryData = payload.firstOrNull() ?: emptyMap()

            val totalSteps = dailySummaryData["totalSteps"] as? Int ?: 0
            val moderateIntensityMinutes = dailySummaryData["moderateIntensityMinutes"] as? Int ?: 0
            val vigorousIntensityMinutes = dailySummaryData["vigorousIntensityMinutes"] as? Int ?: 0
            val bodyBatteryMostRecentValue = dailySummaryData["bodyBatteryMostRecentValue"] as? Int ?: 0

            return DailySummary(
                totalSteps = totalSteps,
                moderateIntensityMinutes = moderateIntensityMinutes,
                vigorousIntensityMinutes = vigorousIntensityMinutes,
                bodyBatteryMostRecentValue = bodyBatteryMostRecentValue,
            )
        }

        private fun extractHeartRateVariability(result: Map<String, Any>): HeartRateVariability {
            val hrvStatusSummary = result["HrvStatusSummary"] as? Map<String, Any> ?: emptyMap()
            val payload = hrvStatusSummary["payload"] as? Map<String, Any> ?: emptyMap()
            val hrvSummaries = payload["hrvSummaries"] as? List<Map<String, Any>> ?: emptyList()

            val hrvData = hrvSummaries.firstOrNull() ?: emptyMap()
            val status = hrvData["status"] as? String ?: "UNKNOWN"

            return HeartRateVariability(heartRateVariabilityStatus = status)
        }
    }
}

data class TrainingBalance(
    val trainingBalanceFeedback: String,
)

data class TrainingStatus(
    val trainingStatusFeedback: String,
    val acuteTrainingLoad: String,
)

data class SleepStatus(
    val overallSleepScore: Int,
    val sleepStartTimestampGMT: Instant?,
    val sleepEndTimestampGMT: Instant?,
    val sleepScores: SleepScores,
    val napTimeMinutes: Int,
    val naps: List<Nap>,
)

data class SleepScores(
    val overall: String,
    val sleepTimeMinutes: Int,
    val deepPercentage: String,
    val lightPercentage: String,
    val remPercentage: String,
    val totalDuration: String,
    val awakeCount: String,
    val stress: String,
    val restlessness: String,
)

data class DailySummary(
    val totalSteps: Int,
    val moderateIntensityMinutes: Int,
    val vigorousIntensityMinutes: Int,
    val bodyBatteryMostRecentValue: Int,
)

data class HeartRateVariability(
    val heartRateVariabilityStatus: String,
)

data class Nap(
    val startTimestamp: LocalDateTime,
    val endTimestamp: LocalDateTime,
    val durationMinutes: Int,
    val feedback: String,
)
