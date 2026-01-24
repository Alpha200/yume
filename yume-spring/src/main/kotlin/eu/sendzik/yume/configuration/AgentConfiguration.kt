package eu.sendzik.yume.configuration

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties("yume.agent")
class AgentConfiguration(
    val model: Model,
    val preferences: Preferences
) {

    class Model(
        val genericAgentModel: String,
        val efaAgentModel: String,
        val dayPlanAgentModel: String,
        val kitchenOwlAgentModel: String,
        val memoryManagerAgentModel: String,
        val schedulerAgentModel: String,
        val routerAgentModel: String,
        val conversationSummarizerModel: String,
        val memorySummarizerModel: String,
        val eInkChatModel: String,
    )

    class Preferences(
        val userLanguage: String
    )
}