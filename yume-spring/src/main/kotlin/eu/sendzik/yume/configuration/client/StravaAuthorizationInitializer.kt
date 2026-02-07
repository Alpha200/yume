package eu.sendzik.yume.configuration.client

import eu.sendzik.yume.repository.strava.StravaCredentialsRepository
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.http.HttpRequest
import org.springframework.http.client.ClientHttpRequestExecution
import org.springframework.http.client.ClientHttpRequestInterceptor
import org.springframework.http.client.ClientHttpResponse
import org.springframework.stereotype.Component

@Component
class StravaAuthorizationInterceptor(
    private val credentialsRepository: StravaCredentialsRepository,
    private val logger: KLogger,
) : ClientHttpRequestInterceptor {
    override fun intercept(request: HttpRequest, body: ByteArray, execution: ClientHttpRequestExecution): ClientHttpResponse {
        try {
            val credentials = credentialsRepository.findById("default").orElse(null)
            if (credentials != null && !credentials.isTokenExpired()) {
                request.headers.setBearerAuth(credentials.accessToken)
            } else {
                logger.warn { "No valid Strava credentials available for authorization" }
            }
        } catch (e: Exception) {
            logger.warn(e) { "Failed to add authorization header to Strava request" }
        }
        return execution.execute(request, body)
    }
}

