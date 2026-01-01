package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode
import eu.sendzik.yume.agent.model.DayPlanAgentResult

@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "dayPlanChatModel",
    tools = ["dayPlanTools"],
)
interface DayPlanAgent {
    @SystemMessage(fromResource = "prompt/day-plan-system-message.txt")
    fun updateDayPlansWithTask(query: String): DayPlanAgentResult
}