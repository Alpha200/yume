package eu.sendzik.yume.service.router

import eu.sendzik.yume.agent.GenericChatAgent
import eu.sendzik.yume.agent.KitchenOwlAgent
import eu.sendzik.yume.agent.RequestRouterAgent
import eu.sendzik.yume.agent.model.YumeAgentResource
import eu.sendzik.yume.agent.model.YumeAgentType
import eu.sendzik.yume.configuration.AgentConfiguration
import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntryType
import eu.sendzik.yume.service.conversation.ConversationHistoryManager
import eu.sendzik.yume.service.dayplan.DayPlanExecutorService
import eu.sendzik.yume.service.memory.MemoryManagerExecutorService
import eu.sendzik.yume.service.memory.MemoryManagerService
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import java.time.LocalDateTime

@Service
class ChatRouterService(
    private val routerAgent: RequestRouterAgent,
    private val conversationHistoryManager: ConversationHistoryManager,
    private val genericAgent: GenericChatAgent,
    private val kitchenOwlAgent: KitchenOwlAgent,
    private val logger: KLogger,
    private val agentConfiguration: AgentConfiguration,
    private val resourceProviderService: ResourceProviderService,
    private val memoryManagerService: MemoryManagerService,
    @Value("classpath:prompt/default-preferences-prefix.txt")
    private val defaultPreferencesPrefix: String,
    private val dayPlanExecutorService: DayPlanExecutorService,
    private val memoryManagerExecutorService: MemoryManagerExecutorService,
) {
    fun handleMessage(message: String, messageTimestamp: LocalDateTime): String? {
        val conversationHistory = conversationHistoryManager.getRecentHistoryFormatted()
        val relevantMemoryEntries = memoryManagerService.getFormattedRelevantMemories(message)

        val result = routerAgent.determineRequestRouting(
            messageHistory = conversationHistory,
            userMessage = message,
            currentDateTime = formatTimestampForLLM(messageTimestamp),
            relevantMemories = relevantMemoryEntries,
        )

        logger.debug { "Routing decision: ${result.agent}. Resources: [${result.requiredResources.joinToString(", ")}] Reasoning: ${result.reasoning}" }

        val response = executeAgent(result.agent, message, result.requiredResources, relevantMemoryEntries)

        conversationHistoryManager.addEntry(message, ConversationHistoryEntryType.USER_MESSAGE, messageTimestamp)
        conversationHistoryManager.addEntry(response, ConversationHistoryEntryType.SYSTEM_MESSAGE)

        return response
    }

    fun executeAgent(agentType: YumeAgentType, message: String, resources: List<YumeAgentResource>, relevantMemories: String): String {
        val userLanguage = agentConfiguration.preferences.userLanguage
        val additionalInformation = buildString {
            appendLine("Additional provided information:")
            appendLine()
            appendLine(resourceProviderService.provideResources(resources))
            appendLine()
            appendLine(relevantMemories)
        }

        val result = when (agentType) {
            YumeAgentType.KITCHEN_OWL -> {
                kitchenOwlAgent.handleKitchenOwlTask(
                    message,
                    defaultPreferencesPrefix,
                    userLanguage = userLanguage,
                    additionalInformation = additionalInformation,
                )
            }
            YumeAgentType.GENERIC -> {
                genericAgent.handleChatInteraction(
                    message,
                    defaultPreferencesPrefix,
                    userLanguage = userLanguage,
                    additionalInformation = additionalInformation
                )
            }
            YumeAgentType.PUBLIC_TRANSPORT -> TODO()
        }

        if (!result.memoryUpdateTask.isNullOrBlank()) {
            memoryManagerExecutorService.updateMemoryWithTask(result.memoryUpdateTask)
        }

        if (!result.dayPlannerUpdateTask.isNullOrBlank()) {
            dayPlanExecutorService.updateDayPlansWithTask(result.dayPlannerUpdateTask)
        }

        return result.messageToUser ?: "Failed to generate a response."
    }
}