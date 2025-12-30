package eu.sendzik.yume.service.calendar

import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class CalendarService(
    @Value("\${yume.calendar.url:}") private val calendarUrl: String,
    @Value("\${yume.calendar.username:}") private val username: String?,
    @Value("\${yume.calendar.password:}") private val password: String?,
) {
}