package eu.sendzik.yume.service.interaction

import dev.langchain4j.data.message.AiMessage
import dev.langchain4j.data.message.SystemMessage
import dev.langchain4j.data.message.ToolExecutionResultMessage
import dev.langchain4j.data.message.UserMessage
import dev.langchain4j.model.chat.listener.ChatModelErrorContext
import dev.langchain4j.model.chat.listener.ChatModelListener
import dev.langchain4j.model.chat.listener.ChatModelResponseContext
import dev.langchain4j.model.output.FinishReason
import eu.sendzik.yume.service.interaction.model.AiInteraction
import eu.sendzik.yume.service.interaction.model.AiInteractionMessage
import eu.sendzik.yume.service.interaction.model.MessageRole
import eu.sendzik.yume.service.interaction.model.ToolCall
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Service
import java.time.Instant

@Service
class InteractionTrackerService(
    private val logger: KLogger,
): ChatModelListener {
    private val aiInteractions = ArrayDeque<AiInteraction>()

    override fun onResponse(responseContext: ChatModelResponseContext) {
        if (responseContext.chatResponse().finishReason() != FinishReason.STOP) return

        val toolCalls: MutableMap<String, ToolCall> = mutableMapOf()
        val messages: MutableList<AiInteractionMessage> = mutableListOf()

        for (message in responseContext.chatRequest().messages()) {
            when (message) {
                is UserMessage -> messages.add(
                    AiInteractionMessage(
                        MessageRole.USER,
                        message.contents().joinToString("\n")
                    )
                )
                is SystemMessage -> messages.add(
                    AiInteractionMessage(
                        MessageRole.SYSTEM,
                        message.text()
                    )
                )
                is AiMessage -> {
                    if (message.hasToolExecutionRequests()) {
                        for (toolRequest in message.toolExecutionRequests()) {
                            val toolCall = ToolCall(
                                toolRequest.name(),
                                toolRequest.arguments(),
                                "" // Will be filled from ToolExecutionResultMessage
                            )
                            toolCalls[toolRequest.id()] = toolCall
                            messages.add(
                                AiInteractionMessage(
                                    MessageRole.TOOL_CALL,
                                    message.text(),
                                    toolCall,
                                )
                            )
                        }
                    }
                }
                is ToolExecutionResultMessage -> {
                    toolCalls[message.id()]?.response = message.text()
                }
            }
        }

        val aiInteraction = AiInteraction(
            timestamp = Instant.now(),
            messages = messages,
            response = responseContext.chatResponse().aiMessage().text(),
        )

        logger.debug { "Tracked AI Interaction: $aiInteraction" }

        synchronized(aiInteractions) {
            aiInteractions.addLast(aiInteraction)

            // Only keep the last 15 interactions
            if (aiInteractions.size > 15) {
                aiInteractions.removeFirst()
            }
        }
    }

    fun getAllInteractions(): List<AiInteraction> = synchronized(aiInteractions) {
        aiInteractions.toList()
    }

    override fun onError(errorContext: ChatModelErrorContext) {
        logger.error { "Chat model execution failed: ${errorContext.error().message}" }
        // TODO: Also track failed interactions
    }
}