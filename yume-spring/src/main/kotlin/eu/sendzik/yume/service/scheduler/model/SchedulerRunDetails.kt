package eu.sendzik.yume.service.scheduler.model

import eu.sendzik.yume.agent.model.SchedulerAgentResult
import java.time.LocalDateTime

data class SchedulerRunDetails(
    var nextRun: LocalDateTime,
    var reason: String,
    var topic: String,
    var details: String,
) {
    companion object {
        fun fromSchedulerAgentResult(result: SchedulerAgentResult): SchedulerRunDetails {
            return SchedulerRunDetails(
                nextRun = result.nextRun,
                reason = result.reason,
                topic = result.topic,
                details = result.details,
            )
        }
    }
}
