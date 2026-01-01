package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.repository.memory.model.ReminderOptions
import eu.sendzik.yume.service.memory.MemoryManagerService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

@Component
@Suppress("unused")
class MemoryManagerTools(
    private val memoryManagerService: MemoryManagerService,
    private val logger: KLogger,
) {

    @Tool("Create a new user preference or update an existing one")
    fun upsertUserPreference(
        @P("Preference content")
        content: String,
        @P("Memory ID to update (omit to create new)", required = false)
        memoryId: String? = null,
        @P("Associated place/location", required = false)
        place: String? = null
    ): String {
        try {
            val resultId = memoryManagerService.upsertUserPreference(
                content = content,
                memoryId = memoryId,
                place = place
            )
            val action = if (memoryId != null) "updated" else "created"
            return "User preference $action with ID: $resultId"
        } catch (ex: RuntimeException) {
            logger.error(ex) { "Error creating/updating user preference" }
            return "Tool execution failed: ${ex.message}"
        }
    }

    @Tool("Create a new user observation or update an existing one with an observation date")
    fun upsertUserObservation(
        @P("Observation content")
        content: String,
        @P("Date and time of the observation (can be omitted on creation)", required = false)
        observationDate: LocalDateTime? = null,
        @P("Memory ID to update (omit to create new)", required = false)
        memoryId: String? = null,
        @P("Associated place/location", required = false)
        place: String? = null
    ): String {
        return try {
            val resultId = memoryManagerService.upsertUserObservation(
                content = content,
                observationDate = observationDate ?: LocalDateTime.now(),
                memoryId = memoryId,
                place = place
            )
            val action = if (memoryId != null) "updated" else "created"
            "User observation $action with ID: $resultId"
        } catch (e: RuntimeException) {
            logger.error(e) { "Error creating/updating user observation" }
            "Tool execution failed: ${e.message}"
        }
    }

    @Tool("Create or update a reminder with various trigger types (one-time, recurring, or location-based)")
    fun upsertReminder(
        @P("Reminder content")
        content: String,
        @P("For one-time reminders", required = false)
        reminderDatetime: LocalDateTime? = null,
        @P("For recurring reminders: time in HH:MM format", required = false)
        reminderTime: String? = null,
        @P("For recurring reminders: list of weekday names (Monday, Tuesday, etc.)", required = false)
        daysOfWeek: List<String>? = null,
        @P("For location-based reminders: geofence location name", required = false)
        location: String? = null,
        @P("For location-based reminders: 'enter' or 'leave'", required = false)
        triggerType: String? = null,
        @P("Memory ID to update (omit to create new)", required = false)
        memoryId: String? = null,
        @P("Associated place/location", required = false)
        place: String? = null
    ): String {
        return try {
            val reminderOptions = ReminderOptions()

            if (reminderDatetime != null) {
                reminderOptions.datetimeValue = reminderDatetime
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
            logger.error(e) { "Error parsing reminder" }
            "Error creating/updating reminder: ${e.message}"
        } catch (e: RuntimeException) {
            logger.error { "Error creating/updating reminder: ${e.message}" }
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