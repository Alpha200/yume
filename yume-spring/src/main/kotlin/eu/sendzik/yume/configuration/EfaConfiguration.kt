package eu.sendzik.yume.configuration

import eu.sendzik.yume.client.EfaClient
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient

@Configuration
class EfaConfiguration(
    @Value("\${yume.efa.api-url:https://efa.vrr.de/standard}")
    private val efaApiUrl: String,
    @Value("\${yume.efa.client-id:CLIENTID}")
    @Suppress("UNUSED")
    private val efaClientId: String,
    @Value("\${yume.efa.client-name:yume}")
    @Suppress("UNUSED")
    private val efaClientName: String,
) {

    @Bean("efaRestClient")
    fun efaRestClient(): RestClient {
        return RestClient.builder()
            .baseUrl(efaApiUrl)
            .defaultHeader("Content-Type", "application/json")
            .build()
    }

    @Bean
    fun efaClient(efaRestClient: RestClient): EfaClient {
        val adapter = RestClientAdapter.create(efaRestClient)
        val factory = HttpServiceProxyFactory.builderFor(adapter).build()
        return factory.createClient<EfaClient>()
    }
}

