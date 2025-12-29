/*package eu.sendzik.yume.advisor

import org.springframework.ai.chat.client.ChatClientRequest
import org.springframework.ai.chat.client.ChatClientResponse
import org.springframework.ai.chat.client.advisor.api.Advisor
import org.springframework.ai.chat.client.advisor.api.AdvisorChain
import org.springframework.ai.chat.client.advisor.api.BaseAdvisor
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class DateTimeAdvisor : BaseAdvisor {
    private val dateTimeFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

    override fun before(
        request: ChatClientRequest,
        advisorChain: AdvisorChain
    ): ChatClientRequest {
        val currentDateTime = LocalDateTime.now().format(dateTimeFormatter)
        var systemMessage = request.prompt().getSystemMessage().text
        systemMessage += "\n\nCurrent date and time: $currentDateTime\n\n"

        val processedRequest = request
            .mutate()
            .prompt(request.prompt().augmentSystemMessage(systemMessage))
            .build()

        return processedRequest
    }

    override fun after(response: ChatClientResponse, advisorChain: AdvisorChain): ChatClientResponse = response

    override fun getOrder(): Int = Advisor.DEFAULT_CHAT_MEMORY_PRECEDENCE_ORDER
}
*/
