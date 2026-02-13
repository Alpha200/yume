package eu.sendzik.yume.service.garminconnect

import com.fasterxml.jackson.databind.ObjectMapper
import eu.sendzik.yume.service.garminconnect.model.GarminHealthStatus
import io.ktor.client.HttpClient
import io.ktor.client.plugins.sse.SSE
import io.modelcontextprotocol.kotlin.sdk.Implementation
import io.modelcontextprotocol.kotlin.sdk.TextContent
import io.modelcontextprotocol.kotlin.sdk.client.Client
import io.modelcontextprotocol.kotlin.sdk.client.SseClientTransport
import kotlinx.coroutines.runBlocking
import org.springframework.beans.factory.annotation.Value
import org.springframework.cache.annotation.Cacheable
import org.springframework.stereotype.Service
import java.time.LocalDate

@Service
class GarminConnectDataFetcherService(
    @param:Value("\${yume.garmin-connect.mcp-server-url}")
    private val mcpServerUrl: String,
    private val jsonMapper: ObjectMapper,
) {

    @Cacheable("garmin_snapshot", sync = true)
    fun getSnapshot(): Result<GarminHealthStatus?> = runBlocking {
        runCatching {
            fetchSnapshotData()?.let { content ->
                @Suppress("UNCHECKED_CAST")
                val contentText: Map<String, Any> = jsonMapper.readValue(content, Map::class.java) as Map<String, Any>
                GarminHealthStatus.fromApi(contentText)
            }
        }
    }

    private suspend fun fetchSnapshotData(): String? {
        val httpClient = HttpClient { install(SSE) }
        val transport = SseClientTransport(httpClient, mcpServerUrl)
        val client = Client(clientInfo = Implementation("GarminConnectService", "1.0"))

        try {
            client.connect(transport)
            val today = LocalDate.now()
            val result = client.callTool("snapshot", mapOf(
                "from_date" to today.toString(),
                "to_date" to today.toString(),
            ))
            val textContent = result?.content?.firstOrNull() as? TextContent
            return textContent?.text
        } finally {
            client.close()
            httpClient.close()
        }
    }
}