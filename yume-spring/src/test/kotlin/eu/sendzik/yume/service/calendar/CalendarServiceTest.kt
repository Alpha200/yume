package eu.sendzik.yume.service.calendar

import io.github.oshai.kotlinlogging.KotlinLogging
import io.mockk.junit5.MockKExtension
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Disabled
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import java.time.LocalDate

@Disabled
@ExtendWith(MockKExtension::class)
class CalendarServiceTest {
    lateinit var service: CalendarService

    @BeforeEach
    fun setUp() {
        // For Nextcloud, use the format: https://cloud.example.com/remote.php/dav/calendars/USERNAME/CALENDARID/
        // The calendar ID can be found in Nextcloud calendar settings
        service = CalendarService(
            calendarUrl = "https://localhost/remote.php/dav/calendars/username/personal/",
            username = "username",
            password = "password",
            logger = KotlinLogging.logger("CalendarServiceTest") ,
        )
    }

    @Test
    fun `test get calendar entries`() {
        val entries = service.getCalendarEntries(
            startDate =  LocalDate.now().atStartOfDay(),
            endDate = LocalDate.now().plusDays(2).atStartOfDay()
        )

        assertThat(entries).isNotEmpty
    }
}