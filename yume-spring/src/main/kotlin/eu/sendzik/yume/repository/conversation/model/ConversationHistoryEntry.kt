package eu.sendzik.yume.repository.conversation.model

import org.springframework.data.annotation.TypeAlias
import org.springframework.data.mongodb.core.mapping.Document
import java.time.LocalDateTime

@Document(collection = "conversation_history")
@TypeAlias("ConversationHistoryEntry")
data class ConversationHistoryEntry(
    val timestamp: LocalDateTime,
    val content: String,
    val type: ConversationHistoryEntryType,
    val eventId: String? = null
)