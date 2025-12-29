/*package eu.sendzik.yume.advisor

import eu.sendzik.yume.service.memory.MemoryManagerService
import eu.sendzik.yume.service.memory.model.MemoryType
import org.springframework.ai.chat.client.ChatClientRequest
import org.springframework.ai.chat.client.ChatClientResponse
import org.springframework.ai.chat.client.advisor.api.Advisor
import org.springframework.ai.chat.client.advisor.api.AdvisorChain
import org.springframework.ai.chat.client.advisor.api.BaseAdvisor

class MemoryAdvisor(
    private val memoryManagerService: MemoryManagerService,
    private val injectPreferences: Boolean,
    private val injectObservations: Boolean,
    private val injectReminders: Boolean,
) : BaseAdvisor {
    override fun before(
        request: ChatClientRequest,
        advisorChain: AdvisorChain
    ): ChatClientRequest {
        var systemMessage = request.prompt().getSystemMessage().text
        systemMessage += "\n\nThe following information is retrieved from the user's memories stored in the system:"

        if (injectPreferences) {
            val preferences = memoryManagerService.getMemoriesByMemoryType(MemoryType.PREFERENCE)

            systemMessage += "\n\nUser Preferences:\n"
            systemMessage += preferences.joinToString("\n\n") {
                if (it.place != null) {
                    "- ${it.content} (Place: ${it.place})"
                } else {
                    "- ${it.content}"
                }
            }
        }

        if (injectObservations) {
            val observations = memoryManagerService.getMemoriesByMemoryType(MemoryType.OBSERVATION)

            systemMessage += "\n\nUser Observations:\n"
            systemMessage += observations.joinToString("\n\n") {
                if (it.place != null) {
                    "- ${it.content} (Place: ${it.place})"
                } else {
                    "- ${it.content}"
                }
            }
        }

        if (injectReminders) {
            val reminders = memoryManagerService.getMemoriesByMemoryType(MemoryType.REMINDER)

            systemMessage += "\n\nReminders:\n"
            systemMessage += reminders.joinToString("\n\n") { reminder ->
                val formattedSchedule = formatReminderSchedule(reminder)
                "- ${reminder.content}\n$formattedSchedule"
            }
        }

        val processedRequest = request
            .mutate()
            .prompt(request.prompt().augmentSystemMessage(systemMessage))
            .build()

        return processedRequest
    }

    override fun after(response: ChatClientResponse, advisorChain: AdvisorChain): ChatClientResponse = response

    override fun getOrder(): Int = Advisor.DEFAULT_CHAT_MEMORY_PRECEDENCE_ORDER

    private fun formatReminderSchedule(reminder: Any): String {
        val ro = (reminder as? eu.sendzik.yume.repository.memory.model.ReminderEntry)?.reminderOptions
            ?: return "Schedule: Unknown format"

        val scheduleInfo = StringBuilder("Reminder Schedule:\n")

        when {
            ro.datetimeValue != null -> {
                scheduleInfo.append("  Type: One-time\n")
                scheduleInfo.append("  Scheduled for: ${ro.datetimeValue}\n")
            }
            ro.timeValue != null -> {
                scheduleInfo.append("  Type: Recurring\n")
                scheduleInfo.append("  Time: ${ro.timeValue}\n")
                if (ro.daysOfWeek?.isNotEmpty() == true) {
                    scheduleInfo.append("  Days: ${ro.daysOfWeek?.joinToString(", ")}\n")
                } else {
                    scheduleInfo.append("  Days: Daily\n")
                }
            }
            ro.location != null -> {
                scheduleInfo.append("  Type: Location-based\n")
                scheduleInfo.append("  Location: ${ro.location}\n")
                if (!ro.triggerType.isNullOrEmpty()) {
                    val triggerText = if (ro.triggerType == "enter") "enter" else "leave"
                    scheduleInfo.append("  Trigger: On $triggerText\n")
                }
            }
        }

        return scheduleInfo.toString()
    }
}
*/