package eu.sendzik.yume.service.weather

import eu.sendzik.yume.client.OpenWeatherMapClient
import eu.sendzik.yume.service.location.LocationRetrieverService
import eu.sendzik.yume.service.location.LocationService
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class WeatherService(
    private val locationRetrieverService: LocationRetrieverService,
    private val openWeatherMapClient: OpenWeatherMapClient,
    private val logger: KLogger,
    @Value("\${yume.weather.openweathermap.appid}")
    private val appId: String,
) {
    fun getWeatherForecast(maxHourlyForecasts: Int = 24): String? {
        val location = locationRetrieverService.getCurrentLocationCoordinates()

        if (location == null) {
            logger.error { "Unable to fetch weather forecast: user location is unknown." }
            return null
        }

        val weatherData = openWeatherMapClient.oneCall(
            appId = appId,
            latitude = location.latitude,
            longitude = location.longitude
        )

        return buildString {
            appendLine("# Weather Forecast")
            appendLine()
            appendLine("Current weather:")
            append("Temp: ${weatherData.current.temp}°C")
            append(" - ")
            append("Condition: ${weatherData.current.weather.joinToString { it.description }}")
            append(" - ")
            appendLine("Wind speed: ${weatherData.current.windSpeed} m/s")
            appendLine()
            appendLine("Hourly forecast:")

            for (hourly in weatherData.hourly) {
                val timestamp = java.time.Instant.ofEpochSecond(hourly.dt)
                    .atZone(java.time.ZoneId.systemDefault())
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