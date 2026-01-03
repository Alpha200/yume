package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode
import eu.sendzik.yume.agent.model.MemoryManagerAgentResult

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "memoryManagerChatModel",
    tools = ["memoryManagerTools"],
)
interface MemoryManagerAgent {
    @SystemMessage(fromResource = "prompt/memory-manager-system-message.txt")
    @UserMessage(fromResource = "prompt/memory-manager-user-message.txt")
    fun updateMemoryWithTask(
        @V("currentDateTime") currentDateTime: String,
        @V("memories") memories: String, // TODO: Instead of passing all memories, pass only relevant ones (Do so by migrating to knowledge graph)
        @V("task") task: String,
    ): MemoryManagerAgentResult

    @SystemMessage(fromResource = "prompt/memory-manager-system-message.txt")
    @UserMessage(fromResource = "prompt/memory-janitor-user-message.txt")
    fun runMemoryJanitor(
        @V("currentDateTime") currentDateTime: String,
        @V("memories") memories: String,
    ): MemoryManagerAgentResult
}