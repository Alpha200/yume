package eu.sendzik.yume.component

import io.github.oshai.kotlinlogging.KLogger
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpRequest
import org.springframework.http.client.ClientHttpRequestExecution
import org.springframework.http.client.ClientHttpRequestInterceptor
import org.springframework.http.client.ClientHttpResponse
import org.springframework.stereotype.Component
import java.io.IOException
import java.nio.charset.StandardCharsets

@Component
class ClientLoggerRequestInterceptor(
    private val logger: KLogger,
) : ClientHttpRequestInterceptor {
    override fun intercept(
        request: HttpRequest, body: ByteArray,
        execution: ClientHttpRequestExecution
    ): ClientHttpResponse {
        logRequest(request, body)
        val response = execution.execute(request, body)
        return logResponse(response)
    }

    private fun logRequest(request: HttpRequest, body: ByteArray?) {
        logger.info { "Request: ${request.method} ${request.uri}" }
        logHeaders(request.headers)

        if (body != null && body.isNotEmpty()) {
            logger.debug {"Request body: ${String(body, StandardCharsets.UTF_8)}" }
        }
    }

    @Throws(IOException::class)
    private fun logResponse(
        response: ClientHttpResponse
    ): ClientHttpResponse {
        logger.debug {"Response status: ${response.statusCode}" }
        logHeaders(response.headers)
        return response
    }

    private fun logHeaders(headers: HttpHeaders) {
        headers.forEach { (key, value) -> logger.debug { "Header: $key = $value" } }
    }
}