package eu.sendzik.yume.service.chat

import eu.sendzik.yume.agent.GenericChatAgent
import eu.sendzik.yume.agent.DayPlanAgent
import eu.sendzik.yume.agent.MemoryManagerAgent
import eu.sendzik.yume.configuration.AgentConfiguration
import eu.sendzik.yume.service.scheduler.SchedulerService
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Service

@Service
class ChatInteractionService(
    private val memoryManagerAgent: MemoryManagerAgent,
    private val dayPlanAgent: DayPlanAgent,
    private val genericChatAgent: GenericChatAgent,
    private val agentConfiguration: AgentConfiguration,
    private val schedulerService: SchedulerService,
    private val logger: KLogger,
) {
//    fun handleMessage(message: String): String? {
//        val result = genericChatAgent.handleChatInteraction(
//            message,
//            agentConfiguration.preferences.userLanguage
//        )
//        var changes = false
//
//        if (!result.memoryUpdateTask.isNullOrBlank()) {
//            changes = memoryManagerAgent
//                .updateMemoryWithTask(result.memoryUpdateTask)
//                .actionsTaken
//                .isNotEmpty()
//        }
//
//        if (!result.dayPlannerUpdateTask.isNullOrBlank()) {
//            changes = changes.or(
//                dayPlanAgent
//                    .updateDayPlansWithTask(result.dayPlannerUpdateTask)
//                    .actionsTaken
//                    .isNotEmpty()
//            )
//        }
//
//        if (changes) {
//            schedulerService.triggerRun()
//        }
//
//        return result.messageToUser
//    }
//
//    fun handleScheduledRun(schedulerRunDetails: SchedulerRunDetails) {
//        TODO("Not yet implemented")
//    }
}