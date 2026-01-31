package eu.sendzik.yume.service.location

import eu.sendzik.yume.repository.location.GeofenceEventLogRepository
import eu.sendzik.yume.repository.location.model.GeofenceEventLog
import eu.sendzik.yume.utils.formatTimestampForLLM
import org.springframework.data.domain.PageRequest
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.util.UUID

@Service
class GeofenceEventLogService(
    private val geofenceEventLogRepository: GeofenceEventLogRepository,
) {

    fun logGeofenceEvent(
        geofenceName: String,
        eventType: String,
        executionSummary: String?
    ): GeofenceEventLog {
        val log = GeofenceEventLog(
            id = UUID.randomUUID().toString(),
            geofenceName = geofenceName,
            eventType = eventType,
            executionSummary = executionSummary,
            triggeredAt = LocalDateTime.now()
        )
        return geofenceEventLogRepository.save(log)
    }

    fun getRecentEvents(limit: Int = 20): List<GeofenceEventLog> {
        val pageable = PageRequest.of(0, limit)
        return geofenceEventLogRepository.findByOrderByTriggeredAtDesc(pageable)
    }

    fun getRecentEventsFormatted(limit: Int): String {
        val recentEvents = getRecentEvents(limit)
        return recentEvents.joinToString("\n---\n") {
            buildString {
                appendLine("- Time: ${formatTimestampForLLM(it.triggeredAt)}")
                appendLine("  Location: ${it.geofenceName} (${it.eventType})")
                if (!it.executionSummary.isNullOrBlank()) {
                    appendLine("  Outcome: ${it.executionSummary}")
                }
            }.trimEnd()
        }
    }
}
