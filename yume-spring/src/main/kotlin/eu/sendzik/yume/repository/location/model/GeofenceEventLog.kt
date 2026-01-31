package eu.sendzik.yume.repository.location.model

import org.springframework.data.annotation.Id
import org.springframework.data.annotation.TypeAlias
import org.springframework.data.mongodb.core.mapping.Document
import org.springframework.data.mongodb.core.mapping.Field
import java.time.LocalDateTime

@TypeAlias("GeofenceEventLog")
@Document(collection = "geofence_event_logs")
data class GeofenceEventLog(
    @field:Id val id: String,
    @field:Field("geofence_name") val geofenceName: String,
    @field:Field("event_type") val eventType: String,  // "enter" or "exit"
    @field:Field("execution_summary") val executionSummary: String?,  // What the agent decided to do
    @field:Field("triggered_at") val triggeredAt: LocalDateTime = LocalDateTime.now(),
)
