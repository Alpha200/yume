package eu.sendzik.yume.configuration.client

import eu.sendzik.yume.client.KitchenOwlClient
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient

@Configuration
class KitchenOwlConfiguration(
    @Value("\${yume.kitchenowl.api-url:http://localhost:8080/api}")
    private val kitchenOwlApiUrl: String,
    @Value("\${yume.kitchenowl.api-key:}")
    private val kitchenOwlApiKey: String,
) {
    @Bean
    fun kitchenOwlClient(
        restClientBuilder: RestClient.Builder,
    ): KitchenOwlClient {
        val restClient = restClientBuilder
            .baseUrl(kitchenOwlApiUrl)
            .let {
                if (kitchenOwlApiKey.isNotBlank()) {
                    it.defaultHeader("Authorization", "Bearer $kitchenOwlApiKey")
                } else {
                    it
                }
            }.build()

        val adapter = RestClientAdapter.create(restClient)
        val factory = HttpServiceProxyFactory.builderFor(adapter).build()
        return factory.createClient<KitchenOwlClient>()
    }
}