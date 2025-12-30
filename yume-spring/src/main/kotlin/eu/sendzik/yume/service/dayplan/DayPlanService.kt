package eu.sendzik.yume.service.dayplan

import eu.sendzik.yume.repository.dayplanner.DayPlanRepository
import eu.sendzik.yume.repository.dayplanner.model.DayPlan
import eu.sendzik.yume.repository.dayplanner.model.DayPlanItem
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Service
import java.time.LocalDate
import java.time.LocalDateTime
import java.util.*

@Service
class DayPlanService(
    private val dayPlanRepository: DayPlanRepository,
    private val logger: KLogger,
) {
    /**
     * Retrieves and formats a day plan for a specific date
     * @param date The date to get the plan for
     * @return Formatted plan string or a message indicating no plan exists
     */
    fun getFormattedPlan(date: LocalDate): String {
        val plan = dayPlanRepository.findByDate(date)
            ?: return "No plan found for ${formatTimestampForLLM(date)}"

        if (plan.items.isEmpty()) {
            return "Day plan for $date is empty.\n"
        }

        val output = StringBuilder()
        output.append("Day Plan for ${formatTimestampForLLM(date)}:\n\n")

        // Sort items by start time
        val sortedItems = plan.items.sortedWith(compareBy { it.startTime ?: LocalDateTime.MAX })

        for (item in sortedItems) {
            var timeStr = ""
            if (item.startTime != null) {
                timeStr = formatTimestampForLLM(item.startTime, true)
                if (item.endTime != null) {
                    timeStr += " - ${formatTimestampForLLM(item.endTime, true)}"
                }
                timeStr = " ($timeStr)"
            }

            output.append("* ${item.title}$timeStr\n")
            if (item.description != null) {
                output.append("${item.description}\n")
            }
            if (item.location != null) {
                output.append("Location: ${item.location}\n")
            }
            output.append("[${item.source.name.lowercase()} | confidence: ${item.confidence.name.lowercase()}]\n")
        }

        return output.toString()
    }

    /**
     * Creates or updates a complete day plan with activities
     * @param date The date of the plan
     * @param items List of day plan items/activities
     * @param summary A brief natural language overview of the day
     * @return The ID of the created or updated plan
     */
    fun createOrUpdatePlan(
        date: LocalDate,
        items: List<DayPlanItem>,
        summary: String,
    ): String {
        return createOrUpdatePlan(date, items, summary, null, emptyMap())
    }

    /**
     * Creates or updates a complete day plan with activities and calendar event hashes
     * @param date The date of the plan
     * @param items List of day plan items/activities
     * @param summary A brief natural language overview of the day
     * @param planId Optional specific plan ID to use
     * @param calendarEventHashes Optional map of calendar event hashes for change detection
     * @return The ID of the created or updated plan
     */
    fun createOrUpdatePlan(
        date: LocalDate,
        items: List<DayPlanItem>,
        summary: String,
        planId: String? = null,
        calendarEventHashes: Map<String, String> = emptyMap(),
    ): String {
        val now = LocalDateTime.now()
        val existingPlan = dayPlanRepository.findByDate(date)

        val actualId = planId ?: existingPlan?.id ?: UUID.randomUUID().toString()
        val createdAt = existingPlan?.createdAt ?: now

        val plan = DayPlan(
            id = actualId,
            date = date,
            items = items,
            summary = summary,
            createdAt = createdAt,
            updatedAt = now,
            calendarEventHashes = calendarEventHashes.ifEmpty { existingPlan?.calendarEventHashes ?: emptyMap() },
        )

        val savedPlan = dayPlanRepository.save(plan)
        logger.info { "Saved day plan for $date" }
        return savedPlan.id
    }

    /**
     * Get the day plan for today
     * @return The day plan for today or null if none exists
     */
    fun getPlanForToday(): DayPlan? {
        return dayPlanRepository.findByDate(LocalDate.now())
    }

    /**
     * Get the day plan for a specific date
     * @param date The date to retrieve
     * @return The day plan or null if none exists
     */
    fun getPlanForDate(date: LocalDate): DayPlan? {
        return dayPlanRepository.findByDate(date)
    }

    /**
     * Add a single item to an existing plan or create a new plan
     * @param date The date to add the item to
     * @param item The item to add
     * @return The ID of the plan
     */
    fun addItemToPlan(date: LocalDate, item: DayPlanItem): String {
        val existingPlan = dayPlanRepository.findByDate(date)

        return if (existingPlan != null) {
            val updatedItems = existingPlan.items.toMutableList().apply { add(item) }
            val updatedPlan = existingPlan.copy(
                items = updatedItems,
                updatedAt = LocalDateTime.now(),
            )
            dayPlanRepository.save(updatedPlan)
            existingPlan.id
        } else {
            createOrUpdatePlan(date, listOf(item), "")
        }
    }

    /**
     * Remove a specific item from a day plan
     * @param date The date of the plan
     * @param itemId The ID of the item to remove
     * @return True if the item was removed, false otherwise
     */
    fun removeItemFromPlan(date: LocalDate, itemId: String): Boolean {
        val existingPlan = dayPlanRepository.findByDate(date) ?: return false

        val originalCount = existingPlan.items.size
        val updatedItems = existingPlan.items.filter { it.id != itemId }

        return if (updatedItems.size < originalCount) {
            val updatedPlan = existingPlan.copy(
                items = updatedItems,
                updatedAt = LocalDateTime.now(),
            )
            dayPlanRepository.save(updatedPlan)
            true
        } else {
            false
        }
    }

    /**
     * Update a specific item in a day plan
     * @param date The date of the plan
     * @param itemId The ID of the item to update
     * @param updatedItem The new item data
     * @return True if the item was updated, false otherwise
     */
    fun updateItemInPlan(date: LocalDate, itemId: String, updatedItem: DayPlanItem): Boolean {
        val existingPlan = dayPlanRepository.findByDate(date) ?: return false

        val itemFound = existingPlan.items.any { it.id == itemId }
        if (!itemFound) return false

        val updatedItems = existingPlan.items.map { item ->
            if (item.id == itemId) updatedItem else item
        }

        val plan = existingPlan.copy(
            items = updatedItems,
            updatedAt = LocalDateTime.now(),
        )
        dayPlanRepository.save(plan)
        return true
    }

    /**
     * Delete a day plan for a specific date
     * @param date The date of the plan to delete
     * @return True if a plan was deleted, false otherwise
     */
    fun deletePlan(date: LocalDate): Boolean {
        return try {
            val plan = dayPlanRepository.findByDate(date) ?: return false
            dayPlanRepository.deleteById(plan.id)
            true
        } catch (e: Exception) {
            logger.error(e) { "Error deleting day plan for $date" }
            false
        }
    }

    /**
     * Check if a plan has changed by comparing items and summary
     * @param existingPlan The existing plan or null
     * @param newItems The new items
     * @param newSummary The new summary
     * @return True if the plan has changed, false otherwise
     */
    fun planHasChanged(
        existingPlan: DayPlan?,
        newItems: List<DayPlanItem>,
        newSummary: String?,
    ): Boolean {
        if (existingPlan == null) {
            return newItems.isNotEmpty()
        }

        // Compare number of items
        if (existingPlan.items.size != newItems.size) {
            return true
        }

        // Compare summary
        if (existingPlan.summary != newSummary) {
            return true
        }

        // Compare item titles
        val existingTitles = existingPlan.items.map { it.title }.sorted()
        val newTitles = newItems.map { it.title }.sorted()
        if (existingTitles != newTitles) {
            return true
        }

        // Compare start times
        val existingTimes = existingPlan.items.map { it.startTime?.toString() ?: "" }.sorted()
        val newTimes = newItems.map { it.startTime?.toString() ?: "" }.sorted()
        if (existingTimes != newTimes) {
            return true
        }

        return false
    }

    // Added read helpers for controller use
    fun getAllPlans(): List<DayPlan> {
        return dayPlanRepository.findAll()
    }
}