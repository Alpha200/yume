package eu.sendzik.yume.service.strava.model

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.annotation.JsonProperty
import java.time.Instant

@JsonIgnoreProperties(ignoreUnknown = true)
data class StravaActivity(
    @JsonProperty("id")
    val id: Long,
    @JsonProperty("name")
    val name: String,
    @JsonProperty("type")
    val type: String,
    @JsonProperty("sport_type")
    val sportType: String? = null,
    @JsonProperty("distance")
    val distance: Double,
    @JsonProperty("elapsed_time")
    val elapsedTime: Int,
    @JsonProperty("moving_time")
    val movingTime: Int,
    @JsonProperty("elevation_gain")
    val elevationGain: Double,
    @JsonProperty("start_date")
    val startDate: Instant,
    @JsonProperty("start_date_local")
    val startDateLocal: Instant? = null,
    @JsonProperty("timezone")
    val timezone: String? = null,
    @JsonProperty("average_speed")
    val averageSpeed: Double,
    @JsonProperty("max_speed")
    val maxSpeed: Double,
    @JsonProperty("average_watts")
    val averageWatts: Double? = null,
    @JsonProperty("weighted_average_watts")
    val weightedAverageWatts: Double? = null,
    @JsonProperty("average_heartrate")
    val averageHeartrate: Double? = null,
    @JsonProperty("max_heartrate")
    val maxHeartrate: Double? = null,
    @JsonProperty("average_cadence")
    val averageCadence: Double? = null,
    @JsonProperty("average_temp")
    val averageTemp: Double? = null,
    @JsonProperty("calories")
    val calories: Double? = null,
    @JsonProperty("description")
    val description: String? = null,
    @JsonProperty("commute")
    val commute: Boolean = false,
    @JsonProperty("trainer")
    val trainer: Boolean = false,
    @JsonProperty("manual")
    val manual: Boolean = false,
    @JsonProperty("private")
    val private: Boolean = false,
    @JsonProperty("flagged")
    val flagged: Boolean = false,
    @JsonProperty("start_latlng")
    val startLatlng: List<Double>? = null,
    @JsonProperty("end_latlng")
    val endLatlng: List<Double>? = null,
) {
    fun isCyclingActivity(): Boolean {
        return type == "Ride" || sportType == "Ride" || 
               type == "MountainBikeRide" || sportType == "MountainBikeRide" ||
               type == "GravelRide" || sportType == "GravelRide" ||
               type == "EBikeRide" || sportType == "EBikeRide"
    }

    fun getDistanceInKm(): Double = distance / 1000

    fun getDurationInMinutes(): Int = movingTime / 60

    fun getAverageSpeedInKmh(): Double = averageSpeed * 3.6

    fun getMaxSpeedInKmh(): Double = maxSpeed * 3.6
}
