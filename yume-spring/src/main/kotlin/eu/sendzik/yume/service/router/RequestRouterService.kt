package eu.sendzik.yume.service.router

import eu.sendzik.yume.agent.ConversationSummarizerAgent
import eu.sendzik.yume.agent.EfaAgent
import eu.sendzik.yume.agent.GenericChatAgent
import eu.sendzik.yume.agent.KitchenOwlAgent
import eu.sendzik.yume.agent.RequestRouterAgent
import eu.sendzik.yume.agent.SportsActivityAgent
import eu.sendzik.yume.agent.model.YumeChatResource
import eu.sendzik.yume.agent.model.YumeAgentType
import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntryType
import eu.sendzik.yume.service.conversation.ConversationHistoryManagerService
import eu.sendzik.yume.service.dayplan.DayPlanExecutorService
import eu.sendzik.yume.service.location.model.GeofenceEventRequest
import eu.sendzik.yume.service.location.model.GeofenceEventType
import eu.sendzik.yume.service.matrix.MatrixClientService
import eu.sendzik.yume.service.matrix.model.UserMessageEvent
import eu.sendzik.yume.service.memory.MemoryManagerExecutorService
import eu.sendzik.yume.service.memory.MemoryManagerService
import eu.sendzik.yume.service.provider.ResourceProviderService
import eu.sendzik.yume.service.provider.model.YumeResource
import eu.sendzik.yume.service.provider.model.toYumeResource
import eu.sendzik.yume.service.scheduler.model.SchedulerRunDetails
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import kotlinx.coroutines.runBlocking
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.event.EventListener
import org.springframework.core.io.Resource
import org.springframework.scheduling.annotation.Async
import org.springframework.stereotype.Service
import java.time.LocalDateTime

