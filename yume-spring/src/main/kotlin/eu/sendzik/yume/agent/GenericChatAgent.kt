package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode
import eu.sendzik.yume.agent.model.BasicUserInteractionAgentResult
import eu.sendzik.yume.agent.model.EventTriggeredAgentResult

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "genericChatModel",
    tools = [],
)
interface GenericChatAgent {
    @SystemMessage(fromResource = "prompt/chat-interaction-system-message.txt")
    fun handleUserMessage(
        @UserMessage query: String,
        @V("systemPromptPrefix") yumeSystemPromptPrefix: String,
        @V("additionalInformation") additionalInformation: String,
    ): BasicUserInteractionAgentResult

    @SystemMessage(fromResource = "prompt/geofence-event-system-message.txt")
    fun handleGeofenceEvent(
        @UserMessage query: String,
        @V("systemPromptPrefix") yumeSystemPromptPrefix: String,
        @V("additionalInformation") additionalInformation: String,
    ): EventTriggeredAgentResult

    @SystemMessage(fromResource = "prompt/chat-interaction-scheduler-system-message.txt")
    fun handleScheduledEvent(
        @UserMessage query: String,
        @V("systemPromptPrefix") yumeSystemPromptPrefix: String,
        @V("additionalInformation") additionalInformation: String,
    ): EventTriggeredAgentResult
}