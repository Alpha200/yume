package eu.sendzik.yume.service.scheduler

import eu.sendzik.yume.repository.scheduler.SchedulerRunRepository
import eu.sendzik.yume.repository.scheduler.model.SchedulerRun
import eu.sendzik.yume.repository.scheduler.model.SchedulerRunStatus
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import eu.sendzik.yume.utils.formatTimestampForLLM
import org.springframework.data.domain.PageRequest
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.util.UUID

@Service
class SchedulerRunLogService(
    private val schedulerRunRepository: SchedulerRunRepository,
) {

    fun logScheduledRun(schedulerRunDetails: SchedulerRunDetails): SchedulerRun {
        // Cancel all scheduled runs
        schedulerRunRepository.cancelAllScheduledRuns()

        // Create and save the new scheduled run
        val run = SchedulerRun(
            id = UUID.randomUUID().toString(),
            scheduledTime = schedulerRunDetails.nextRun,
            reason = schedulerRunDetails.reason,
            topic = schedulerRunDetails.topic,
            details = schedulerRunDetails.details,
            status = SchedulerRunStatus.SCHEDULED,
            createdAt = LocalDateTime.now(),
            updatedAt = LocalDateTime.now()
        )
        return schedulerRunRepository.save(run)
    }

    fun markAsCompleted(runId: String, aiResponse: String? = null, executionDurationMs: Long? = null): SchedulerRun? {
        val run = schedulerRunRepository.findById(runId).orElse(null) ?: return null
        val updated = run.copy(
            status = SchedulerRunStatus.COMPLETED,
            aiResponse = aiResponse,
            executionDurationMs = executionDurationMs,
            updatedAt = LocalDateTime.now()
        )
        return schedulerRunRepository.save(updated)
    }

    fun markAsFailed(runId: String, errorMessage: String, executionDurationMs: Long? = null): SchedulerRun? {
        val run = schedulerRunRepository.findById(runId).orElse(null) ?: return null
        val updated = run.copy(
            status = SchedulerRunStatus.FAILED,
            errorMessage = errorMessage,
            executionDurationMs = executionDurationMs,
            updatedAt = LocalDateTime.now()
        )
        return schedulerRunRepository.save(updated)
    }

    fun getRecentRuns(limit: Int = 20, status: SchedulerRunStatus? = null): List<SchedulerRun> {
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

    fun getRecentExecutedRunsFormatted(limit: Int): String {
        val recentRuns = getRecentRuns(limit, SchedulerRunStatus.COMPLETED)
        return recentRuns.joinToString {
            "- Scheduled: ${formatTimestampForLLM(it.scheduledTime)} Topic: ${it.topic}"
        }
    }
}

