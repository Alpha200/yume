/*package eu.sendzik.yume.configuration

import dev.langchain4j.model.chat.ChatModel
import dev.langchain4j.service.AiServices
import eu.sendzik.yume.agent.KitchenOwlAgent
import eu.sendzik.yume.tool.KitchenOwlReadTools
import eu.sendzik.yume.tool.KitchenOwlTools
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class AgentProviderConfiguration(
    private val defaultChatModel: ChatModel,
) {
    @Bean
    fun kitchenOwlAgent(
        kitchenOwlReadTools: KitchenOwlReadTools,
        kitchenOwlTools: KitchenOwlTools,
        @Value("classpath:prompt/default-preferences-prefix.txt")
        defaultPreferencesPrefix: String,
        @Value("classpath:prompt/kitchenowl-system-message.txt")
        kitchenOwlSystemMessage: String,
    ): KitchenOwlAgent {
        return AiServices
            .builder(KitchenOwlAgent::class.java)
            .systemMessageProvider { listOf(
                defaultPreferencesPrefix,
                kitchenOwlSystemMessage
            ).joinToString("\n") }
            .chatModel(defaultChatModel)
            .tools(kitchenOwlReadTools, kitchenOwlTools)
            .build()
    }
}
*/