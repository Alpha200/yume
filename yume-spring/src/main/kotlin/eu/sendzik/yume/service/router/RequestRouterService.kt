package eu.sendzik.yume.service.router

import eu.sendzik.yume.agent.ConversationSummarizerAgent
import eu.sendzik.yume.agent.EfaAgent
import eu.sendzik.yume.agent.GenericChatAgent
import eu.sendzik.yume.agent.KitchenOwlAgent
import eu.sendzik.yume.agent.RequestRouterAgent
import eu.sendzik.yume.agent.model.YumeChatResource
import eu.sendzik.yume.agent.model.YumeAgentType
import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntryType
import eu.sendzik.yume.service.conversation.ConversationHistoryManagerService
import eu.sendzik.yume.service.dayplan.DayPlanExecutorService
import eu.sendzik.yume.service.location.model.GeofenceEventRequest
import eu.sendzik.yume.service.memory.MemoryManagerExecutorService
import eu.sendzik.yume.service.memory.MemoryManagerService
import eu.sendzik.yume.service.provider.ResourceProviderService
import eu.sendzik.yume.service.provider.model.YumeResource
import eu.sendzik.yume.service.provider.model.toYumeResource
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.core.io.Resource
import org.springframework.stereotype.Service
import java.time.LocalDateTime

@Service
class RequestRouterService(
    private val conversationHistoryManagerService: ConversationHistoryManagerService,
    private val resourceProviderService: ResourceProviderService,
    private val memoryManagerService: MemoryManagerService,
    private val dayPlanExecutorService: DayPlanExecutorService,
    private val memoryManagerExecutorService: MemoryManagerExecutorService,
    private val routerAgent: RequestRouterAgent,
    private val genericAgent: GenericChatAgent,
    private val kitchenOwlAgent: KitchenOwlAgent,
    private val efaAgent: EfaAgent,
    private val conversationSummarizerAgent: ConversationSummarizerAgent,
    private val logger: KLogger,
    @Value("classpath:prompt/default-preferences-prefix.txt")
    private val defaultPreferencesPrefixResource: Resource,
) {
    fun handleMessage(message: String, messageTimestamp: LocalDateTime): String? {
        val conversationHistory = conversationHistoryManagerService.getRecentHistoryFormatted()
        val conversationSummary = conversationSummarizerAgent.summarizeConversation(conversationHistory, message)
        val relevantMemoryEntries = memoryManagerService.getFormattedRelevantMemories(conversationSummary)

        logger.debug { "Summarized conversation history into: $conversationSummary" }

        val result = routerAgent.determineRequestRouting(
            conversationSummary = conversationSummary,
            userMessage = message,
            currentDateTime = formatTimestampForLLM(messageTimestamp),
            relevantMemories = relevantMemoryEntries,
        )

        logger.debug { "Routing decision: ${result.agent}. Resources: [${result.requiredResources.joinToString(", ")}] Reasoning: ${result.reasoning}" }

        val response = executeAgent(result.agent, message, result.requiredResources, relevantMemoryEntries, conversationHistory)

        conversationHistoryManagerService.addEntry(message, ConversationHistoryEntryType.USER_MESSAGE, messageTimestamp)
        conversationHistoryManagerService.addEntry(response, ConversationHistoryEntryType.SYSTEM_MESSAGE)

        return response
    }

    fun executeAgent(agentType: YumeAgentType, message: String, resources: List<YumeChatResource>, relevantMemories: String, conversationHistory: String): String {
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

    // TODO: Extract to a separate service (or use context object and attach data there)
    private fun provideAdditionalResources(
        resources: List<YumeChatResource>,
        relevantMemories: String,
        conversationHistory: String
    ): String {
        val additionalInformation = buildString {
            appendLine("Additional provided information:")

            appendLine(resourceProviderService.provideResources(
                listOf(
                    YumeResource.USER_LANGUAGE,
                    YumeResource.CURRENT_DATE_TIME,
                ) + resources.map { it.toYumeResource() }
            ))

            appendLine(relevantMemories)
            appendLine(conversationHistory)
        }
        return additionalInformation
    }
}