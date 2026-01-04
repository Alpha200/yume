package eu.sendzik.yume.service.calendar

import com.github.caldav4j.CalDAVConstants
import com.github.caldav4j.methods.HttpCalDAVReportMethod
import com.github.caldav4j.model.request.CalendarData
import com.github.caldav4j.model.request.CalendarQuery
import com.github.caldav4j.model.request.CompFilter
import com.github.caldav4j.model.request.TimeRange
import com.github.caldav4j.model.response.CalendarDataProperty
import eu.sendzik.yume.service.calendar.model.CalendarEntry
import io.github.oshai.kotlinlogging.KLogger
import net.fortuna.ical4j.model.Calendar
import net.fortuna.ical4j.model.Component
import net.fortuna.ical4j.model.DateTime
import net.fortuna.ical4j.model.component.VEvent
import org.apache.http.auth.AuthScope
import org.apache.http.auth.UsernamePasswordCredentials
import org.apache.http.impl.client.BasicCredentialsProvider
import org.apache.http.impl.client.HttpClients
import org.apache.jackrabbit.webdav.property.DavPropertyName
import org.apache.jackrabbit.webdav.property.DavPropertyNameSet
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.time.ZoneId
import java.util.*
import jakarta.servlet.http.HttpServletResponse

/**
 * Service for fetching calendar entries from a CalDAV server (e.g., Nextcloud).
 *
 * For Nextcloud, the calendar URL should be in the format:
 * https://cloud.example.com/remote.php/dav/calendars/USERNAME/CALENDARID/
 *
 * You can find your calendar IDs in your Nextcloud calendar settings.
 * The most common calendar is "personal".
 */
