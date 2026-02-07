package eu.sendzik.yume.component

import eu.sendzik.yume.service.strava.StravaWebhookService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.boot.context.event.ApplicationReadyEvent
import org.springframework.context.event.EventListener
import org.springframework.stereotype.Component

@Component
class StravaWebhookInitializer(
    private val stravaWebhookService: StravaWebhookService,
    private val logger: KLogger,
) {

    @EventListener(ApplicationReadyEvent::class)
    fun initializeWebhook() {
        logger.info { "Initializing Strava webhook on application startup" }
        stravaWebhookService.registerWebhook()
            .onSuccess {
                logger.info { "Strava webhook initialization completed successfully" }
            }
            .onFailure { e ->
                logger.warn(e) { "Strava webhook initialization failed, but application startup will continue" }
            }
    }
}
