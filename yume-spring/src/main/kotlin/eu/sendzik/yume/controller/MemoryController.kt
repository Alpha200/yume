package eu.sendzik.yume.controller

import eu.sendzik.yume.service.memory.MemoryManagerService
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("memory")
class MemoryController(
    private val memoryManagerService: MemoryManagerService,
) {
    @PostMapping("reset-rag")
    //@PreAuthorize("hasRole('Administrator')")
    fun resetRag() {
        memoryManagerService.resetRagDatabase()
    }
}