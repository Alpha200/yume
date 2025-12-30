package eu.sendzik.yume.service.weather

import eu.sendzik.yume.client.OpenWeatherMapClient
import eu.sendzik.yume.service.location.LocationService
import eu.sendzik.yume.utils.formatTimestampForLLM
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class WeatherService(
    private val locationService: LocationService,
    private val openWeatherMapClient: OpenWeatherMapClient,
    @Value("\${yume.weather.openweathermap.appid}")
    private val appId: String,
) {
    fun getWeatherForecast(): String {
        val location = locationService.getCurrentLocationCoordinates()
        val weatherData = openWeatherMapClient.oneCall(appId = appId, latitude = location?.first ?: 0.0, longitude = location?.second ?: 0.0)

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

                append("Time: ${formatTimestampForLLM(timestamp)}")
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