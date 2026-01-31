package eu.sendzik.yume.agent.model

open class BasicUserInteractionAgentResult(
    open val messageToUser: String?,
    open val memoryUpdateTask: String?,
    open val dayPlannerUpdateTask: String?,
    open val reasoning: String?
)