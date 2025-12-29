package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.repository.memory.model.ReminderOptions
import eu.sendzik.yume.service.memory.MemoryManagerService
import org.springframework.stereotype.Component
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

@Component
class MemoryManagerTools(
    private val memoryManagerService: MemoryManagerService,
) {

    @Tool("Create a new user preference or update an existing one")
    fun upsertUserPreference(
        @P("Preference content")
        content: String,
        @P("Memory ID to update (omit to create new)")
        memoryId: String? = null,
        @P("Associated place/location")
        place: String? = null
    ): String {
        val resultId = memoryManagerService.upsertUserPreference(
            content = content,
            memoryId = memoryId,
            place = place
        )
        val action = if (memoryId != null) "updated" else "created"
        return "User preference $action with ID: $resultId"
    }

    @Tool("Create a new user observation or update an existing one with an observation date")
    fun upsertUserObservation(
        @P("Observation content")
        content: String,
        @P("Date in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format")
        observationDate: String,
        @P("Memory ID to update (omit to create new)")
        memoryId: String? = null,
        @P("Associated place/location")
        place: String? = null
    ): String {
        return try {
            val obsDate = try {
                // Try to parse with time first (YYYY-MM-DD HH:MM:SS)
                LocalDateTime.parse(observationDate, DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
            } catch (e: DateTimeParseException) {
                // If that fails, try date only (YYYY-MM-DD) and set time to current time
                try {
                    val datePart = LocalDateTime.parse("${observationDate}T00:00:00")
                    datePart.withHour(LocalDateTime.now().hour)
                        .withMinute(LocalDateTime.now().minute)
                        .withSecond(LocalDateTime.now().second)
                } catch (_: DateTimeParseException) {
                    throw e
                }
            }

            val resultId = memoryManagerService.upsertUserObservation(
                content = content,
                observationDate = obsDate,
                memoryId = memoryId,
                place = place
            )
            val action = if (memoryId != null) "updated" else "created"
            "User observation $action with ID: $resultId"
        } catch (e: DateTimeParseException) {
            "Error parsing observation date '$observationDate': ${e.message}. Please use format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
        }
    }

    @Tool("Create or update a reminder with various trigger types (one-time, recurring, or location-based)")
    fun upsertReminder(
        @P("Reminder content")
        content: String,
        @P("For one-time reminders: datetime in YYYY-MM-DD HH:MM:SS format")
        reminderDatetime: String? = null,
        @P("For recurring reminders: time in HH:MM format")
        reminderTime: String? = null,
        @P("For recurring reminders: list of weekday names (Monday, Tuesday, etc.)")
        daysOfWeek: List<String>? = null,
        @P("For location-based reminders: geofence location name")
        location: String? = null,
        @P("For location-based reminders: 'enter' or 'leave'")
        triggerType: String? = null,
        @P("Memory ID to update (omit to create new)")
        memoryId: String? = null,
        @P("Associated place/location")
        place: String? = null
    ): String {
        return try {
            val reminderOptions = ReminderOptions()

            if (reminderDatetime != null) {
                reminderOptions.datetimeValue = LocalDateTime.parse(
                    reminderDatetime,
                    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
                )
            }

            if (reminderTime != null) {
                reminderOptions.timeValue = reminderTime
            }

            if (daysOfWeek != null) {
                reminderOptions.daysOfWeek = daysOfWeek
            }

            if (location != null) {
                reminderOptions.location = location
                // Validate trigger_type if location is specified
                if (triggerType != null && triggerType !in listOf("enter", "leave")) {
                    return "Error: triggerType must be 'enter' or 'leave'"
                }
                reminderOptions.triggerType = triggerType ?: "enter" // Default to "enter" if not specified
            }

            // Validate that we have a reminder type
            val hasTimeReminder = reminderOptions.datetimeValue != null ||
                (reminderOptions.timeValue != null && reminderOptions.daysOfWeek != null)
            val hasLocationReminder = reminderOptions.location != null

            if (!hasTimeReminder && !hasLocationReminder) {
                return "Error: Either provide reminderDatetime for one-time reminders, both reminderTime and daysOfWeek for recurring reminders, or location and triggerType for location-based reminders"
            }

            val resultId = memoryManagerService.upsertReminder(
                content = content,
                reminderOptions = reminderOptions,
                memoryId = memoryId,
                place = place
            )
            val action = if (memoryId != null) "updated" else "created"
            "Reminder $action with ID: $resultId"
        } catch (e: DateTimeParseException) {
            "Error creating/updating reminder: ${e.message}"
        } catch (e: Exception) {
            "Error creating/updating reminder: ${e.message}"
        }
    }

    @Tool("Delete a memory by its ID")
    fun deleteMemory(
        @P("ID of the memory to delete")
        memoryId: String
    ): String {
        val success = memoryManagerService.deleteMemory(memoryId)
        return if (success) {
            "Memory with ID $memoryId has been deleted."
        } else {
            "Memory with ID $memoryId not found."
        }
    }
}