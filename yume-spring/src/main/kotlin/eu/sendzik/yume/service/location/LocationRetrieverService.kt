package eu.sendzik.yume.service.location

import eu.sendzik.yume.client.HomeAssistantClient
import eu.sendzik.yume.service.location.model.UserLocation
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.cache.annotation.Cacheable
import org.springframework.stereotype.Service

@Service
class LocationRetrieverService(
    private val homeAssistantClient: HomeAssistantClient,
    private val logger: KLogger,
    @Value("\${yume.home-assistant.person.entity-id}")
    private val userEntityId: String,
) {
    @Cacheable("UserLocation", unless = "#result == null")
    fun getCurrentLocationCoordinates(): UserLocation? {
        try {
            val location = homeAssistantClient.getStateForEntity(userEntityId)

            val latitude = location.attributes["latitude"] as? Double
            val longitude = location.attributes["longitude"] as? Double
            val geofence = location.state

            if (latitude == null || longitude == null) {
                logger.warn { "Location attributes are missing latitude or longitude!" }
                return null
            } else {
                return UserLocation(
                    geofence = geofence,
                    latitude = latitude,
                    longitude = longitude,
                )
            }
        } catch (ex: RuntimeException) {
            logger.error { "Failed to fetch user location: ${ex.message}" }
            return null
        }
    }
}