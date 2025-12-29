package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "defaultChatModel",
    tools = ["efaTools"],
)
interface EfaAgent {
    @SystemMessage(fromResource = "prompt/efa-system-message.txt")
    fun handleEfaRequest(query: String): String
}