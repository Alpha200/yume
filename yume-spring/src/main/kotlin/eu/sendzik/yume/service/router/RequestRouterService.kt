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
import eu.sendzik.yume.service.location.model.GeofenceEventType
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
        val schedulerMessage = buildString {
            append("Scheduled run: ")
            append(schedulerRunDetails.reason)
            append(". Topic: ")
            append(schedulerRunDetails.topic)
        }

        logger.info { schedulerMessage }

        val conversationHistory = conversationHistoryManagerService.getRecentHistoryFormatted()
        val relevantMemoryEntries = memoryManagerService.getFormattedRelevantMemories(schedulerRunDetails.details)

        routeAndExecuteEvent(
            eventMessage = schedulerMessage,
            messageContent = schedulerRunDetails.details,
            relevantMemories = relevantMemoryEntries,
            conversationHistory = conversationHistory,
            eventType = EventType.SCHEDULED,
        )
    }

    fun handleGeofenceEvent(geofenceEvent: GeofenceEventRequest) {
        val geofenceEventMessage = buildString {
            append("Geofence event: User ")
            append(when (geofenceEvent.eventType) {
                GeofenceEventType.ENTER -> "entered"
                GeofenceEventType.LEAVE -> "left"
            })
            append(" geofence '${geofenceEvent.geofenceName}'")
        }

        logger.info { geofenceEventMessage }

        val conversationHistory = conversationHistoryManagerService.getRecentHistoryFormatted()
        val relevantMemoryEntries = memoryManagerService.getFormattedRelevantMemories(geofenceEvent.geofenceName)

        routeAndExecuteEvent(
            eventMessage = geofenceEventMessage,
            messageContent = geofenceEventMessage,
            relevantMemories = relevantMemoryEntries,
            conversationHistory = conversationHistory,
            eventType = EventType.GEOFENCE,
        )
    }

    private enum class EventType {
        GEOFENCE, SCHEDULED
    }

    private fun routeAndExecuteEvent(
        eventMessage: String,
        messageContent: String,
        relevantMemories: String,
        conversationHistory: String,
        eventType: EventType,
    ) {
        val routerResult = routerAgent.determineRequestRouting(
            conversationSummary = eventMessage,
            userMessage = messageContent,
            currentDateTime = formatTimestampForLLM(LocalDateTime.now()),
            relevantMemories = relevantMemories,
        )

        logger.debug { "Routing ${eventType.name.lowercase()} event to agent: ${routerResult.agent}. Reasoning: ${routerResult.reasoning}" }

        val defaultPreferencesPrefix = defaultPreferencesPrefixResource.getContentAsString(Charsets.UTF_8)
        val additionalInformation = provideAdditionalResources(
            resources = routerResult.requiredResources,
            relevantMemories = relevantMemories,
            conversationHistory = conversationHistory
        )

        val agentResponse = when (eventType) {
            EventType.GEOFENCE -> executeGeofenceAgent(routerResult.agent, messageContent, defaultPreferencesPrefix, additionalInformation)
            EventType.SCHEDULED -> executeScheduledAgent(routerResult.agent, messageContent, defaultPreferencesPrefix, additionalInformation)
        }

        if (!agentResponse.memoryUpdateTask.isNullOrBlank()) {
            memoryManagerExecutorService.updateMemoryWithTask(agentResponse.memoryUpdateTask)
        }

        if (!agentResponse.dayPlannerUpdateTask.isNullOrBlank()) {
            dayPlanExecutorService.updateDayPlansWithTask(agentResponse.dayPlannerUpdateTask)
        }

        if (!agentResponse.messageToUser.isNullOrBlank()) {
            conversationHistoryManagerService.addEntry(
                agentResponse.messageToUser,
                ConversationHistoryEntryType.SYSTEM_MESSAGE
            )
        }

        // Always add event message for geofence events; for scheduled events only if no message was already added
        if (eventType == EventType.GEOFENCE) {
            conversationHistoryManagerService.addEntry(
                eventMessage,
                ConversationHistoryEntryType.SYSTEM_MESSAGE
            )
        }
    }

    private fun executeScheduledAgent(
        agentType: YumeAgentType,
        message: String,
        systemPromptPrefix: String,
        additionalInformation: String,
    ): eu.sendzik.yume.agent.model.BasicUserInteractionAgentResult {
        return when (agentType) {
            YumeAgentType.KITCHEN_OWL -> kitchenOwlAgent.handleUserMessage(message, systemPromptPrefix, additionalInformation)
            YumeAgentType.GENERIC -> genericAgent.handleUserMessage(message, systemPromptPrefix, additionalInformation)
            YumeAgentType.PUBLIC_TRANSPORT -> efaAgent.handleUserMessage(message, systemPromptPrefix, additionalInformation)
        }
    }

    private fun executeGeofenceAgent(
        agentType: YumeAgentType,
        message: String,
        systemPromptPrefix: String,
        additionalInformation: String,
    ): eu.sendzik.yume.agent.model.BasicUserInteractionAgentResult {
        return when (agentType) {
            YumeAgentType.KITCHEN_OWL -> kitchenOwlAgent.handleGeofenceEvent(message, systemPromptPrefix, additionalInformation)
            YumeAgentType.GENERIC -> genericAgent.handleGeofenceEvent(message, systemPromptPrefix, additionalInformation)
            YumeAgentType.PUBLIC_TRANSPORT -> efaAgent.handleGeofenceEvent(message, systemPromptPrefix, additionalInformation)
        }
    }

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