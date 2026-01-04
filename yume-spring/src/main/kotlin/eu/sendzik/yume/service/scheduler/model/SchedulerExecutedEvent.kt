package eu.sendzik.yume.service.scheduler.model

import java.time.LocalDateTime

data class SchedulerExecutedEvent(
    val timestamp: LocalDateTime = LocalDateTime.now()
)
