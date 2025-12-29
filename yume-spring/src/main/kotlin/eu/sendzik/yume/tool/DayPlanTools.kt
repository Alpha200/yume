package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.repository.dayplanner.model.DayPlanItem
import eu.sendzik.yume.service.dayplan.DayPlanService
import eu.sendzik.yume.tool.model.Activity
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.*

@Component
class DayPlanTools(
    private val dayPlanService: DayPlanService,
    private val logger: KLogger,
) {
    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE
    private val dateTimeFormatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME

    @Suppress("UNUSED")
    @Tool("Get the day plan for a specific date (YYYY-MM-DD) or today if not specified")
    fun getDayPlan(
        @P("Date in YYYY-MM-DD format. If not provided, uses today's date")
        date: String? = null
    ): String = runCatching {
        val planDate = parseDate(date) ?: return "Error: Invalid date format '$date'. Please use YYYY-MM-DD format."
        dayPlanService.getFormattedPlan(planDate)
    }.getOrElse {
        logger.error(it) { "Error retrieving day plan" }
        "Error retrieving day plan: ${it.message}"
    }

    @Suppress("UNUSED")
    @Tool("Create or update a day plan with activities for a specific date")
    fun updateDayPlan(
        @P("Date in YYYY-MM-DD format")
        date: String,
        @P("List of activities for the day")
        activities: List<Activity>,
        @P("Brief summary of the day (2-3 sentences)")
        summary: String,
    ): String = runCatching {
        val planDate = parseDate(date) ?: throw IllegalArgumentException("Invalid date format '$date'. Please use YYYY-MM-DD format.")

        if (activities.isEmpty()) {
            throw IllegalArgumentException("activities must contain at least one activity")
        }

        val items = activities.mapIndexed { idx, activity ->
            try {
                val source = try {
                    DayPlanItem.Source.valueOf(activity.source.uppercase())
                } catch (_: Exception) {
                    throw IllegalArgumentException("Invalid source '${activity.source}' in activity $idx. Must be one of: memory, calendar, user_input")
                }

                val confidence = try {
                    DayPlanItem.Confidence.valueOf(activity.confidence.uppercase())
                } catch (_: Exception) {
                    throw IllegalArgumentException("Invalid confidence '${activity.confidence}' in activity $idx. Must be one of: low, medium, high")
                }

                DayPlanItem(
                    id = UUID.randomUUID().toString(),
                    title = activity.title,
                    description = activity.description,
                    startTime = activity.startTime,
                    endTime = activity.endTime,
                    source = source,
                    confidence = confidence,
                    location = activity.location,
                    tags = activity.tags,
                    metadata = activity.metadata,
                )
            } catch (e: Exception) {
                throw IllegalArgumentException("Error processing activity at index $idx: ${e.message}")
            }
        }

        val planId = dayPlanService.createOrUpdatePlan(date = planDate, items = items, summary = summary)
        "Successfully updated day plan for $date with ${items.size} activities (plan ID: $planId)"
    }.getOrElse {
        logger.error(it) { "Error updating day plan" }
        "Error: ${it.message}"
    }

    private fun parseDate(date: String?): LocalDate? {
        if (date.isNullOrBlank()) return LocalDate.now()
        return try {
            LocalDate.parse(date, dateFormatter)
        } catch (_: Exception) {
            null
        }
    }

    private fun parseDateTime(dateTime: String?): LocalDateTime? {
        return dateTime?.let {
            try {
                LocalDateTime.parse(it, dateTimeFormatter)
            } catch (e: Exception) {
                throw IllegalArgumentException("Invalid datetime format: ${e.message}")
            }
        }
    }
}