@Service
class CalendarService(
    @Value("\${yume.calendar.url}") private val calendarUrl: String,
    @Value("\${yume.calendar.username}") private val username: String?,
    @Value("\${yume.calendar.password}") private val password: String?,
    private val logger: KLogger,
) {

    fun getFormattedCalendarEntries(startDate: LocalDateTime, endDate: LocalDateTime): String {
        val calendarEntries = getCalendarEntries(startDate, endDate)

        if (calendarEntries.isEmpty()) {
            return "No calendar entries"
        }

        return calendarEntries.joinToString("\n") { it.formatForLLM() }
    }

    fun getCalendarEntries(startDate: LocalDateTime, endDate: LocalDateTime): List<CalendarEntry> {
        return try {
            logger.debug { "Fetching calendar entries from: $calendarUrl for range $startDate to $endDate" }

            // Create a set of DAV properties to query
            val properties = DavPropertyNameSet().apply {
                add(DavPropertyName.GETETAG)
            }

            // Create component filters for VCALENDAR and VEVENT with TimeRange
            val vcalendar = CompFilter(Calendar.VCALENDAR)
            val vevent = CompFilter(Component.VEVENT)

            // Add server-side date range filtering to only fetch events in the specified range
            // This significantly reduces bandwidth and processing on the client side
            val startDateIcal4j = DateTime(Date.from(startDate.atZone(ZoneId.systemDefault()).toInstant()))
            val endDateIcal4j = DateTime(Date.from(endDate.atZone(ZoneId.systemDefault()).toInstant()))
            val timeRange = TimeRange(startDateIcal4j, endDateIcal4j)
            vevent.timeRange = timeRange

            vcalendar.addCompFilter(vevent)

            // Create the calendar query with date range filtering
            val query = CalendarQuery(properties, vcalendar, CalendarData(), false, false)

            // Create HTTP method with the query
            val method = HttpCalDAVReportMethod(calendarUrl, query, CalDAVConstants.DEPTH_1)

            logger.debug { "Sending CalDAV query with server-side date range filter" }

            // Create HTTP client with authentication if provided
            val httpClient = if (!username.isNullOrBlank() && !password.isNullOrBlank()) {
                logger.debug { "Using authentication for calendar request" }
                val credentialsProvider = BasicCredentialsProvider()
                credentialsProvider.setCredentials(
                    AuthScope.ANY,
                    UsernamePasswordCredentials(username, password)
                )
                HttpClients.custom()
                    .setDefaultCredentialsProvider(credentialsProvider)
                    .build()
            } else {
                HttpClients.createDefault()
            }

            httpClient.use { client ->
                val httpResponse = client.execute(method)

                logger.debug { "Calendar request response: ${httpResponse.statusLine}" }

                if (!method.succeeded(httpResponse)) {
                    logger.warn { "Failed to fetch calendar entries: ${httpResponse.statusLine}" }
                    // Try to read response body for more details
                    httpResponse.entity?.let { entity ->
                        try {
                            val content = entity.content.bufferedReader().use { it.readText() }
                            logger.debug { "Response body: $content" }
                        } catch (e: Exception) {
                            logger.debug { "Could not read response body: ${e.message}" }
                        }
                    }
                    return@use emptyList()
                }

                val multiStatusResponses = method.getResponseBodyAsMultiStatus(httpResponse)?.responses
                    ?: return@use emptyList()

                logger.debug { "Found ${multiStatusResponses.size} responses from server" }

                val entries = mutableListOf<CalendarEntry>()

                for (response in multiStatusResponses) {
                    if (response.status[0].statusCode != HttpServletResponse.SC_OK) {
                        logger.debug { "Skipping response with status: ${response.status[0].statusCode}" }
                        continue
                    }

                    try {
                        val calendar = CalendarDataProperty.getCalendarfromResponse(response)
                        if (calendar != null) {
                            // No client-side filtering needed since server already filtered by date range
                            val events = calendar.components.filterIsInstance<VEvent>()

                            logger.debug { "Found ${events.size} events from server (already filtered)" }

                            entries.addAll(events.mapNotNull { event ->
                                try {
                                    mapToCalendarEntryDto(event)
                                } catch (e: Exception) {
                                    logger.warn(e) { "Failed to map calendar event" }
                                    null
                                }
                            })
                        }
                    } catch (e: Exception) {
                        logger.warn(e) { "Failed to process calendar response" }
                    }
                }

                entries
            }
        } catch (e: Exception) {
            logger.error(e) { "Error fetching calendar entries" }
            emptyList()
        }
    }

    private fun convertToLocalDateTime(date: Any?): LocalDateTime? {
        if (date !is String) return null

        return try {
            when {
                // All-day format: YYYYMMDD
                date.length == 8 && date.all { it.isDigit() } -> {
                    val year = date.substring(0, 4).toInt()
                    val month = date.substring(4, 6).toInt()
                    val day = date.substring(6, 8).toInt()
                    LocalDateTime.of(year, month, day, 0, 0, 0)
                }
                // DateTime format: YYYYMMDDTHHMMSS or YYYYMMDDTHHMMSSZ
                date.length >= 15 && date[8] == 'T' -> {
                    val year = date.substring(0, 4).toInt()
                    val month = date.substring(4, 6).toInt()
                    val day = date.substring(6, 8).toInt()
                    val hour = date.substring(9, 11).toInt()
                    val minute = date.substring(11, 13).toInt()
                    val second = date.substring(13, 15).toInt()
                    LocalDateTime.of(year, month, day, hour, minute, second)
                }
                else -> {
                    logger.warn { "Unsupported date format: $date" }
                    null
                }
            }
        } catch (_: Exception) {
            logger.warn { "Could not parse date string: $date" }
            null
        }
    }

    private fun mapToCalendarEntryDto(event: VEvent): CalendarEntry? {
        val uid = event.uid?.value ?: UUID.randomUUID().toString()
        val title = event.summary?.value ?: "Untitled"
        val description = event.description?.value
        val location = event.location?.value

        val (startTime, endTime) = getEventTimes(event) ?: run {
            logger.warn { "Skipping event '$title' - could not parse dates" }
            return null
        }

        // An all-day event has a date string in YYYYMMDD format (8 digits, no T)
        val startDateValue = event.startDate?.value
        val allDay = startDateValue is String &&
                     startDateValue.length == 8 &&
                     startDateValue.all { it.isDigit() }

        return CalendarEntry(
            uid = uid,
            title = title,
            description = description,
            startTime = startTime,
            endTime = endTime,
            location = location,
            allDay = allDay
        )
    }

    private fun getEventTimes(event: VEvent): Pair<LocalDateTime, LocalDateTime>? {
        val startTime = convertToLocalDateTime(event.startDate?.value)
        val endTime = convertToLocalDateTime(event.endDate?.value)

        return if (startTime != null && endTime != null) {
            Pair(startTime, endTime)
        } else {
            null
        }
    }
}