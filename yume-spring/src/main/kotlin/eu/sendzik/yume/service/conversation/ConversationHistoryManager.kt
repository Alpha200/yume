package eu.sendzik.yume.service.conversation

import eu.sendzik.yume.repository.conversation.ConversationHistoryRepository
import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntry
import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntryType
import eu.sendzik.yume.utils.formatTimestampForLLM
import org.springframework.data.domain.Limit
import org.springframework.stereotype.Service
import java.time.LocalDateTime

@Service
class ConversationHistoryManager(
    private val conversationHistoryRepository: ConversationHistoryRepository,
) {
    fun getRecentHistoryFormatted(limit: Int = 20): String {
        val history = conversationHistoryRepository.findAllOrderByTimestampDesc(Limit.of(limit))
        return history.joinToString(separator = "\n") { entry ->
            "[${entry.type} - ${formatTimestampForLLM(entry.timestamp, true)}] ${entry.content}"
        }
    }

    fun addEntry(content: String, type: ConversationHistoryEntryType, timestamp: LocalDateTime? = null) {
        val entry = ConversationHistoryEntry(
            content = content,
            type = type,
            timestamp = timestamp ?: LocalDateTime.now()
        )
        conversationHistoryRepository.save(entry)
    }
}