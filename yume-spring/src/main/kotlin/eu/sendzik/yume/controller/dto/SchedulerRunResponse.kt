package eu.sendzik.yume.controller.dto

data class SchedulerRunResponse(
    val id: String,
    val scheduledTime: String,
    val actualExecutionTime: String? = null,
    val reason: String,
    val topic: String,
    val status: String,
    val errorMessage: String? = null,
    val executionDurationMs: Long? = null,
    val aiResponse: String? = null,
    val details: String? = null,
    val createdAt: String,
    val updatedAt: String,
)