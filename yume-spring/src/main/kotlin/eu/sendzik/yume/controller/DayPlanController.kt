package eu.sendzik.yume.controller

import eu.sendzik.yume.repository.dayplanner.model.DayPlan
import eu.sendzik.yume.service.dayplan.DayPlanService
import eu.sendzik.yume.service.interaction.InteractionTrackerService
import eu.sendzik.yume.service.interaction.model.AiInteraction
import org.springframework.format.annotation.DateTimeFormat
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import java.time.LocalDate
import java.util.UUID

@RestController
@RequestMapping("day-plan")
class DayPlanController(
    private val dayPlanService: DayPlanService
) {
    @GetMapping("/date/{date}")
    fun getPlanForDate(@PathVariable @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) date: LocalDate): ResponseEntity<DayPlan> {
        val plan = dayPlanService.getPlanForDate(date)
        return if (plan != null) ResponseEntity.ok(plan) else ResponseEntity.notFound().build()
    }
}