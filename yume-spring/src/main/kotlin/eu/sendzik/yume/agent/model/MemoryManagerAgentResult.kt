package eu.sendzik.yume.agent.model

data class MemoryManagerAgentResult(
    val actionsTaken: List<String>,
    val reasoning: String,
)