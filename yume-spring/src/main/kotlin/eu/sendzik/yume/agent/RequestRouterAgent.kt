package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode
import eu.sendzik.yume.agent.model.RequestRouterAgentResult

@AiService(
    chatModel = "routerChatModel",
    wiringMode = AiServiceWiringMode.EXPLICIT,
)
interface RequestRouterAgent {
    @SystemMessage(fromResource = "prompt/request-router-system-message.txt")
    @UserMessage("Current date and time: {{currentDateTime}}\n\nPrevious conversation history:\n{{messageHistory}}\n-------------\nRelevant memory entries: {{relevantMemories}}\n-------------\nUser message:\n{{userMessage}} ")
    fun determineRequestRouting(
        @V("currentDateTime") currentDateTime: String,
        @V("messageHistory") messageHistory: String,
        @V("userMessage") userMessage: String,
        @V("relevantMemories") relevantMemories: String
    ): RequestRouterAgentResult
}