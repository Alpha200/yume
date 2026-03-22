package eu.sendzik.yume.controller

import eu.sendzik.yume.service.eink.EInkDisplayService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("e-ink-display")
class EInkDisplayController(
    private val eInkDisplayService: EInkDisplayService,
) {
    @GetMapping("content", produces = ["text/plain"])
    fun getEInkDisplayContent(): String {
        return eInkDisplayService.getEInkDisplayContent()
    }
}