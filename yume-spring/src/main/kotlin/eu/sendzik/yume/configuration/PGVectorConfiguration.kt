package eu.sendzik.yume.configuration

import dev.langchain4j.data.segment.TextSegment
import dev.langchain4j.model.openai.OpenAiEmbeddingModel
import dev.langchain4j.model.openai.OpenAiEmbeddingModelName
import dev.langchain4j.store.embedding.EmbeddingStore
import dev.langchain4j.store.embedding.pgvector.PgVectorEmbeddingStore
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class PGVectorConfiguration {
    @Bean
    fun embeddingStore(
        @Value("\${spring.datasource.vector.database}")
        database: String,
        @Value("\${spring.datasource.vector.username}")
        user: String,
        @Value("\${spring.datasource.vector.password}")
        password: String,
        @Value("\${spring.datasource.vector.host}")
        host: String,
        @Value("\${spring.datasource.vector.table}")
        table: String,
        @Value("\${spring.datasource.vector.port}")
        port: Int,
    ): EmbeddingStore<TextSegment> {
        return PgVectorEmbeddingStore
            .builder()
            .database(database)
            .host(host)
            .port(port)
            .user(user)
            .password(password)
            .table(table)
            .createTable(true)
            .dimension(OpenAiEmbeddingModelName.TEXT_EMBEDDING_3_LARGE.dimension())
            .build()
    }
}