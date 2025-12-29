package eu.sendzik.yume.agent.model

data class DayPlanAgentResult(
    val actionsTaken: List<String>?,
    val reasoning: String,
)