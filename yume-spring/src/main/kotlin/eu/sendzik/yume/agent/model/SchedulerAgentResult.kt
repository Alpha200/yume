package eu.sendzik.yume.agent.model

import java.time.LocalDateTime

data class SchedulerAgentResult(
    var nextRun: LocalDateTime,
    var reason: String,
    var topic: String,
    var details: String,
)