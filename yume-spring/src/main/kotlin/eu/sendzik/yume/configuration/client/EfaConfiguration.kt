package eu.sendzik.yume.configuration.client

import eu.sendzik.yume.client.EfaClient
import eu.sendzik.yume.component.ClientLoggerRequestInterceptor
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient

@Configuration
class EfaConfiguration(
    @Value("\${yume.efa.api-url}")
    private val efaApiUrl: String,
) {
    @Bean
    fun efaClient(
        restClientBuilder: RestClient.Builder,
        clientLoggerRequestInterceptor: ClientLoggerRequestInterceptor,
    ): EfaClient {
        val restClient = restClientBuilder
            .baseUrl(efaApiUrl)
            .requestInterceptor(clientLoggerRequestInterceptor)
            .build()

        val adapter = RestClientAdapter.create(restClient)
        val factory = HttpServiceProxyFactory.builderFor(adapter).build()
        return factory.createClient<EfaClient>()
    }
}