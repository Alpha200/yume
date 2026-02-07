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
        agentName = "Generic",
        modelName = agentConfiguration.model.genericAgentModel,
    )

    @Bean
    fun efaChatModel() = buildYumeChatModel(
        agentName = "EFA",
        modelName = agentConfiguration.model.efaAgentModel,
    )

    @Bean
    fun dayPlanChatModel() = buildYumeChatModel(
        agentName = "DayPlan",
        modelName = agentConfiguration.model.dayPlanAgentModel,
    )

    @Bean
    fun kitchenOwlChatModel() = buildYumeChatModel(
        agentName = "KitchenOwl",
        modelName = agentConfiguration.model.kitchenOwlAgentModel,
    )

    @Bean
    fun memoryManagerChatModel() = buildYumeChatModel(
        agentName = "MemoryManager",
        modelName = agentConfiguration.model.memoryManagerAgentModel,
    )

    @Bean
    fun schedulerChatModel() = buildYumeChatModel(
        agentName = "Scheduler",
        modelName = agentConfiguration.model.schedulerAgentModel,
    )

    @Bean
    fun routerChatModel() = buildYumeChatModel(
        agentName = "Router",
        modelName = agentConfiguration.model.routerAgentModel,
    )

    @Bean
    fun conversationSummarizerChatModel() = buildYumeChatModel(
        agentName = "Summarizer",
        modelName = agentConfiguration.model.conversationSummarizerModel,
        jsonOutput = false
    )

    @Bean
    fun memorySummarizerChatModel() = buildYumeChatModel(
        agentName = "MemorySummarizer",
        modelName = agentConfiguration.model.memorySummarizerModel,
        jsonOutput = false
    )

    @Bean
    fun eInkChatModel() = buildYumeChatModel(
        agentName = "EInkDisplay",
        modelName = agentConfiguration.model.eInkChatModel,
        jsonOutput = false
    )

    @Bean
    fun sportsChatModel() = buildYumeChatModel(
        agentName = "Sports",
        modelName = agentConfiguration.model.sportsAgentModel,
    )

    private fun buildYumeChatModel(
        agentName: String,
        modelName: String,
        jsonOutput: Boolean = true,
    ): ChatModel {
        return OpenAiChatModel
            .builder()
            .modelName(modelName)
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