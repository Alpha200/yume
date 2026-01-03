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
    abstract val memoryType: String
    abstract fun toFormattedString(compact: Boolean = false): String
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
    override val memoryType: String = "USER_PREFERENCE"
) : MemoryEntry() {
    override fun toFormattedString(compact: Boolean): String {
        return if (compact) {
            buildString {
                append("- $content")
                if (place != null) {
                    append(" (Place: $place)")
                }
            }
        } else {
            toString()
        }
    }
    
    override fun toString(): String {
        return buildString {
            appendLine("ID: $id")
            appendLine("Type: $memoryType")
            appendLine("Content: $content")
            if (place != null) {
                appendLine("Place: $place")
            }
            appendLine("Created: ${createdAt.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
            appendLine("Modified: ${modifiedAt.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
        }.trim()
    }
}

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
    val observationDate: LocalDateTime,
    override val memoryType: String = "USER_OBSERVATION"
) : MemoryEntry() {
    override fun toFormattedString(compact: Boolean): String {
        return if (compact) {
            buildString {
                appendLine("Content: $content")
                if (place != null) {
                    appendLine("Place: $place")
                }
                appendLine("Observation Date: ${observationDate.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
            }.trim()
        } else {
            toString()
        }
    }
    
    override fun toString(): String {
        return buildString {
            appendLine("ID: $id")
            appendLine("Type: $memoryType")
            appendLine("Content: $content")
            if (place != null) {
                appendLine("Place: $place")
            }
            appendLine("Created: ${createdAt.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
            appendLine("Modified: ${modifiedAt.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
            appendLine("Observation Date: ${observationDate.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
        }.trim()
    }
}

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
    val reminderOptions: ReminderOptions,
    override val memoryType: String = "REMINDER"
) : MemoryEntry() {
    override fun toFormattedString(compact: Boolean): String {
        return if (compact) {
            buildString {
                appendLine("Content: $content")
                if (place != null) {
                    appendLine("Place: $place")
                }
                append(formatReminderSchedule())
            }.trim()
        } else {
            toString()
        }
    }
    
    override fun toString(): String {
        return buildString {
            appendLine("ID: $id")
            appendLine("Type: $memoryType")
            appendLine("Content: $content")
            if (place != null) {
                appendLine("Place: $place")
            }
            appendLine("Created: ${createdAt.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
            appendLine("Modified: ${modifiedAt.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")

            // Format reminder schedule
            append(formatReminderSchedule())
        }.trim()
    }
    
    private fun formatReminderSchedule(): String {
        return buildString {
            appendLine("Reminder Schedule:")

            when {
                reminderOptions.datetimeValue != null -> {
                    appendLine("  Type: One-time")
                    appendLine("  Scheduled for: ${reminderOptions.datetimeValue!!.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))}")
                }
                reminderOptions.timeValue != null -> {
                    appendLine("  Type: Recurring")
                    appendLine("  Time: ${reminderOptions.timeValue}")
                    if (!reminderOptions.daysOfWeek.isNullOrEmpty()) {
                        appendLine("  Days: ${reminderOptions.daysOfWeek!!.joinToString(", ")}")
                    } else {
                        appendLine("  Days: Daily")
                    }
                }
                reminderOptions.location != null -> {
                    appendLine("  Type: Location-based")
                    appendLine("  Location: ${reminderOptions.location}")
                    if (reminderOptions.triggerType != null) {
                        val triggerText = if (reminderOptions.triggerType == "enter") "enter" else "leave"
                        appendLine("  Trigger: On $triggerText")
                    }
                }
            }
        }
    }
}

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
