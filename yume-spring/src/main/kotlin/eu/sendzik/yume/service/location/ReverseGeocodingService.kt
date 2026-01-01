package eu.sendzik.yume.service.location

import eu.sendzik.yume.client.NominatimClient
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.cache.annotation.Cacheable
import org.springframework.stereotype.Service

@Service
class ReverseGeocodingService(
    private val nominatimClient: NominatimClient,
    private val logger: KLogger,
) {
    @Cacheable("ReverseGeocodedLocation", unless = "#result == null")
    fun reverseGeocode(latitude: Double, longitude: Double): String? {
        return try {
            val result = nominatimClient.reverseGeocode(latitude, longitude)

            val resultList: MutableList<String> = mutableListOf()

            if (result.address.containsKey("city")) {
                resultList.add(result.address["city"]!!)
            } else if (result.address.containsKey("town")) {
                resultList.add(result.address["town"]!!)
            } else if (result.address.containsKey("village")) {
                resultList.add(result.address["village"]!!)
            }

            if (result.address.containsKey("country")) {
                resultList.add(result.address["country"]!!)
            }

            return resultList.joinToString(", ")
        } catch (ex: RuntimeException) {
            logger.error { "Failed to reverse geocode coordinates ($latitude, $longitude): ${ex.message}" }
            null
        }
    }
}