package eu.sendzik.yume.service.location

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