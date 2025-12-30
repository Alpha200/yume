package eu.sendzik.yume.client.model

import com.fasterxml.jackson.annotation.JsonProperty

data class OpenWeatherMapOneCallResult(
    val current: OpenWeatherMapHourlyForecast,
    val hourly: List<OpenWeatherMapHourlyForecast>
)

data class OpenWeatherMapHourlyForecast(
    val dt: Long,
    val temp: Double,
    @JsonProperty("wind_speed")
    val windSpeed: Double,
    val weather: List<OpenWeatherMapWeatherDescription>
)

data class OpenWeatherMapWeatherDescription(
    val main: String,
    val description: String,
)
