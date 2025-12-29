package eu.sendzik.yume.configuration

import dev.langchain4j.http.client.HttpClientBuilder
import dev.langchain4j.http.client.spring.restclient.SpringRestClientBuilder
import dev.langchain4j.http.client.spring.restclient.SpringRestClientBuilderFactory
import dev.langchain4j.model.embedding.EmbeddingModel
import dev.langchain4j.model.openai.OpenAiEmbeddingModel
import dev.langchain4j.model.openai.OpenAiEmbeddingModelName
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class EmbeddingModelConfiguration {
    @Bean
    fun embeddingModel(
        @Value("\${langchain4j.open-ai.chat-model.api-key}")
        openAiApiKey: String,
        @Value("\${langchain4j.open-ai.chat-model.base-url}")
        baseUrl: String,
        openAiEmbeddingModelHttpClientBuilder: HttpClientBuilder
    ): EmbeddingModel {
        return OpenAiEmbeddingModel
            .builder()
            .modelName(OpenAiEmbeddingModelName.TEXT_EMBEDDING_3_LARGE)
            .baseUrl(baseUrl)
            .apiKey(openAiApiKey)
            .httpClientBuilder(openAiEmbeddingModelHttpClientBuilder)
            .build()
    }
}