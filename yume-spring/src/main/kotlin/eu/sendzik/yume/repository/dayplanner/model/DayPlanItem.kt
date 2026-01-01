package eu.sendzik.yume.repository.dayplanner.model

import java.time.LocalDateTime

data class DayPlanItem(
    val id: String,
    val title: String,
    val description: String? = null,
    val startTime: LocalDateTime? = null,
    val endTime: LocalDateTime? = null,
    val source: Source,
    val confidence: Confidence,
    val location: String? = null,
    val tags: List<String> = emptyList(),
    val metadata: Map<String, Any> = emptyMap(),
) {
    enum class Source {
        MEMORY,
        CALENDAR,
        USER_INPUT,
        GUESS
    }

    enum class Confidence {
        LOW,
        MEDIUM,
        HIGH
    }
}

