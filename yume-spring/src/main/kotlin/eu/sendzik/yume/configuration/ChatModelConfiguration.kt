package eu.sendzik.yume.configuration

import dev.langchain4j.model.chat.Capability
import dev.langchain4j.model.chat.ChatModel
import dev.langchain4j.model.openai.OpenAiChatModel
import eu.sendzik.yume.service.interaction.InteractionTrackerService
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class ChatModelConfiguration(
    private val interactionTrackerService: InteractionTrackerService,
    @Value("\${langchain4j.open-ai.chat-model.api-key}")
    private val openAiApiKey: String,
    @Value("\${langchain4j.open-ai.chat-model.base-url}")
    private val baseUrl: String,
    @Value("\${langchain4j.open-ai.chat-model.log-request}")
    private val logRequest: Boolean,
    @Value("\${langchain4j.open-ai.chat-model.log-response}")
    private val logResponse: Boolean,
    private val agentConfiguration: AgentConfiguration,
) {
    @Bean
    fun genericChatModel() = buildYumeChatModel(
        "Generic"
    )

    @Bean
    fun efaChatModel() = buildYumeChatModel(
        agentName = "EFA",
    )

    @Bean
    fun dayPlanChatModel() = buildYumeChatModel(
        agentName = "DayPlan",
    )

    @Bean
    fun kitchenOwlChatModel() = buildYumeChatModel(
        agentName = "KitchenOwl",
    )

    @Bean
    fun memoryManagerChatModel() = buildYumeChatModel(
        agentName = "MemoryManager",
    )

    @Bean
    fun schedulerChatModel() = buildYumeChatModel(
        agentName = "Scheduler",
    )

    @Bean
    fun routerChatModel() = buildYumeChatModel(
        agentName = "Router",
        modelName = agentConfiguration.model.routerAgentModel,
    )

    @Bean
    fun conversationSummarizerModel() = buildYumeChatModel(
        agentName = "Summarizer",
        modelName = agentConfiguration.model.conversationSummarizerModel,
        jsonOutput = false
    )

    private fun buildYumeChatModel(
        agentName: String,
        jsonOutput: Boolean = true,
        modelName: String? = null,
    ): ChatModel {
        return OpenAiChatModel
            .builder()
            .modelName(modelName ?: agentConfiguration.model.defaultAgentModel)
            .baseUrl(baseUrl)
            .apiKey(openAiApiKey)
            .logRequests(logRequest)
            .logResponses(logResponse)
            .listeners(listOf(interactionTrackerService))
            .metadata(mapOf("agentName" to agentName))
            .let {
                if (jsonOutput) {
                    it.supportedCapabilities(Capability.RESPONSE_FORMAT_JSON_SCHEMA).strictJsonSchema(true)
                } else {
                    it
                }
            }
            .build()
    }
}