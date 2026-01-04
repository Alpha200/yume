package eu.sendzik.yume.tool.model

import java.time.LocalDateTime

data class Activity(
    val title: String,
    val description: String? = null,
    val startTime: LocalDateTime? = null,
    val endTime: LocalDateTime? = null,
    val source: String = "user_input",
    val confidence: String = "medium",
    val location: String? = null,
    val tags: List<String> = emptyList(),
    val metadata: Map<String, Any> = emptyMap(),
)

