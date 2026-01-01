package eu.sendzik.yume.configuration

import eu.sendzik.yume.client.NominatimClient
import eu.sendzik.yume.client.OpenWeatherMapClient
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
            .build()

        val serviceProxyFactory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(webClient))
            .build()

        return serviceProxyFactory.createClient<NominatimClient>()
    }
}