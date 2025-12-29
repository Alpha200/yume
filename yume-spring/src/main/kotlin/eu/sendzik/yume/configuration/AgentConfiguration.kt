package eu.sendzik.yume.configuration

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties("yume.agent")
class AgentConfiguration(
    val model: Model,
    val preferences: Preferences
) {

    class Model(
        val defaultAgentModel: String,
        val routerAgentModel: String,
    )

    class Preferences(
        val userLanguage: String
    )
}