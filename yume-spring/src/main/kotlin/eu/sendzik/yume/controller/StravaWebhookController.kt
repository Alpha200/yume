package eu.sendzik.yume.controller

import eu.sendzik.yume.service.strava.StravaAuthService
import eu.sendzik.yume.service.strava.StravaWebhookService
import eu.sendzik.yume.service.strava.model.StravaConnectionStatus
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.http.HttpStatus
import org.springframework.http.ProblemDetail
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("strava")
class StravaWebhookController(
    private val stravaWebhookService: StravaWebhookService,
    private val stravaAuthService: StravaAuthService,
    private val logger: KLogger,
) {
    @GetMapping("webhook")
    fun handleSubscriptionChallenge(
        @RequestParam("hub.mode") mode: String,
        @RequestParam("hub.challenge") challenge: String,
        @RequestParam("hub.verify_token") verifyToken: String,
    ): ResponseEntity<Any> {
        logger.info { "Received Strava subscription challenge" }
        return stravaWebhookService.handleSubscriptionChallenge(mode, challenge, verifyToken)
            .fold(
                onSuccess = { ResponseEntity.ok(mapOf("hub.challenge" to it)) },
                onFailure = { 
                    val problemDetail = ProblemDetail.forStatusAndDetail(
                        HttpStatus.UNAUTHORIZED,
                        it.message ?: "Subscription challenge verification failed"
                    )
                    ResponseEntity.of(problemDetail).build()
                }
            )
    }

    @PostMapping("webhook")
    fun handleStravaEvent(@RequestBody event: Map<String, Any>) {
        logger.info { "Received Strava webhook event: ${event["object_type"]}" }
        stravaWebhookService.handleStravaEvent(event)
    }

    @GetMapping("oauth/callback")
    fun handleOAuthCallback(
        @RequestParam("code") code: String,
    ): ResponseEntity<String> {
        logger.info { "Received Strava OAuth callback" }
        return stravaAuthService.exchangeAuthorizationCode(code)
            .fold(
                onSuccess = {
                    val message = "Successfully authenticated with Strava. Athlete: ${it.athleteName}"
                    logger.info { message }
                    // Redirect to preferences tab with success message
                    ResponseEntity.status(302)
                        .header("Location", "/?tab=preferences&strava=connected")
                        .body(null)
                },
                onFailure = {
                    logger.error(it) { "OAuth authentication failed" }
                    // Redirect back to preferences with error
                    ResponseEntity.status(302)
                        .header("Location", "/?tab=preferences&strava=error")
                        .body(null)
                }
            )
    }

    @GetMapping("status")
    fun getConnectionStatus(): ResponseEntity<StravaConnectionStatus> {
        val result: Result<StravaConnectionStatus> = stravaAuthService.getConnectionStatus()
        return result.fold(
            onSuccess = { ResponseEntity.ok(it) as ResponseEntity<StravaConnectionStatus> },
            onFailure = { ResponseEntity.ok(StravaConnectionStatus(connected = false)) as ResponseEntity<StravaConnectionStatus> }
        )
    }

    @PostMapping("disconnect")
    fun disconnectStrava(): ResponseEntity<Map<String, String>> {
        val result: Result<Unit> = stravaAuthService.disconnect()
        return result.fold(
            onSuccess = { ResponseEntity.ok(mapOf("status" to "disconnected")) as ResponseEntity<Map<String, String>> },
            onFailure = {
                val problemDetail = ProblemDetail.forStatusAndDetail(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    it.message ?: "Failed to disconnect Strava"
                )
                ResponseEntity.of(problemDetail).build()
            }
        )
    }

    @GetMapping("oauth/authorize-url")
    fun getAuthorizeUrl(): ResponseEntity<Map<String, String>> {
        return stravaAuthService.getAuthorizeUrl()
            .fold(
                onSuccess = { ResponseEntity.ok(mapOf("url" to it)) },
                onFailure = {
                    val problemDetail = ProblemDetail.forStatusAndDetail(
                        HttpStatus.BAD_REQUEST,
                        it.message ?: "Failed to generate authorization URL"
                    )
                    ResponseEntity.of(problemDetail).build()
                }
            )
    }
}

