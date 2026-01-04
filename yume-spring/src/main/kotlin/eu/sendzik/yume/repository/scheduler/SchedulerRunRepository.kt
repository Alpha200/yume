package eu.sendzik.yume.repository.scheduler

import eu.sendzik.yume.repository.scheduler.model.SchedulerRun
import org.springframework.data.mongodb.repository.MongoRepository
import org.springframework.data.mongodb.repository.Query
import org.springframework.stereotype.Repository
import java.time.LocalDateTime

@Repository
interface SchedulerRunRepository : MongoRepository<SchedulerRun, String> {
    
    fun findByOrderByUpdatedAtDesc(pageable: org.springframework.data.domain.Pageable): List<SchedulerRun>
    
    fun findByStatusOrderByUpdatedAtDesc(status: String, pageable: org.springframework.data.domain.Pageable): List<SchedulerRun>
    
    fun findByTopicOrderByUpdatedAtDesc(topic: String, pageable: org.springframework.data.domain.Pageable): List<SchedulerRun>
    
    @Query("{ 'status': 'failed' }")
    fun findFailedRuns(pageable: org.springframework.data.domain.Pageable): List<SchedulerRun>
    
    @Query("{ 'createdAt': { \$gte: ?0 } }")
    fun findRunsCreatedAfter(dateTime: LocalDateTime): List<SchedulerRun>
    
    fun findFirstByOrderByScheduledTimeDesc(): SchedulerRun?
}
