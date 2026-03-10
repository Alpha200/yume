package eu.sendzik.yume.repository.memory.model

import org.springframework.data.annotation.Id
import org.springframework.data.mongodb.core.mapping.Document
import org.springframework.data.mongodb.core.mapping.Field
import java.time.LocalDateTime

@Document(collection = "memories")
data class MemoryDocument(
    @Id
    val id: String,
    val type: String,
    val content: String,
    val place: String? = null,
    @Field("created_at")
    val createdAt: LocalDateTime,
    @Field("modified_at")
    val modifiedAt: LocalDateTime,
    // UserObservationEntry
    @Field("observation_date")
    val observationDate: LocalDateTime? = null,
    // ReminderEntry
    @Field("reminder_options")
    val reminderOptions: ReminderOptions? = null
)