@Service
class RequestRouterService(
    private val conversationHistoryManagerService: ConversationHistoryManagerService,
    private val resourceProviderService: ResourceProviderService,
    private val memoryManagerService: MemoryManagerService,
    private val dayPlanExecutorService: DayPlanExecutorService,
    private val memoryManagerExecutorService: MemoryManagerExecutorService,
    private val matrixClientService: MatrixClientService,
    private val routerAgent: RequestRouterAgent,
    private val genericAgent: GenericChatAgent,
    private val kitchenOwlAgent: KitchenOwlAgent,
    private val efaAgent: EfaAgent,
    private val sportsActivityAgent: SportsActivityAgent,
    private val conversationSummarizerAgent: ConversationSummarizerAgent,
    private val geofenceEventLogService: eu.sendzik.yume.service.location.GeofenceEventLogService,
    private val logger: KLogger,
    @Value("classpath:prompt/default-preferences-prefix.txt")
    private val defaultPreferencesPrefixResource: Resource,
) {
    @EventListener
    @Async
    fun handleMessage(userMessageEvent: UserMessageEvent) {
        val response = runCatching {
            val conversationHistory = conversationHistoryManagerService.getRecentHistoryFormatted()
            val conversationSummary =
                conversationSummarizerAgent.summarizeConversation(conversationHistory, userMessageEvent.message)
            val relevantMemoryEntries = memoryManagerService.getFormattedRelevantMemories(conversationSummary)

            logger.debug { "Summarized conversation history into: $conversationSummary" }

            val result = routerAgent.determineRequestRouting(
                conversationSummary = conversationSummary,
                userMessage = userMessageEvent.message,
                currentDateTime = formatTimestampForLLM(userMessageEvent.timestamp),
                relevantMemories = relevantMemoryEntries,
            )

            logger.debug { "Routing decision: ${result.agent}. Resources: [${result.requiredResources.joinToString(", ")}] Reasoning: ${result.reasoning}" }

            val response = executeAgent(
                result.agent,
                userMessageEvent.message,
                result.requiredResources,
                relevantMemoryEntries,
                conversationHistory
            )

            conversationHistoryManagerService.addEntry(
                userMessageEvent.message,
                ConversationHistoryEntryType.USER_MESSAGE,
                userMessageEvent.timestamp
            )
            conversationHistoryManagerService.addEntry(response, ConversationHistoryEntryType.SYSTEM_MESSAGE)

            response
        }.onFailure {
            logger.error(it) { "Failure in message processing" }
        }.getOrDefault("There was an error processing your message. Please try again later.")

        runBlocking {
            matrixClientService.sendMessageToRoom(response)
        }
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
            YumeAgentType.SPORTS -> {
                sportsActivityAgent.handleUserMessage(
                    message,
                    defaultPreferencesPrefix,
                    additionalInformation,
                )
            }
        }

        result.memoryUpdateTask?.let {
            if (!it.isBlank()) {
                memoryManagerExecutorService.updateMemoryWithTask(it)
            }
        }

        result.dayPlannerUpdateTask?.let {
            if (!it.isBlank()) {
                dayPlanExecutorService.updateDayPlansWithTask(it)
            }
        }

        return result.messageToUser ?: "Failed to generate a response."
    }

    fun runFromScheduler(schedulerRunDetails: SchedulerRunDetails): String {
        val schedulerMessage = buildString {
            appendLine("A scheduled run has been triggered with the topic '${schedulerRunDetails.topic}'")
            appendLine("The scheduler agent provided the following details: ${schedulerRunDetails.details}")
        }

        logger.info { schedulerMessage }

        val conversationHistory = conversationHistoryManagerService.getRecentHistoryFormatted()
        val relevantMemoryEntries = memoryManagerService.getFormattedRelevantMemories(schedulerRunDetails.details)

        val (message, executionSummary) = routeAndExecuteEvent(
            eventMessage = schedulerMessage,
            relevantMemories = relevantMemoryEntries,
            conversationHistory = conversationHistory,
            eventType = EventType.SCHEDULED,
        )

        if (message != null) {
            runBlocking {
                matrixClientService.sendMessageToRoom(message)
            }
        }
        
        return executionSummary
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

        val (message, executionSummary) = routeAndExecuteEvent(
            eventMessage = geofenceEventMessage,
            relevantMemories = relevantMemoryEntries,
            conversationHistory = conversationHistory,
            eventType = EventType.GEOFENCE,
        )
        
        // Log geofence event with execution summary for scheduler feedback
        geofenceEventLogService.logGeofenceEvent(
            geofenceName = geofenceEvent.geofenceName,
            eventType = geofenceEvent.eventType.name.lowercase(),
            executionSummary = executionSummary
        )

        if (message != null) {
            runBlocking {
                matrixClientService.sendMessageToRoom(message)
            }
        }
    }

    fun handleSportsActivity(activityDetails: String) {
        logger.info { "Processing sports activity" }

        val conversationHistory = conversationHistoryManagerService.getRecentHistoryFormatted()
        val relevantMemoryEntries = memoryManagerService.getFormattedRelevantMemories("sports activities fitness cycling")

        val (message, executionSummary) = routeAndExecuteEvent(
            eventMessage = activityDetails,
            relevantMemories = relevantMemoryEntries,
            conversationHistory = conversationHistory,
            eventType = EventType.SPORTS_ACTIVITY,
        )

        if (message != null) {
            runBlocking {
                matrixClientService.sendMessageToRoom(message)
            }
        }

        logger.info { "Sports activity processed: $executionSummary" }
    }

    private enum class EventType {
        GEOFENCE, SCHEDULED, SPORTS_ACTIVITY
    }

    private fun routeAndExecuteEvent(
        eventMessage: String,
        relevantMemories: String,
        conversationHistory: String,
        eventType: EventType,
    ): Pair<String?, String> {
        val defaultPreferencesPrefix = defaultPreferencesPrefixResource.getContentAsString(Charsets.UTF_8)
        val additionalInformation = provideAdditionalResources(
            resources = emptyList(),
            relevantMemories = relevantMemories,
            conversationHistory = conversationHistory
        )

        // Get the agent response based on event type
        val agentResponse = if (eventType == EventType.SPORTS_ACTIVITY) {
            // For sports activities, directly use the Sports agent without routing
            sportsActivityAgent.handleSportsActivity(
                activityDetails = eventMessage,
                yumeSystemPromptPrefix = defaultPreferencesPrefix,
                additionalInformation = additionalInformation
            )
        } else {
            // For geofence and scheduled events, use the router
            val routerResult = when (eventType) {
                EventType.GEOFENCE -> routerAgent.routeGeofenceEvent(
                    conversationSummary = eventMessage,
                    geofenceEvent = eventMessage,
                    currentDateTime = formatTimestampForLLM(LocalDateTime.now()),
                    relevantMemories = relevantMemories,
                )
                EventType.SCHEDULED -> routerAgent.routeScheduledEvent(
                    conversationSummary = eventMessage,
                    scheduledEvent = eventMessage,
                    currentDateTime = formatTimestampForLLM(LocalDateTime.now()),
                    relevantMemories = relevantMemories,
                )
                EventType.SPORTS_ACTIVITY -> throw IllegalStateException("Should not reach here")
            }

            logger.debug { "Routing ${eventType.name.lowercase()} event to agent: ${routerResult.agent}. Reasoning: ${routerResult.reasoning}" }

            when (eventType) {
                EventType.GEOFENCE -> executeGeofenceAgent(routerResult.agent, eventMessage, defaultPreferencesPrefix, additionalInformation)
                EventType.SCHEDULED -> executeScheduledAgent(routerResult.agent, eventMessage, defaultPreferencesPrefix, additionalInformation)
                EventType.SPORTS_ACTIVITY -> throw IllegalStateException("Should not reach here")
            }
        }

        // Process agent response (common logic for all event types)
        if (!agentResponse.memoryUpdateTask.isNullOrBlank()) {
            memoryManagerExecutorService.updateMemoryWithTask(agentResponse.memoryUpdateTask)
        }

        if (!agentResponse.dayPlannerUpdateTask.isNullOrBlank()) {
            dayPlanExecutorService.updateDayPlansWithTask(agentResponse.dayPlannerUpdateTask)
        }

        // Add to conversation history
        if (eventType == EventType.GEOFENCE) {
            conversationHistoryManagerService.addEntry(
                eventMessage,
                ConversationHistoryEntryType.GEOFENCE_ACTION
            )
        }

        if (!agentResponse.messageToUser.isNullOrBlank()) {
            conversationHistoryManagerService.addEntry(
                agentResponse.messageToUser,
                ConversationHistoryEntryType.SYSTEM_MESSAGE
            )
        }
        
        // Extract execution summary
        val executionSummary = agentResponse.executionSummary ?: run {
            if (!agentResponse.messageToUser.isNullOrBlank()) {
                "Sent message to user"
            } else {
                "No action taken"
            }
        }

        return Pair(agentResponse.messageToUser, executionSummary)
    }

    private fun executeScheduledAgent(
        agentType: YumeAgentType,
        eventMessage: String,
        systemPromptPrefix: String,
        additionalInformation: String,
    ): eu.sendzik.yume.agent.model.EventTriggeredAgentResult {
        return when (agentType) {
            YumeAgentType.KITCHEN_OWL -> kitchenOwlAgent.handleScheduledEvent(eventMessage, systemPromptPrefix, additionalInformation)
            YumeAgentType.GENERIC -> genericAgent.handleScheduledEvent(eventMessage, systemPromptPrefix, additionalInformation)
            YumeAgentType.PUBLIC_TRANSPORT -> efaAgent.handleScheduledEvent(eventMessage, systemPromptPrefix, additionalInformation)
            YumeAgentType.SPORTS -> sportsActivityAgent.handleScheduledEvent(eventMessage, systemPromptPrefix, additionalInformation)
        }
    }

    private fun executeGeofenceAgent(
        agentType: YumeAgentType,
        eventMessage: String,
        systemPromptPrefix: String,
        additionalInformation: String,
    ): eu.sendzik.yume.agent.model.EventTriggeredAgentResult {
        return when (agentType) {
            YumeAgentType.KITCHEN_OWL -> kitchenOwlAgent.handleGeofenceEvent(eventMessage, systemPromptPrefix, additionalInformation)
            YumeAgentType.GENERIC -> genericAgent.handleGeofenceEvent(eventMessage, systemPromptPrefix, additionalInformation)
            YumeAgentType.PUBLIC_TRANSPORT -> efaAgent.handleGeofenceEvent(eventMessage, systemPromptPrefix, additionalInformation)
            YumeAgentType.SPORTS -> sportsActivityAgent.handleGeofenceEvent(eventMessage, systemPromptPrefix, additionalInformation)
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
                    YumeResource.LOCATION,
                ) + resources.map { it.toYumeResource() }
            ))

            appendLine(relevantMemories)
            appendLine(conversationHistory)
        }
        return additionalInformation
    }
}