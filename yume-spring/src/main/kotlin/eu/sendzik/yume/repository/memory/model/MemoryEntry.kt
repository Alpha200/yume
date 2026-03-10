package eu.sendzik.yume.repository.memory.model

import java.time.LocalDateTime

/**
 * Base class for all memory entries
 */
sealed class MemoryEntry {
    abstract val id: String
    abstract val content: String
    abstract val place: String?
    abstract val createdAt: LocalDateTime
    abstract val modifiedAt: LocalDateTime
    abstract val type: String
    abstract fun toFormattedString(compact: Boolean = false): String
}

/**
 * Memory entry for user preferences
 */
data class UserPreferenceEntry(
    override val id: String,
    override val content: String,
    override val place: String?,
    override val createdAt: LocalDateTime,
    override val modifiedAt: LocalDateTime,
    override val type: String = "user_preference"
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
            appendLine("Type: $type")
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
data class UserObservationEntry(
    override val id: String,
    override val content: String,
    override val place: String?,
    override val createdAt: LocalDateTime,
    override val modifiedAt: LocalDateTime,
    val observationDate: LocalDateTime,
    override val type: String = "user_observation"
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
            appendLine("Type: $type")
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
data class ReminderEntry(
    override val id: String,
    override val content: String,
    override val place: String?,
    override val createdAt: LocalDateTime,
    override val modifiedAt: LocalDateTime,
    val reminderOptions: ReminderOptions,
    override val type: String = "reminder"
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
            appendLine("Type: $type")
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
    var datetimeValue: LocalDateTime? = null,
    var timeValue: String? = null,
    var daysOfWeek: List<String>? = null,
    var location: String? = null,
    var triggerType: String? = null
)
