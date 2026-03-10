package eu.sendzik.yume.repository.memory

import eu.sendzik.yume.repository.memory.model.MemoryDocument
import org.springframework.data.mongodb.repository.MongoRepository
import org.springframework.data.mongodb.repository.Query
import org.springframework.stereotype.Repository

@Repository
interface MongoMemoryRepository : MongoRepository<MemoryDocument, String> {
    @Query("{ 'type': ?0 }")
    fun findAllByMemoryType(type: String): List<MemoryDocument>
}
