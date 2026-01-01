package eu.sendzik.yume.agent

import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode

@AiService(
    chatModel = "conversationSummarizerModel",
    wiringMode = AiServiceWiringMode.EXPLICIT,
)
interface ConversationSummarizerAgent {
    @SystemMessage("Given the following conversation, provide a concise summary highlighting the key points discussed in two sentences. Only output these sentences and nothing else. Keep the summary in the same language. If there was a break in the conversation, focus on the most recent part relevant to the follow up user input.")
    @UserMessage("Chat history: {{conversation}}\n\nFollow up user input: {{userInput}}")
    fun summarizeConversation(
        @V("conversation") conversation: String,
        @V("userInput") userInput: String
    ): String
}