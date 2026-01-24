package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "eInkChatModel",
    tools = [],
)
interface EInkDisplayAgent {
    @SystemMessage(fromResource = "prompt/e-ink-display-system-message.txt")
    fun generateTextForEInkDisplay(
        @UserMessage information: String,
    ): String
}