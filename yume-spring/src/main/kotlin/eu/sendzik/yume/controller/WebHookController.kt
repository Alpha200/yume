package eu.sendzik.yume.controller

import eu.sendzik.yume.service.location.model.GeofenceEventRequest
import eu.sendzik.yume.service.router.RequestRouterService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("webhook")
class WebHookController(
    private val requestRouterService: RequestRouterService,
    private val logger: KLogger,
) {
    @PostMapping("geofence-event")
    fun handleGeofenceEvent(@RequestBody geofenceEvent: GeofenceEventRequest) {
        logger.info { "Received geofence event webhook: Geofence=${geofenceEvent.geofenceName} - Action=${geofenceEvent.eventType}" }
        requestRouterService.handleGeofenceEvent(geofenceEvent)
    }
}