package eu.sendzik.yume.service.weather

import eu.sendzik.yume.client.OpenWeatherMapClient
import eu.sendzik.yume.service.location.LocationRetrieverService
import eu.sendzik.yume.service.location.LocationService
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import java.time.Instant
import java.time.ZoneId

@Service
class WeatherService(
    private val locationRetrieverService: LocationRetrieverService,
    private val openWeatherMapClient: OpenWeatherMapClient,
    private val logger: KLogger,
    @Value("\${yume.weather.openweathermap.appid}")
    private val appId: String,
) {
    fun getWeatherForecast(maxHourlyForecasts: Int = 24): Result<String> {
        return locationRetrieverService.getCurrentLocationCoordinates().onFailure {
            logger.error(it) { "Failed to retrieve user location for weather forecast." }
        }.mapCatching { location ->
            openWeatherMapClient.oneCall(
                appId = appId,
                latitude = location.latitude,
                longitude = location.longitude
            )
        }.onFailure {
            logger.error(it) { "Failed to retrieve weather forecast from OpenWeatherMap." }
        }.map { weatherData ->
            buildString {
                appendLine("Current weather:")
                append("Temp: ${weatherData.current.temp}°C")
                append(" - ")
                append("Condition: ${weatherData.current.weather.joinToString { it.description }}")
                append(" - ")
                appendLine("Wind speed: ${weatherData.current.windSpeed} m/s")
                appendLine()
                appendLine("Hourly forecast:")

                for (hourly in weatherData.hourly) {
                    val timestamp = Instant.ofEpochSecond(hourly.dt)
                        .atZone(ZoneId.systemDefault())
                        .toLocalDateTime()

                    append(formatTimestampForLLM(timestamp, timeOnly = maxHourlyForecasts <= 24))
                    append(" - ")
                    append("Temp: ${hourly.temp}°C")
                    append(" - ")
                    append("Condition: ${hourly.weather.joinToString { it.description }}")
                    append(" - ")
                    appendLine("Wind speed: ${hourly.windSpeed} m/s")
                }
            }
        }
    }
}