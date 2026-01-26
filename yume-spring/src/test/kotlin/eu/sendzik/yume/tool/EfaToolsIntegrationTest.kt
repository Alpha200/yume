package eu.sendzik.yume.tool

import eu.sendzik.yume.client.EfaClient
import eu.sendzik.yume.service.efa.EfaService
import io.github.oshai.kotlinlogging.KotlinLogging
import io.mockk.junit5.MockKExtension
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient

@ExtendWith(MockKExtension::class)
class EfaToolsIntegrationTest {
    private lateinit var efaService: EfaService
    private lateinit var efaTools: EfaTools

    @BeforeEach
    fun setUp() {
        val efaClient = buildEfaClient()

        efaService = EfaService(
            efaClient,
            "yume",
            "yume",
            KotlinLogging.logger("EfaService")
        )

        efaTools = EfaTools(
            efaService,
            KotlinLogging.logger("EfaTools")
        )
    }

    @Test
    fun `test get station departures`() {
        val departures = efaTools.getStationDepartures("Stadtkrone Ost", 5, "", "Westerfilde")

        assertNotNull(departures)
        assertTrue(departures.isNotEmpty())

        println(departures)
    }

    private fun buildEfaClient(): EfaClient {
        val restClient = RestClient.builder()
            .baseUrl("https://efa.vrr.de/standard")
            .build()

        val adapter = RestClientAdapter.create(restClient)
        val factory = HttpServiceProxyFactory.builderFor(adapter).build()
        return factory.createClient<EfaClient>()
    }
}