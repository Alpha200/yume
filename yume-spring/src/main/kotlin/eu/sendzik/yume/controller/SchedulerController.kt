package eu.sendzik.yume.controller

import eu.sendzik.yume.repository.scheduler.model.SchedulerRun
import eu.sendzik.yume.service.scheduler.SchedulerRunLogService
import eu.sendzik.yume.controller.dto.SchedulerRunResponse
import eu.sendzik.yume.repository.scheduler.model.SchedulerRunStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("scheduler-runs")
class SchedulerController(
    private val schedulerRunLogService: SchedulerRunLogService
) {

    private fun toResponse(run: SchedulerRun): SchedulerRunResponse {
        return SchedulerRunResponse(
            id = run.id,
            scheduledTime = run.scheduledTime.toString(),
            actualExecutionTime = run.actualExecutionTime?.toString(),
            reason = run.reason,
            topic = run.topic,
            status = run.status.value,
            errorMessage = run.errorMessage,
            executionDurationMs = run.executionDurationMs,
            aiResponse = run.aiResponse,
            details = run.details,
            createdAt = run.createdAt.toString(),
            updatedAt = run.updatedAt.toString()
        )
    }

    @GetMapping("/recent")
    fun getRecentRuns(
        @RequestParam(defaultValue = "20") limit: Int,
        @RequestParam status: SchedulerRunStatus?
    ): List<SchedulerRunResponse> {
        return schedulerRunLogService.getRecentRuns(limit, status).map { toResponse(it) }
    }

    @GetMapping("/{runId}")
    fun getSchedulerRun(@PathVariable runId: String): ResponseEntity<SchedulerRunResponse> {
        val run = schedulerRunLogService.getRunById(runId) ?: return ResponseEntity.notFound().build()
        return ResponseEntity.ok(toResponse(run))
    }

    @GetMapping("/topic/{topic}")
    fun getRunsByTopic(
        @PathVariable topic: String,
        @RequestParam(defaultValue = "20") limit: Int
    ): List<SchedulerRunResponse> {
        return schedulerRunLogService.getRunsByTopic(topic, limit).map { toResponse(it) }
    }

    @GetMapping("/failed")
    fun getFailedRuns(
        @RequestParam(defaultValue = "20") limit: Int
    ): List<SchedulerRunResponse> {
        return schedulerRunLogService.getFailedRuns(limit).map { toResponse(it) }
    }
}
