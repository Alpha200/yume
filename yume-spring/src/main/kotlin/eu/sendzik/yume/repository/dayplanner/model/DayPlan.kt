package eu.sendzik.yume.repository.dayplanner.model

import org.springframework.data.annotation.Id
import org.springframework.data.annotation.TypeAlias
import org.springframework.data.mongodb.core.mapping.Document
import java.time.LocalDate
import java.time.LocalDateTime

@TypeAlias("DayPlan")
@Document(collection = "day_plans")
data class DayPlan(
    @field:Id val id: String,
    val date: LocalDate,
    val items: List<DayPlanItem> = emptyList(),
    val createdAt: LocalDateTime,
    val updatedAt: LocalDateTime,
    val summary: String? = null,
    val calendarEventHashes: Map<String, String> = emptyMap(),
)
