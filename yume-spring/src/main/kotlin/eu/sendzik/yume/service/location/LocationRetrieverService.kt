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
    @Value("\${yume.home-assistant.person.entity-id}")
    private val userEntityId: String,
) {
    @Cacheable("UserLocation", unless = "#result.isFailure")
    fun getCurrentLocationCoordinates(): Result<UserLocation> {
        return runCatching {
            homeAssistantClient.getStateForEntity(userEntityId)
        }.mapCatching { location ->
            val latitude = location.attributes["latitude"] as? Double
            val longitude = location.attributes["longitude"] as? Double
            val geofence = location.state

            if (latitude == null || longitude == null) {
                throw RuntimeException("Location attributes are missing latitude or longitude.")
            } else {
                UserLocation(
                    geofence = geofence,
                    latitude = latitude,
                    longitude = longitude,
                )
            }
        }
    }
}