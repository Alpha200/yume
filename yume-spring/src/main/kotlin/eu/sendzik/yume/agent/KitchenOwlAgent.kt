package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode
import eu.sendzik.yume.agent.model.BasicUserInteractionAgentResult

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "kitchenOwlChatModel",
    tools = ["kitchenOwlTools", "kitchenOwlReadTools"],
)
interface KitchenOwlAgent {
    @SystemMessage(fromResource = "prompt/kitchenowl-system-message.txt")
    fun handleUserMessage(
        @UserMessage query: String,
        @V("systemPromptPrefix") yumeSystemPromptPrefix: String,
        @V("additionalInformation") additionalInformation: String,
    ): BasicUserInteractionAgentResult

    @SystemMessage(fromResource = "prompt/kitchenowl-geofence-system-message.txt")
    fun handleGeofenceEvent(
        @UserMessage query: String,
        @V("systemPromptPrefix") yumeSystemPromptPrefix: String,
        @V("additionalInformation") additionalInformation: String,
    ): BasicUserInteractionAgentResult
}