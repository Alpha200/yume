package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode
import eu.sendzik.yume.agent.model.BasicUserInteractionAgentResult

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "defaultChatModel",
    tools = ["kitchenOwlTools", "kitchenOwlReadTools"],
)
interface KitchenOwlAgent {
    @SystemMessage(fromResource = "prompt/kitchenowl-system-message.txt")
    fun handleKitchenOwlTask(
        @UserMessage query: String,
        @V("systemPromptPrefix") yumeSystemPromptPrefix: String,
        @V("userLanguage") userLanguage: String,
        @V("additionalInformation") additionalInformation: String,
    ): BasicUserInteractionAgentResult
}