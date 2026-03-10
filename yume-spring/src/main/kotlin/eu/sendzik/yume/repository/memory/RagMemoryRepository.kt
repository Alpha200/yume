package eu.sendzik.yume.repository.memory

import dev.langchain4j.data.segment.TextSegment
import dev.langchain4j.data.segment.TextSegment.textSegment
import dev.langchain4j.model.embedding.EmbeddingModel
import dev.langchain4j.store.embedding.EmbeddingSearchRequest
import dev.langchain4j.store.embedding.EmbeddingStore
import eu.sendzik.yume.repository.memory.model.MemoryEntry
import eu.sendzik.yume.repository.memory.model.toDocument
import eu.sendzik.yume.repository.memory.model.toEntry
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.data.repository.CrudRepository
import org.springframework.stereotype.Repository
import java.util.Optional
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Repository
class RagMemoryRepository(
    private val embeddingModel: EmbeddingModel,
    private val embeddingStore: EmbeddingStore<TextSegment>,
    private val mongoRepository: MongoMemoryRepository,
    private val logger: KLogger,
) : CrudRepository<MemoryEntry, String> {
    private val lock = ReentrantLock()

    override fun <S : MemoryEntry> save(entity: S): S = lock.withLock {
        mongoRepository.save(entity.toDocument())
        val embedding = embeddingModel.embed(entity.formatForRAG()).content()
        embeddingStore.add(entity.id, embedding)
        return entity
    }

    override fun <S : MemoryEntry> saveAll(entities: Iterable<S>): Iterable<S> = lock.withLock {
        mongoRepository.saveAll(entities.map { it.toDocument() })
        val entitiesList = entities.toList()
        val embeddings = embeddingModel.embedAll(entitiesList.map { textSegment(it.formatForRAG()) }).content()
        embeddingStore.addAll(entitiesList.map { it.id }, embeddings, null)
        return entitiesList
    }

    override fun findById(id: String): Optional<MemoryEntry> {
        return mongoRepository.findById(id).map { it.toEntry() }
    }

    override fun existsById(id: String): Boolean {
        return mongoRepository.existsById(id)
    }

    override fun findAll(): Iterable<MemoryEntry> {
        return mongoRepository.findAll().map { it.toEntry() }
    }

    override fun findAllById(ids: Iterable<String>): Iterable<MemoryEntry> {
        return mongoRepository.findAllById(ids).map { it.toEntry() }
    }

    override fun count(): Long {
        return mongoRepository.count()
    }

    override fun deleteById(id: String) {
        lock.withLock {
            mongoRepository.deleteById(id)
            embeddingStore.remove(id)
        }
    }

    override fun delete(entity: MemoryEntry) {
        lock.withLock {
            mongoRepository.deleteById(entity.id)
            embeddingStore.remove(entity.id)
        }
    }

    override fun deleteAllById(ids: Iterable<String>) {
        val idsList = ids.toList()
        mongoRepository.deleteAllById(idsList)
        embeddingStore.removeAll(idsList)
    }

    override fun deleteAll(entities: Iterable<MemoryEntry>) {
        lock.withLock {
            val idsList = entities.map { it.id }
            mongoRepository.deleteAllById(idsList)
            embeddingStore.removeAll(idsList)
        }
    }

    override fun deleteAll() {
        lock.withLock {
            mongoRepository.deleteAll()
            embeddingStore.removeAll()
        }
    }

    fun findAllByMemoryType(type: String): List<MemoryEntry> {
        return mongoRepository.findAllByMemoryType(type).map { it.toEntry() }
    }

    fun resetRagDatabase() {
        lock.withLock {
            logger.info { "Resetting RAG memory repository..." }
            embeddingStore.removeAll()

            val data = mongoRepository.findAll().asSequence()

            data.chunked(100).forEach { batch ->
                val entries = batch.map { it.toEntry() }
                val embeddings = embeddingModel.embedAll(entries.map { textSegment(it.formatForRAG()) }).content()
                embeddingStore.addAll(entries.map { it.id }, embeddings, null)
            }

            logger.info { "Finished resetting RAG memory repository..." }
        }
    }

    fun searchAll(query: String, minScore: Double = 0.5, maxResults: Int = 20): List<MemoryEntry> {
        val embedding = embeddingModel.embed(query).content()
        val matches = embeddingStore.search(
            EmbeddingSearchRequest.builder()
                .queryEmbedding(embedding)
                .minScore(minScore)
                .maxResults(maxResults)
                .build()
        ).matches()

        logger.debug { "RAG search for query '$query' returned ${matches.size} matches. Scores: [${matches.map { it.score() }}]" }

        return if (matches.isEmpty()) {
            emptyList()
        } else {
            val ids = matches.map { it.embeddingId() }
            mongoRepository.findAllById(ids).map { it.toEntry() }
        }
    }

    fun MemoryEntry.formatForRAG() = buildString {
        if (!place.isNullOrBlank()) {
            append(place)
            append(" - ")
        }
        append(content)
    }
}