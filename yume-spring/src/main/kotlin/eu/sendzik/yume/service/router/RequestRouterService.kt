package eu.sendzik.yume.service.router

import eu.sendzik.yume.agent.EfaAgent
import eu.sendzik.yume.agent.GenericChatAgent
import eu.sendzik.yume.agent.KitchenOwlAgent
import eu.sendzik.yume.agent.RequestRouterAgent
import eu.sendzik.yume.agent.model.YumeAgentResource
import eu.sendzik.yume.agent.model.YumeAgentType
import eu.sendzik.yume.configuration.AgentConfiguration
import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntryType
import eu.sendzik.yume.service.conversation.ConversationHistoryManager
import eu.sendzik.yume.service.dayplan.DayPlanExecutorService
import eu.sendzik.yume.service.location.model.GeofenceEventRequest
import eu.sendzik.yume.service.memory.MemoryManagerExecutorService
import eu.sendzik.yume.service.memory.MemoryManagerService
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.core.io.Resource
import org.springframework.stereotype.Service
import java.time.LocalDateTime

@Service
class RequestRouterService(
    private val routerAgent: RequestRouterAgent,
    private val conversationHistoryManager: ConversationHistoryManager,
    private val genericAgent: GenericChatAgent,
    private val kitchenOwlAgent: KitchenOwlAgent,
    private val agentConfiguration: AgentConfiguration,
    private val resourceProviderService: ResourceProviderService,
    private val memoryManagerService: MemoryManagerService,
    @Value("classpath:prompt/default-preferences-prefix.txt")
    private val defaultPreferencesPrefixResource: Resource,
    private val dayPlanExecutorService: DayPlanExecutorService,
    private val memoryManagerExecutorService: MemoryManagerExecutorService,
    private val efaAgent: EfaAgent,
    private val logger: KLogger,
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

        val response = executeAgent(result.agent, message, result.requiredResources, relevantMemoryEntries, conversationHistory)

        conversationHistoryManager.addEntry(message, ConversationHistoryEntryType.USER_MESSAGE, messageTimestamp)
        conversationHistoryManager.addEntry(response, ConversationHistoryEntryType.SYSTEM_MESSAGE)

        return response
    }

    fun executeAgent(agentType: YumeAgentType, message: String, resources: List<YumeAgentResource>, relevantMemories: String, conversationHistory: String): String {
        val additionalInformation = provideAdditionalResources(resources, relevantMemories, conversationHistory)
        val defaultPreferencesPrefix = defaultPreferencesPrefixResource.getContentAsString(Charsets.UTF_8)

        val result = when (agentType) {
            YumeAgentType.KITCHEN_OWL -> {
                kitchenOwlAgent.handleUserMessage(
                    message,
                    defaultPreferencesPrefix,
                    additionalInformation,
                )
            }
            YumeAgentType.GENERIC -> {
                genericAgent.handleUserMessage(
                    message,
                    defaultPreferencesPrefix,
                    additionalInformation
                )
            }
            YumeAgentType.PUBLIC_TRANSPORT -> {
                efaAgent.handleUserMessage(
                    message,
                    defaultPreferencesPrefix,
                    additionalInformation,
                )
            }
        }

        if (!result.memoryUpdateTask.isNullOrBlank()) {
            memoryManagerExecutorService.updateMemoryWithTask(result.memoryUpdateTask)
        }

        if (!result.dayPlannerUpdateTask.isNullOrBlank()) {
            dayPlanExecutorService.updateDayPlansWithTask(result.dayPlannerUpdateTask)
        }

        return result.messageToUser ?: "Failed to generate a response."
    }

    fun runFromScheduler(schedulerRunDetails: SchedulerRunDetails) {
        TODO("Not yet implemented")
    }

    fun handleGeofenceEvent(geofenceEvent: GeofenceEventRequest) {
        TODO("Not yet implemented")
    }

    private fun provideAdditionalResources(
        resources: List<YumeAgentResource>,
        relevantMemories: String,
        conversationHistory: String
    ): String {
        val additionalInformation = buildString {
            appendLine("Additional provided information:")
            appendLine("Always communicate in the user's preferred language: ${agentConfiguration.preferences.userLanguage}")
            appendLine("The current date and time is: ${formatTimestampForLLM(LocalDateTime.now())}")

            if (resources.isNotEmpty()) {
                appendLine(resourceProviderService.provideResources(resources))
                appendLine()
            }

            appendLine(relevantMemories)
            appendLine(conversationHistory)
        }
        return additionalInformation
    }
}