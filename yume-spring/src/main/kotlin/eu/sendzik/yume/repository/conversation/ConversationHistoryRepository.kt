package eu.sendzik.yume.repository.conversation

import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntry
import org.springframework.data.domain.Limit
import org.springframework.data.mongodb.repository.MongoRepository
import org.springframework.data.mongodb.repository.Query

interface ConversationHistoryRepository : MongoRepository<ConversationHistoryEntry, String>{

    @Query(value = "{}", sort = "{ 'timestamp': -1 }")
    fun findAllOrderByTimestampDesc(limit: Limit): List<ConversationHistoryEntry>
}