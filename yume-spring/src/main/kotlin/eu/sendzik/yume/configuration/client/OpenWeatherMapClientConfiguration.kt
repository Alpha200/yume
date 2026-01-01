package eu.sendzik.yume.configuration.client

import eu.sendzik.yume.client.OpenWeatherMapClient
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient

@Configuration
class OpenWeatherMapClientConfiguration {
    @Bean
    fun openWeatherMapClient(
        restClientBuilder: RestClient.Builder,
    ): OpenWeatherMapClient {
        val webClient = restClientBuilder
            .baseUrl("https://api.openweathermap.org/data/3.0/")
            .build()

        val serviceProxyFactory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(webClient))
            .build()

        return serviceProxyFactory.createClient<OpenWeatherMapClient>()
    }
}