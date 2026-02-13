package eu.sendzik.yume.service.garminconnect.model

import com.fasterxml.jackson.databind.ObjectMapper
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import java.nio.file.Files
import java.nio.file.Paths

class GarminHealthStatusTest {
    @Test
    fun testGarminConnectHealthStatusParsing() {
        val objectMapper = ObjectMapper()

        // Read test data from garmin-test-data.json
        val testDataPath = Paths.get("src/test/kotlin/eu/sendzik/yume/garmin-test-data.json")
        val rawData = Files.readString(testDataPath)

        // Parse the raw data into a Map
        @Suppress("UNCHECKED_CAST")
        val apiResponse = objectMapper.readValue(rawData, Map::class.java) as Map<String, Any>

        // Create GarminHealthStatus from API response
        val healthStatus = GarminHealthStatus.fromApi(apiResponse)

        // Assert training balance feedback
        assertNotNull(healthStatus.trainingBalance)
        assertNotNull(healthStatus.trainingBalance.trainingBalanceFeedback)
        assertNotEquals("", healthStatus.trainingBalance.trainingBalanceFeedback)

        // Assert training status
        assertNotNull(healthStatus.trainingStatus)
        assertNotNull(healthStatus.trainingStatus.trainingStatusFeedback)
        assertNotNull(healthStatus.trainingStatus.acuteTrainingLoad)

        // Assert sleep status
        assertNotNull(healthStatus.sleepStatus)
        assertNotNull(healthStatus.sleepStatus.sleepScores)
        assertTrue(healthStatus.sleepStatus.overallSleepScore >= 0)
        assertTrue(healthStatus.sleepStatus.sleepScores.sleepTimeMinutes >= 0)

        // Assert sleep timestamps
        assertNotNull(healthStatus.sleepStatus.sleepStartTimestampGMT, "Sleep start timestamp should not be null")
        assertNotNull(healthStatus.sleepStatus.sleepEndTimestampGMT, "Sleep end timestamp should not be null")

        // Verify timestamps are in correct order (start before end)
        if (healthStatus.sleepStatus.sleepStartTimestampGMT != null && healthStatus.sleepStatus.sleepEndTimestampGMT != null) {
            assertTrue(healthStatus.sleepStatus.sleepStartTimestampGMT.isBefore(healthStatus.sleepStatus.sleepEndTimestampGMT),
                "Sleep end timestamp should be after start timestamp")
        }

        // Assert nap information
        assertTrue(healthStatus.sleepStatus.napTimeMinutes >= 0, "Nap time minutes should be >= 0")
        assertNotNull(healthStatus.sleepStatus.naps, "Naps list should not be null")

        // If there are naps, verify their properties
        if (healthStatus.sleepStatus.naps.isNotEmpty()) {
            val nap = healthStatus.sleepStatus.naps[0]
            assertNotNull(nap.startTimestamp, "Nap start timestamp should not be null")
            assertNotNull(nap.endTimestamp, "Nap end timestamp should not be null")
            assertTrue(nap.durationMinutes >= 0, "Nap duration should be >= 0")
            assertNotNull(nap.feedback, "Nap feedback should not be null")
            assertTrue(nap.startTimestamp.isBefore(nap.endTimestamp), "Nap end timestamp should be after start timestamp")
        }

        // Assert daily summary
        assertNotNull(healthStatus.dailySummary)
        assertTrue(healthStatus.dailySummary.totalSteps >= 0)
        assertTrue(healthStatus.dailySummary.moderateIntensityMinutes >= 0)
        assertTrue(healthStatus.dailySummary.vigorousIntensityMinutes >= 0)
        assertTrue(healthStatus.dailySummary.bodyBatteryMostRecentValue >= 0)

        // Assert heart rate variability
        assertNotNull(healthStatus.heartRateVariability)
        assertNotNull(healthStatus.heartRateVariability.heartRateVariabilityStatus)
    }

}