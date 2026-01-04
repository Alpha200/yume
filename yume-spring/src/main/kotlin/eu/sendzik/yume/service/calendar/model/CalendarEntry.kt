package eu.sendzik.yume.service.calendar.model

import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

data class CalendarEntry(
    val uid: String,
    val title: String,
    val description: String? = null,
    val startTime: LocalDateTime,
    val endTime: LocalDateTime,
    val location: String? = null,
    val allDay: Boolean = false,
) {
    fun formatForLLM(): String {
        val datePattern = if (allDay) "EEEE yyyy-MM-dd" else "EEEE yyyy-MM-dd HH:mm:ss"
        val startStr = startTime.format(DateTimeFormatter.ofPattern(datePattern))
        val endStr = endTime.format(DateTimeFormatter.ofPattern(datePattern))

        return buildString {
            appendLine("Title: $title")
            appendLine("Start Time: $startStr")
            appendLine("End Time: $endStr")

            if (description != null) {
                append("Description: $description")
            }

            if (location != null) {
                append("Location: $location")
            }
            append("All Day Event: $allDay")
        }
    }
}
