package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode
import eu.sendzik.yume.agent.model.SchedulerAgentResult

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "defaultChatModel",
    tools = [],
)
interface SchedulerAgent {
    @SystemMessage(fromResource = "prompt/scheduler-system-message.txt")
    @UserMessage("Determine the next optimal run time")
    fun determineNextRun(): SchedulerAgentResult
}