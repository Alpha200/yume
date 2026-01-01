package eu.sendzik.yume.controller

import eu.sendzik.yume.repository.memory.model.MemoryEntry
import eu.sendzik.yume.service.memory.MemoryManagerService
import eu.sendzik.yume.service.memory.model.MemoryType
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.DeleteMapping
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("memories")
class MemoryController(
    private val memoryManagerService: MemoryManagerService,
) {
    @GetMapping
    fun getAllMemories(): List<MemoryEntry> = memoryManagerService.getAllMemories()

    @GetMapping("/{id}")
    fun getMemoryById(@PathVariable id: String): ResponseEntity<MemoryEntry> {
        val memory = memoryManagerService.getMemoryById(id)
        return if (memory != null) ResponseEntity.ok(memory) else ResponseEntity.notFound().build()
    }

    @GetMapping("/type/{type}")
    fun getMemoriesByType(@PathVariable type: String): ResponseEntity<List<MemoryEntry>> {
        val memoryType = try {
            MemoryType.valueOf(type.uppercase())
        } catch (_: IllegalArgumentException) {
            return ResponseEntity.badRequest().build()
        }

        val memories = memoryManagerService.getMemoriesByType(memoryType)
        return ResponseEntity.ok(memories)
    }

    @DeleteMapping("/{id}")
    fun deleteMemory(@PathVariable id: String): ResponseEntity<Void> {
        return if (memoryManagerService.deleteMemory(id)) ResponseEntity.noContent().build() else ResponseEntity.notFound().build()
    }

    @PostMapping("reset-rag")
    //@PreAuthorize("hasRole('Administrator')")
    fun resetRag() {
        memoryManagerService.resetRagDatabase()
    }
}