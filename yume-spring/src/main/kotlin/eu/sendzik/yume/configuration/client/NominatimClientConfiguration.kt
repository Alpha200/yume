package eu.sendzik.yume.configuration.client

import eu.sendzik.yume.client.NominatimClient
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient

@Configuration
class NominatimClientConfiguration {
    @Bean
    fun nominatimClient(
        restClientBuilder: RestClient.Builder,
    ): NominatimClient {
        val webClient = restClientBuilder
            .baseUrl("https://nominatim.openstreetmap.org/")
            .defaultHeader("User-Agent", "yume/1.0 (https://github.com/alpha200/yume)")
            .build()

        val serviceProxyFactory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(webClient))
            .build()

        return serviceProxyFactory.createClient<NominatimClient>()
    }
}