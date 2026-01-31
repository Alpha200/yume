package eu.sendzik.yume.configuration

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "yume.location.home")
class HomeLocationConfiguration {
    val latitude: Double = 0.0
    val longitude: Double = 0.0
}