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
    @JsonProperty("total_elevation_gain")
    val totalElevationGain: Double,
    @JsonProperty("elev_high")
    val elevHigh: Double? = null,
    @JsonProperty("elev_low")
    val elevLow: Double? = null,
    @JsonProperty("start_date")
    val startDate: Instant,
    @JsonProperty("start_date_local")
    val startDateLocal: Instant? = null,
    @JsonProperty("timezone")
    val timezone: String? = null,
    @JsonProperty("start_latlng")
    val startLatlng: List<Double>? = null,
    @JsonProperty("end_latlng")
    val endLatlng: List<Double>? = null,
    @JsonProperty("achievement_count")
    val achievementCount: Int? = null,
    @JsonProperty("kudos_count")
    val kudosCount: Int? = null,
    @JsonProperty("comment_count")
    val commentCount: Int? = null,
    @JsonProperty("athlete_count")
    val athleteCount: Int? = null,
    @JsonProperty("photo_count")
    val photoCount: Int? = null,
    @JsonProperty("total_photo_count")
    val totalPhotoCount: Int? = null,
    @JsonProperty("device_name")
    val deviceName: String? = null,
    @JsonProperty("trainer")
    val trainer: Boolean = false,
    @JsonProperty("commute")
    val commute: Boolean = false,
    @JsonProperty("manual")
    val manual: Boolean = false,
    @JsonProperty("private")
    val private: Boolean = false,
    @JsonProperty("flagged")
    val flagged: Boolean = false,
    @JsonProperty("workout_type")
    val workoutType: Int? = null,
    @JsonProperty("external_id")
    val externalId: String? = null,
    @JsonProperty("upload_id")
    val uploadId: Long? = null,
    @JsonProperty("upload_id_str")
    val uploadIdStr: String? = null,
    @JsonProperty("average_speed")
    val averageSpeed: Double,
    @JsonProperty("max_speed")
    val maxSpeed: Double,
    @JsonProperty("has_kudoed")
    val hasKudoed: Boolean? = null,
    @JsonProperty("hide_from_home")
    val hideFromHome: Boolean? = null,
    @JsonProperty("gear_id")
    val gearId: String? = null,
    @JsonProperty("kilojoules")
    val kilojoules: Double? = null,
    @JsonProperty("average_watts")
    val averageWatts: Double? = null,
    @JsonProperty("device_watts")
    val deviceWatts: Boolean? = null,
    @JsonProperty("max_watts")
    val maxWatts: Int? = null,
    @JsonProperty("weighted_average_watts")
    val weightedAverageWatts: Int? = null,
    // Present in SummaryActivity examples but not formally defined in the schema
    @JsonProperty("average_heartrate")
    val averageHeartrate: Double? = null,
    @JsonProperty("max_heartrate")
    val maxHeartrate: Double? = null,
    @JsonProperty("average_cadence")
    val averageCadence: Double? = null,
    @JsonProperty("average_temp")
    val averageTemp: Double? = null, // not in spec, but returned in practice
    // DetailedActivity fields (only present when fetching a single activity)
    @JsonProperty("calories")
    val calories: Double? = null,
    @JsonProperty("description")
    val description: String? = null,
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
