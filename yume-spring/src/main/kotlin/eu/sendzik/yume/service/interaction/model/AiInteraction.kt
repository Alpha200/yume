package eu.sendzik.yume.service.interaction.model

import java.time.Instant
import java.util.UUID

data class AiInteraction(
    val id: UUID = UUID.randomUUID(),
    val timestamp: Instant,
    val messages: List<AiInteractionMessage>,
    val response: String = ""
)

data class ToolCall(
    val name: String,
    val arguments: String,
    var response: String
)

data class AiInteractionMessage(
    val role: MessageRole,
    val text: String,
    val toolCall: ToolCall? = null
)

enum class MessageRole {
    USER,
    TOOL_CALL,
    SYSTEM
}