package eu.sendzik.yume.controller

import eu.sendzik.yume.service.interaction.InteractionTrackerService
import eu.sendzik.yume.service.interaction.model.AiInteraction
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import java.util.UUID


@RestController
@RequestMapping("interactions")
class InteractionController(
    private val interactionTrackerService: InteractionTrackerService,
) {
    @GetMapping
    fun getAll(): List<AiInteraction> = interactionTrackerService.getAllInteractions()

    @GetMapping("{id}")
    fun getById(@PathVariable id: UUID): ResponseEntity<AiInteraction> {
        val aiInteraction = interactionTrackerService.getAllInteractions().find { it.id == id }
        return if (aiInteraction == null) {
            ResponseEntity.notFound().build()
        } else {
            ResponseEntity.ok(aiInteraction)
        }
    }
}