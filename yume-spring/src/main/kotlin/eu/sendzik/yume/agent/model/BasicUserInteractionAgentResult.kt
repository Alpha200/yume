package eu.sendzik.yume.agent.model

data class BasicUserInteractionAgentResult(
    val messageToUser: String?,
    val memoryUpdateTask: String?,
    val dayPlannerUpdateTask: String?,
    val reasoning: String?
)