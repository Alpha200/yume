package eu.sendzik.yume.configuration

import dev.langchain4j.model.chat.Capability
import dev.langchain4j.model.chat.ChatModel
import dev.langchain4j.model.openai.OpenAiChatModel
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class ChatModelConfiguration(
    @Value("\${langchain4j.open-ai.chat-model.api-key}")
    private val openAiApiKey: String,
    @Value("\${langchain4j.open-ai.chat-model.base-url}")
    private val baseUrl: String,
    val agentConfiguration: AgentConfiguration,
    @Value("\${langchain4j.open-ai.chat-model.log-request}")
    private val logRequest: Boolean,
    @Value("\${langchain4j.open-ai.chat-model.log-response}")
    private val logResponse: Boolean,
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
            .build()
    }
}