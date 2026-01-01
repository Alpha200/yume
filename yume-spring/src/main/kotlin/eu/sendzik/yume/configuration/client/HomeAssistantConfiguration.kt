package eu.sendzik.yume.configuration.client

import eu.sendzik.yume.client.HomeAssistantClient
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient

@Configuration
class HomeAssistantConfiguration {
    @Bean
    fun homeAssistantClient(
        restClientBuilder: RestClient.Builder,
        @Value("\${yume.home-assistant.api.url}")
        homeAssistantApiUrl: String,
        @Value("\${yume.home-assistant.api.token}")
        homeAssistantApiToken: String,
    ): HomeAssistantClient {
        val webClient = restClientBuilder
            .baseUrl(homeAssistantApiUrl)
            .defaultHeader("Authorization", "Bearer $homeAssistantApiToken")
            .build()

        val serviceProxyFactory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(webClient))
            .build()

        return serviceProxyFactory.createClient<HomeAssistantClient>()
    }
}