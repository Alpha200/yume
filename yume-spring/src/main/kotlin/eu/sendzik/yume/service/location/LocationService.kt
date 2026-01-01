package eu.sendzik.yume.service.location

import eu.sendzik.yume.client.HomeAssistantClient
import eu.sendzik.yume.client.NominatimClient
import eu.sendzik.yume.service.location.model.UserLocation
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.cache.annotation.Cacheable
import org.springframework.stereotype.Service

@Service
class LocationService(
    private val reverseGeocodingService: ReverseGeocodingService,
    private val locationRetrieverService: LocationRetrieverService,
) {
    fun getCurrentLocationFormatted() = buildString {
        appendLine("Current location of user:")
        val userLocation = locationRetrieverService.getCurrentLocationCoordinates()

        if (userLocation != null) {
            val locationDetails = reverseGeocodingService.reverseGeocode(
                userLocation.latitude,
                userLocation.longitude
            )

            appendLine("Geofence: ${userLocation.geofence}")
            appendLine("Place: ${locationDetails ?: "Unknown location"}")
        } else {
            appendLine("Location data is not available.")
        }
    }
}