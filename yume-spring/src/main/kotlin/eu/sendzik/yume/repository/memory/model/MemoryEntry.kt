package eu.sendzik.yume.repository.memory.model

import java.time.LocalDateTime
import org.springframework.data.annotation.Id
import org.springframework.data.annotation.TypeAlias
import org.springframework.data.mongodb.core.mapping.Document
import org.springframework.data.mongodb.core.mapping.Field

/**
 * Base class for all memory entries
 */
@Document(collection = "memories")
sealed class MemoryEntry {
    abstract val id: String
    abstract val content: String
    abstract val place: String?
    abstract val createdAt: LocalDateTime
    abstract val modifiedAt: LocalDateTime
}

/**
 * Memory entry for user preferences
 */
@TypeAlias("UserPreferenceEntry")
data class UserPreferenceEntry(
    @field:Id
    @Field("_id")
    override val id: String,
    override val content: String,
    override val place: String?,
    @Field("created_at")
    override val createdAt: LocalDateTime,
    @Field("modified_at")
    override val modifiedAt: LocalDateTime,
) : MemoryEntry()

/**
 * Memory entry for user observations with observation date
 */
@TypeAlias("UserObservationEntry")
data class UserObservationEntry(
    @field:Id
    @Field("_id")
    override val id: String,
    override val content: String,
    override val place: String?,
    @Field("created_at")
    override val createdAt: LocalDateTime,
    @Field("modified_at")
    override val modifiedAt: LocalDateTime,
    @Field("observation_date")
    val observationDate: LocalDateTime
) : MemoryEntry()

/**
 * Memory entry for reminders with reminder options
 */
@TypeAlias("ReminderEntry")
data class ReminderEntry(
    @field:Id
    @Field("_id")
    override val id: String,
    override val content: String,
    override val place: String?,
    @Field("created_at")
    override val createdAt: LocalDateTime,
    @Field("modified_at")
    override val modifiedAt: LocalDateTime,
    @Field("reminder_options")
    val reminderOptions: ReminderOptions
) : MemoryEntry()

/**
 * Reminder options configuration - supports time-based and location-based reminders
 */
data class ReminderOptions(
    @Field("datetime_value")
    var datetimeValue: LocalDateTime? = null,
    @Field("time_value")
    var timeValue: String? = null,
    @Field("days_of_week")
    var daysOfWeek: List<String>? = null,
    var location: String? = null,
    @Field("trigger_type")
    var triggerType: String? = null
)
