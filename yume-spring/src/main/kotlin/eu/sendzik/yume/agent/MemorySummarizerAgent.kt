package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "memorySummarizerChatModel",
)
interface MemorySummarizerAgent {
    @SystemMessage(fromResource = "prompt/memory-summarizer-system-message.txt")
    @UserMessage(fromResource = "prompt/memory-summarizer-user-message.txt")
    fun summarizeMemory(
        @V("currentDateTime") currentDateTime: String,
        @V("memories") memories: String,
    ): String
}