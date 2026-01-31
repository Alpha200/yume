package eu.sendzik.yume.service.location

import eu.sendzik.yume.configuration.HomeLocationConfiguration
import org.springframework.stereotype.Service
import kotlin.math.*

@Service
class LocationService(
    private val reverseGeocodingService: ReverseGeocodingService,
    private val locationRetrieverService: LocationRetrieverService,
    private val homeLocationConfiguration: HomeLocationConfiguration,
) {
    fun getCurrentLocationFormatted(): Result<String> {
        return locationRetrieverService.getCurrentLocationCoordinates().mapCatching { userLocation ->
            val place = reverseGeocodingService.reverseGeocode(
                userLocation.latitude,
                userLocation.longitude
            )
            Pair(place, userLocation)
        }.map { (place, userLocation) ->
            buildString {
                appendLine("Current geofence: ${userLocation.geofence}")
                appendLine("Current place: ${place ?: "Unknown location"}")

                if (isHomeLocationValid()) {
                    val distanceKm = calculateDistanceToHome(userLocation.latitude, userLocation.longitude)
                    if (distanceKm > 0.2) {
                        appendLine("Distance to home: ${"%.2f".format(distanceKm)} km")
                    }
                }
            }
        }
    }

    private fun isHomeLocationValid(): Boolean {
        return !(homeLocationConfiguration.latitude == 0.0 && homeLocationConfiguration.longitude == 0.0)
    }

    private fun calculateDistanceToHome(currentLat: Double, currentLng: Double): Double {
        val earthRadiusKm = 6371.0
        val dLat = Math.toRadians(homeLocationConfiguration.latitude - currentLat)
        val dLng = Math.toRadians(homeLocationConfiguration.longitude - currentLng)

        val a = sin(dLat / 2) * sin(dLat / 2) +
                cos(Math.toRadians(currentLat)) * cos(Math.toRadians(homeLocationConfiguration.latitude)) *
                sin(dLng / 2) * sin(dLng / 2)

        val c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return earthRadiusKm * c
    }
}