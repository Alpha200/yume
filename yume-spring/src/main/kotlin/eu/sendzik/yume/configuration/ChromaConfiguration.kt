//package eu.sendzik.yume.configuration
//
//import dev.langchain4j.data.segment.TextSegment
//import dev.langchain4j.store.embedding.EmbeddingStore
//import dev.langchain4j.store.embedding.chroma.ChromaApiVersion
//import dev.langchain4j.store.embedding.chroma.ChromaEmbeddingStore
//import io.github.locxngo.chroma.AdminClient
//import io.github.locxngo.chroma.Client
//import io.github.locxngo.chroma.Collection
//import io.github.locxngo.chroma.Config
//import io.github.locxngo.chroma.exception.NotFoundException
//import io.github.locxngo.chroma.params.CreateCollectionParam
//import io.github.locxngo.chroma.params.GetCollectionParam
//import org.springframework.beans.factory.annotation.Value
//import org.springframework.context.annotation.Bean
//import org.springframework.context.annotation.Configuration
//
//@Configuration
//class ChromaConfiguration {
//    @Bean
//    fun chromaEmbeddingStore(
//        @Value("\${langchain4j.chroma.base-url}")
//        baseUrl: String,
//        @Value("\${langchain4j.chroma.tenant-name:yume}")
//        tenantName: String,
//        @Value("\${langchain4j.chroma.database-name:yume}")
//        databaseName: String,
//        @Value("\${langchain4j.chroma.collection-name:yume}")
//        collectionName: String,
//    ): EmbeddingStore<TextSegment> = ChromaEmbeddingStore
//        .builder()
//        .apiVersion(ChromaApiVersion.V2)
//        .baseUrl(baseUrl)
//        .tenantName(tenantName)
//        .databaseName(databaseName)
//        .collectionName(collectionName)
//        .build()
//
//    @Bean
//    fun chromaClient(
//        @Value("\${langchain4j.chroma.base-url}")
//        baseUrl: String,
//        @Value("\${langchain4j.chroma.tenant-name}")
//        tenantName: String,
//        @Value("\${langchain4j.chroma.database-name}")
//        databaseName: String,
//        @Suppress("UNUSED") // Required to initialize before client
//        embeddingStore: EmbeddingStore<TextSegment>,
//    ): Client {
//        val config = Config.builder()
//            .tenant(tenantName)
//            .endpoint(baseUrl)
//            .database(databaseName)
//            .build()
//
//        //val adminClient = AdminClient(config)
//
//        //// Ensure database exists
//        //val response = adminClient.getDatabase(tenantName, databaseName)
//        //if (response.errorCode == 404) {
//        //    adminClient.createDatabase(tenantName, databaseName)
//        //}
//
//        return Client(config)
//    }
//
//    @Bean
//    fun memoryCollection(
//        chromaClient: Client,
//        @Value("\${langchain4j.chroma.collection-name}")
//        collectionName: String,
//    ): Collection {
//        return try {
//            chromaClient.getCollection(
//                GetCollectionParam.builder().nameOrId(collectionName).build()
//            )
//        } catch (_: NotFoundException) {
//            chromaClient.createCollection(
//                CreateCollectionParam.builder()
//                    .name(collectionName)
//                    .build()
//            )
//        }
//    }
//}