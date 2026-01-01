package eu.sendzik.yume.service.calendar.model

import java.time.LocalDateTime

data class CalendarEntryDto(
    val uid: String,
    val title: String,
    val description: String? = null,
    val startTime: LocalDateTime,
    val endTime: LocalDateTime,
    val location: String? = null,
    val allDay: Boolean = false,
)
