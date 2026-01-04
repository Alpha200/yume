package eu.sendzik.yume.service.location.model

import com.fasterxml.jackson.annotation.JsonProperty

data class GeofenceEventRequest(
    val geofenceName: String,
    val eventType: GeofenceEventType,
)

enum class GeofenceEventType {
    @JsonProperty("enter")
    ENTER,
    @JsonProperty("leave")
    LEAVE,
}
