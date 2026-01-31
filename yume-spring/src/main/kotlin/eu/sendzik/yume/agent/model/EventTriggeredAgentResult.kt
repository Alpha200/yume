package eu.sendzik.yume.agent.model

data class EventTriggeredAgentResult(
    override val messageToUser: String?,
    override val memoryUpdateTask: String?,
    override val dayPlannerUpdateTask: String?,
    override val reasoning: String?,
    val executionSummary: String?
) : BasicUserInteractionAgentResult(messageToUser, memoryUpdateTask, dayPlannerUpdateTask, reasoning)
