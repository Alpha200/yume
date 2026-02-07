package eu.sendzik.yume.client

import eu.sendzik.yume.service.strava.model.StravaActivity
import eu.sendzik.yume.service.strava.model.StravaTokenResponse
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.service.annotation.GetExchange
import org.springframework.web.service.annotation.PostExchange

interface StravaClient {
    @PostExchange("/push/subscriptions")
    fun registerWebhookSubscription(
        @RequestParam("client_id") clientId: String,
        @RequestParam("client_secret") clientSecret: String,
        @RequestParam("callback_url") callbackUrl: String,
        @RequestParam("verify_token") verifyToken: String,
    ): Map<String, Any>?

    @PostExchange("/oauth/token")
    fun exchangeAuthorizationCode(
        @RequestParam("client_id") clientId: String,
        @RequestParam("client_secret") clientSecret: String,
        @RequestParam("code") code: String,
        @RequestParam("grant_type") grantType: String = "authorization_code",
    ): StravaTokenResponse

    @PostExchange("/oauth/token")
    fun refreshAccessToken(
        @RequestParam("client_id") clientId: String,
        @RequestParam("client_secret") clientSecret: String,
        @RequestParam("refresh_token") refreshToken: String,
        @RequestParam("grant_type") grantType: String = "refresh_token",
    ): StravaTokenResponse

    @GetExchange("/activities/{id}")
    fun getActivity(@PathVariable id: Long): StravaActivity

    @GetExchange("/athlete/activities")
    fun getAthleteActivities(
        @RequestParam("per_page") perPage: Int = 30,
        @RequestParam("page") page: Int = 1,
    ): List<StravaActivity>
}

