package eu.sendzik.yume.service.matrix.model

import java.time.LocalDateTime

data class UserReactionEvent(
    val timestamp: LocalDateTime,
    val reaction: String,
    val relatedMessage: String,
    val relatedEventId: String,
)
