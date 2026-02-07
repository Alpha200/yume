package eu.sendzik.yume.service.matrix.model

import java.time.LocalDateTime

data class UserMessageEvent(
    val timestamp: LocalDateTime,
    val message: String,
    val eventId: String,
)