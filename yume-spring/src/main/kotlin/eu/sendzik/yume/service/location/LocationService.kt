package eu.sendzik.yume.service.location

import eu.sendzik.yume.client.HomeAssistantClient
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.cache.annotation.Cacheable
import org.springframework.stereotype.Service

@Service
class LocationService(
    private val homeAssistantClient: HomeAssistantClient,
    @Value("\${yume.home-assistant.person.entity-id}")
    private val userEntityId: String,
    private val logger: KLogger,
) {
    fun getCurrentLocationFormatted() = buildString {
        appendLine("Current Location:")
        // TODO: Implement
        appendLine("Unknown")
    }

    @Cacheable("UserLocation", unless = "#result == null")
    fun getCurrentLocationCoordinates(): Pair<Double, Double>? {
        try {
            val location = homeAssistantClient.getStateForEntity(userEntityId)

            val latitude = location.attributes["latitude"] as? Double
            val longitude = location.attributes["longitude"] as? Double

            if (latitude == null || longitude == null) {
                logger.warn { "Location attributes are missing latitude or longitude!" }
                return null
            } else {
                return Pair(latitude, longitude)
            }
        } catch (ex: RuntimeException) {
            logger.error { "Failed to fetch user location: ${ex.message}" }
            return null
        }
    }

}