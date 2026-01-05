package eu.sendzik.yume.repository.scheduler.model

import com.fasterxml.jackson.annotation.JsonCreator
import com.fasterxml.jackson.annotation.JsonValue
import org.springframework.data.annotation.Id
import org.springframework.data.annotation.TypeAlias
import org.springframework.data.mongodb.core.mapping.Document
import org.springframework.data.mongodb.core.mapping.Field
import java.time.LocalDateTime

enum class SchedulerRunStatus(
    @JsonValue
    val value: String
) {
    SCHEDULED("scheduled"),
    COMPLETED("completed"),
    FAILED("failed"),
    CANCELLED("cancelled");

    companion object {
        @JsonCreator
        @JvmStatic
        fun fromValue(value: String?): SchedulerRunStatus? {
            return entries.find { it.value == value }
        }
    }
}

@TypeAlias("SchedulerRun")
@Document(collection = "scheduler_runs")
data class SchedulerRun(
    @field:Id val id: String,
    @field:Field("scheduled_time") val scheduledTime: LocalDateTime,
    @field:Field("actual_execution_time") val actualExecutionTime: LocalDateTime? = null,  // When it actually ran
    val reason: String,  // Why this run was scheduled
    val topic: String,  // Topic/subject of the interaction
    val status: SchedulerRunStatus = SchedulerRunStatus.SCHEDULED,  // scheduled, executing, completed, failed, cancelled
    @field:Field("error_message") val errorMessage: String? = null,  // Error details if status is FAILED
    @field:Field("execution_duration_ms") val executionDurationMs: Long? = null,  // How long the execution took
    @field:Field("ai_response") val aiResponse: String? = null,  // The response/output from the AI engine
    val details: String? = null,  // Additional context/information
    val metadata: Map<String, Any>? = null,  // Additional context data
    @field:Field("created_at") val createdAt: LocalDateTime = LocalDateTime.now(),
    @field:Field("updated_at") val updatedAt: LocalDateTime = LocalDateTime.now(),
)
