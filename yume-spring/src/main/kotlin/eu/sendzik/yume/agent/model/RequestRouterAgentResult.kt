package eu.sendzik.yume.agent.model

data class RequestRouterAgentResult(
    val reasoning: String,
    val agent: YumeAgentType,
    val requiredResources: List<YumeChatResource>
)
