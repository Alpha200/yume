package eu.sendzik.yume.service.scheduler

import eu.sendzik.yume.repository.scheduler.SchedulerRunRepository
import eu.sendzik.yume.repository.scheduler.model.SchedulerRun
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.data.domain.PageRequest
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.util.UUID

@Service
class SchedulerRunLogService(
    private val schedulerRunRepository: SchedulerRunRepository,
    private val logger: KLogger,
) {

    fun logScheduledRun(schedulerRunDetails: SchedulerRunDetails): SchedulerRun {
        val run = SchedulerRun(
            id = UUID.randomUUID().toString(),
            scheduledTime = schedulerRunDetails.nextRun,
            reason = schedulerRunDetails.reason,
            topic = schedulerRunDetails.topic,
            details = schedulerRunDetails.details,
            status = "scheduled",
            createdAt = LocalDateTime.now(),
            updatedAt = LocalDateTime.now()
        )
        return schedulerRunRepository.save(run)
    }

    fun markAsExecuting(runId: String): SchedulerRun? {
        val run = schedulerRunRepository.findById(runId).orElse(null) ?: return null
        val updated = run.copy(
            status = "executing",
            actualExecutionTime = LocalDateTime.now(),
            updatedAt = LocalDateTime.now()
        )
        return schedulerRunRepository.save(updated)
    }

    fun markAsCompleted(runId: String, aiResponse: String? = null, executionDurationMs: Long? = null): SchedulerRun? {
        val run = schedulerRunRepository.findById(runId).orElse(null) ?: return null
        val updated = run.copy(
            status = "completed",
            aiResponse = aiResponse,
            executionDurationMs = executionDurationMs,
            updatedAt = LocalDateTime.now()
        )
        return schedulerRunRepository.save(updated)
    }

    fun markAsFailed(runId: String, errorMessage: String, executionDurationMs: Long? = null): SchedulerRun? {
        val run = schedulerRunRepository.findById(runId).orElse(null) ?: return null
        val updated = run.copy(
            status = "failed",
            errorMessage = errorMessage,
            executionDurationMs = executionDurationMs,
            updatedAt = LocalDateTime.now()
        )
        return schedulerRunRepository.save(updated)
    }

    fun getRecentRuns(limit: Int = 20, status: String? = null): List<SchedulerRun> {
        val pageable = PageRequest.of(0, limit)
        return if (status != null) {
            schedulerRunRepository.findByStatusOrderByUpdatedAtDesc(status, pageable)
        } else {
            schedulerRunRepository.findByOrderByUpdatedAtDesc(pageable)
        }
    }

    fun getRunById(runId: String): SchedulerRun? {
        return schedulerRunRepository.findById(runId).orElse(null)
    }

    fun getRunsByTopic(topic: String, limit: Int = 20): List<SchedulerRun> {
        val pageable = PageRequest.of(0, limit)
        return schedulerRunRepository.findByTopicOrderByUpdatedAtDesc(topic, pageable)
    }

    fun getFailedRuns(limit: Int = 20): List<SchedulerRun> {
        val pageable = PageRequest.of(0, limit)
        return schedulerRunRepository.findFailedRuns(pageable)
    }

    fun getNextScheduledRun(): SchedulerRun? {
        return schedulerRunRepository.findFirstByOrderByScheduledTimeDesc()
    }
}
