package eu.sendzik.yume.repository.memory

import dev.langchain4j.data.segment.TextSegment
import dev.langchain4j.data.segment.TextSegment.textSegment
import dev.langchain4j.model.embedding.EmbeddingModel
import dev.langchain4j.store.embedding.EmbeddingSearchRequest
import dev.langchain4j.store.embedding.EmbeddingStore
import eu.sendzik.yume.repository.memory.model.MemoryEntry
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.data.repository.CrudRepository
import org.springframework.stereotype.Repository
import java.util.Optional
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Repository
class RagMemoryRepository (
    private val embeddingModel: EmbeddingModel,
    private val embeddingStore: EmbeddingStore<TextSegment>,
    private val mongoRepository: MongoMemoryRepository,
    private val logger: KLogger,
) : CrudRepository<MemoryEntry, String> {
    private val lock = ReentrantLock()

    override fun <S : MemoryEntry> save(entity: S): S = lock.withLock {
        val savedEntity = mongoRepository.save(entity)
        val embedding = embeddingModel.embed(savedEntity.formatForRAG()).content()
        embeddingStore.add(savedEntity.id, embedding)
        return savedEntity
    }

    override fun <S : MemoryEntry> saveAll(entities: Iterable<S>): Iterable<S> = lock.withLock {
        val savedEntities = saveAll(entities)
        val embeddings = embeddingModel.embedAll(entities.map { textSegment(it.formatForRAG()) }).content()
        embeddingStore.addAll(
            savedEntities.map { it.id },
            embeddings,
            null
        )
        return savedEntities
    }

    override fun findById(id: String): Optional<MemoryEntry> {
        return findById(id)
    }

    override fun existsById(id: String): Boolean {
        return mongoRepository.existsById(id)
    }

    override fun findAll(): Iterable<MemoryEntry> {
        return mongoRepository.findAll()
    }

    override fun findAllById(ids: Iterable<String>): Iterable<MemoryEntry> {
        return mongoRepository.findAllById(ids)
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
            mongoRepository.delete(entity)
            embeddingStore.remove(entity.id)
        }
    }

    override fun deleteAllById(ids: Iterable<String>) {
        val idsList = ids.toList()
        mongoRepository.deleteAllById(ids)
        embeddingStore.removeAll(idsList)
    }

    override fun deleteAll(entities: Iterable<MemoryEntry>) {
        lock.withLock {
            mongoRepository.deleteAll(entities)
            embeddingStore.removeAll(entities.map { it.id })
        }
    }

    override fun deleteAll() {
        lock.withLock {
            mongoRepository.deleteAll()
            embeddingStore.removeAll()
        }
    }

    fun resetRagDatabase() {
        lock.withLock {
            logger.info {"Resetting RAG memory repository..." }
            embeddingStore.removeAll()

            val data = mongoRepository.findAll().asSequence()

            do {
                val batch = data.take(100).toList()
                if (batch.isEmpty()) {
                    break
                }
                val embeddings = embeddingModel.embedAll(batch.map { textSegment(it.formatForRAG()) }).content()
                embeddingStore.addAll(
                    batch.map { it.id },
                    embeddings,
                    null
                )
            } while (true)

            logger.info {"Finished resetting RAG memory repository..." }
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

        return if(matches.isEmpty()) {
            emptyList()
        } else {
            val ids = matches.map { it.embeddingId() }
            mongoRepository.findAllById(ids)
        }
    }

    fun MemoryEntry.formatForRAG() = buildString {
        if (!place.isNullOrBlank()) {
            append(place)
            append(" - ")
        }
        append(content)

        // TODO: Add more fields
    }
}