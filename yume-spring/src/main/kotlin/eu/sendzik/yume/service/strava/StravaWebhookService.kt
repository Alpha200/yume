package eu.sendzik.yume.service.strava

import eu.sendzik.yume.client.StravaClient
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class StravaWebhookService(
    private val stravaClient: StravaClient,
    private val stravaActivityService: StravaActivityService,
    private val requestRouterService: eu.sendzik.yume.service.router.RequestRouterService,
    private val logger: KLogger,
    @Value("\${yume.strava.webhook-verify-token:}")
    private val webhookVerifyToken: String,
    @Value("\${yume.strava.enabled:false}")
    private val enabled: Boolean,
    @Value("\${yume.strava.client-id:}")
    private val clientId: String,
    @Value("\${yume.strava.client-secret:}")
    private val clientSecret: String,
    @Value("\${yume.strava.webhook-url:}")
    private val webhookUrl: String,
) {
    fun registerWebhook(): Result<Unit> {
        if (!enabled) {
            logger.debug { "Strava webhook is not enabled, skipping registration" }
            return Result.success(Unit)
        }

        if (clientId.isBlank() || clientSecret.isBlank()) {
            logger.warn { "Strava client_id or client_secret is not configured" }
            return Result.failure(IllegalStateException("Client ID and secret are required"))
        }

        if (webhookUrl.isBlank()) {
            logger.warn { "Strava webhook URL is not configured" }
            return Result.failure(IllegalStateException("Webhook URL is required"))
        }

        return runCatching {
            logger.info { "Registering Strava webhook with callback URL: $webhookUrl" }
            stravaClient.registerWebhookSubscription(
                clientId = clientId,
                clientSecret = clientSecret,
                callbackUrl = webhookUrl,
                verifyToken = webhookVerifyToken
            )
            logger.info { "Strava webhook registered successfully" }
        }.onFailure { e ->
            logger.error(e) { "Failed to register Strava webhook: ${e.message}" }
        }
    }

    fun handleSubscriptionChallenge(
        mode: String,
        challenge: String,
        verifyToken: String,
    ): Result<String> {
        if (!enabled) {
            logger.warn { "Strava webhook is not enabled" }
            return Result.failure(IllegalStateException("Strava webhook is disabled"))
        }

        if (mode != "subscribe") {
            logger.warn { "Invalid subscription mode: $mode" }
            return Result.failure(IllegalArgumentException("Invalid mode: $mode"))
        }

        if (verifyToken != webhookVerifyToken) {
            logger.warn { "Invalid verify token provided" }
            return Result.failure(SecurityException("Invalid verify token"))
        }

        logger.info { "Strava subscription challenge verified successfully" }
        return Result.success(challenge)
    }

    fun handleStravaEvent(event: Map<String, Any>) {
        if (!enabled) {
            logger.debug { "Strava webhook is not enabled, ignoring event" }
            return
        }

        runCatching {
            val objectType = event["object_type"] as? String
            val objectId = event["object_id"] as? Number
            val aspect = event["aspect_type"] as? String

            logger.info { "Processing Strava event: objectType=$objectType, objectId=$objectId, aspect=$aspect" }

            when (objectType) {
                "activity" -> handleActivityEvent(objectId, aspect, event)
                "athlete" -> handleAthleteEvent(aspect, event)
                else -> logger.warn { "Unknown Strava object type: $objectType" }
            }
        }.onFailure { e ->
            logger.error(e) { "Error processing Strava webhook event: ${e.message}" }
        }
    }

    private fun handleActivityEvent(objectId: Number?, aspect: String?, event: Map<String, Any>) {
        logger.debug { "Handling activity event: objectId=$objectId, aspect=$aspect" }
        
        if (objectId == null) {
            logger.warn { "Activity event missing object_id" }
            return
        }

        // Only process "created" activities (not "updated")
        if (aspect == "created") {
            stravaActivityService.fetchActivityIfCycling(objectId.toLong())
                .onSuccess { activity ->
                    if (activity != null) {
                        logger.info { "Successfully fetched cycling activity: ${activity.name}" }
                        // Format and send to router service for processing
                        val activityDetails = stravaActivityService.formatActivityDetails(activity)
                        requestRouterService.handleSportsActivity(activityDetails)
                    }
                }
                .onFailure { error ->
                    logger.error(error) { "Failed to fetch cycling activity $objectId" }
                }
        } else {
            logger.debug { "Ignoring non-created activity event: aspect=$aspect" }
        }
    }

    private fun handleAthleteEvent(aspect: String?, event: Map<String, Any>) {
        logger.debug { "Handling athlete event: aspect=$aspect" }
        // TODO: Implement athlete event handling
        // This could include profile updates, etc.
    }
}
