package eu.sendzik.yume.configuration

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
    fun kitchenOwlRestClient(): RestClient {
        val builder = RestClient.builder()
            .baseUrl(kitchenOwlApiUrl)
            .defaultHeader("Content-Type", "application/json")

        if (kitchenOwlApiKey.isNotBlank()) {
            builder.defaultHeader("Authorization", "Bearer $kitchenOwlApiKey")
        }

        return builder.build()
    }

    @Bean
    fun kitchenOwlClient(kitchenOwlRestClient: RestClient): KitchenOwlClient {
        val adapter = RestClientAdapter.create(kitchenOwlRestClient)
        val factory = HttpServiceProxyFactory.builderFor(adapter).build()
        return factory.createClient<KitchenOwlClient>()
    }
}

