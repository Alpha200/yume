package eu.sendzik.yume.repository.scheduler

import eu.sendzik.yume.repository.scheduler.model.SchedulerRun
import eu.sendzik.yume.repository.scheduler.model.SchedulerRunStatus
import org.springframework.data.domain.Pageable
import org.springframework.data.mongodb.repository.MongoRepository
import org.springframework.data.mongodb.repository.Query
import org.springframework.data.mongodb.repository.Update
import org.springframework.stereotype.Repository

@Repository
interface SchedulerRunRepository : MongoRepository<SchedulerRun, String> {
    
    fun findByOrderByUpdatedAtDesc(pageable: Pageable): List<SchedulerRun>
    
    fun findByStatusOrderByUpdatedAtDesc(status: SchedulerRunStatus, pageable: Pageable): List<SchedulerRun>

    fun findByTopicOrderByUpdatedAtDesc(topic: String, pageable: Pageable): List<SchedulerRun>
    
    @Query("{ 'status': 'failed' }")
    fun findFailedRuns(pageable: Pageable): List<SchedulerRun>

    @Query("{ 'status': 'scheduled' }")
    @Update($$"{ '$set': { 'status': 'cancelled', 'updated_at': ?#{T(java.time.LocalDateTime).now()} } }")
    fun cancelAllScheduledRuns()
}
