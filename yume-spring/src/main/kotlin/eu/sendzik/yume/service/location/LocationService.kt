package eu.sendzik.yume.service.location

import org.springframework.stereotype.Service

@Service
class LocationService {
    fun getCurrentLocationFormatted() = buildString {
        appendLine("Current Location:")
        // TODO: Implement
        appendLine("Unknown")
    }
}