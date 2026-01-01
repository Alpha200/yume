package eu.sendzik.yume.configuration

import dev.langchain4j.model.chat.Capability
import dev.langchain4j.model.chat.ChatModel
import dev.langchain4j.model.chat.listener.ChatModelErrorContext
import dev.langchain4j.model.chat.listener.ChatModelListener
import dev.langchain4j.model.chat.listener.ChatModelRequestContext
import dev.langchain4j.model.chat.listener.ChatModelResponseContext
import dev.langchain4j.model.openai.OpenAiChatModel
import eu.sendzik.yume.service.interaction.InteractionTrackerService
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class ChatModelConfiguration(
    val interactionTrackerService: InteractionTrackerService,
    @Value("\${langchain4j.open-ai.chat-model.api-key}")
    private val openAiApiKey: String,
    @Value("\${langchain4j.open-ai.chat-model.base-url}")
    private val baseUrl: String,
    @Value("\${langchain4j.open-ai.chat-model.log-request}")
    private val logRequest: Boolean,
    @Value("\${langchain4j.open-ai.chat-model.log-response}")
    private val logResponse: Boolean,
    val agentConfiguration: AgentConfiguration,
) {
    @Bean
    fun defaultChatModel(): ChatModel {
        return OpenAiChatModel
            .builder()
            .baseUrl(baseUrl)
            .apiKey(openAiApiKey)
            .modelName(agentConfiguration.model.defaultAgentModel)
            .strictJsonSchema(true)
            .supportedCapabilities(Capability.RESPONSE_FORMAT_JSON_SCHEMA)
            .logRequests(logRequest)
            .logResponses(logResponse)
            .listeners(listOf(interactionTrackerService))
            .build()
    }

    @Bean
    fun routerChatModel(): ChatModel {
        return OpenAiChatModel
            .builder()
            .baseUrl(baseUrl)
            .apiKey(openAiApiKey)
            .modelName(agentConfiguration.model.routerAgentModel)
            .strictJsonSchema(true)
            .supportedCapabilities(Capability.RESPONSE_FORMAT_JSON_SCHEMA)
            .logRequests(logRequest)
            .logResponses(logResponse)
            .listeners(listOf(interactionTrackerService))
            .build()
    }

    @Bean
    fun conversationSummarizerModel(): ChatModel {
        return OpenAiChatModel
            .builder()
            .baseUrl(baseUrl)
            .apiKey(openAiApiKey)
            .modelName(agentConfiguration.model.conversationSummarizerModel)
            .logRequests(logRequest)
            .logResponses(logResponse)
            .listeners(listOf(interactionTrackerService))
            .build()
    }
}