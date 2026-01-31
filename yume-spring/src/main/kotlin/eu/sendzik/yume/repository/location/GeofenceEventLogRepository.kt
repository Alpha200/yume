package eu.sendzik.yume.repository.location

import eu.sendzik.yume.repository.location.model.GeofenceEventLog
import org.springframework.data.domain.Pageable
import org.springframework.data.mongodb.repository.MongoRepository

interface GeofenceEventLogRepository : MongoRepository<GeofenceEventLog, String> {
    fun findByOrderByTriggeredAtDesc(pageable: Pageable): List<GeofenceEventLog>
}
