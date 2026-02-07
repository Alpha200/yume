package eu.sendzik.yume.configuration.client

import eu.sendzik.yume.client.StravaClient
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.http.client.JdkClientHttpRequestFactory
import org.springframework.web.client.RestClient
import org.springframework.web.client.support.RestClientAdapter
import org.springframework.web.service.invoker.HttpServiceProxyFactory
import org.springframework.web.service.invoker.createClient
import java.time.Duration

@Configuration
class StravaClientConfiguration {
    @Bean
    fun stravaClient(
        restClientBuilder: RestClient.Builder,
        stravaAuthorizationInterceptor: StravaAuthorizationInterceptor,
        @Value("\${yume.strava.api-base-url:https://www.strava.com/api/v3}")
        apiBaseUrl: String,
    ): StravaClient {
        val requestFactory = JdkClientHttpRequestFactory()
        requestFactory.setReadTimeout(Duration.ofSeconds(30))

        val client = restClientBuilder
            .baseUrl(apiBaseUrl)
            .requestFactory(requestFactory)
            .requestInterceptor(stravaAuthorizationInterceptor)
            .build()

        val serviceProxyFactory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(client))
            .build()

        return serviceProxyFactory.createClient<StravaClient>()
    }
}


