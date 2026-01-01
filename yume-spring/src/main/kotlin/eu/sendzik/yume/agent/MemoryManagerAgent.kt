package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
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
    fun updateMemoryWithTask(task: String): MemoryManagerAgentResult
}