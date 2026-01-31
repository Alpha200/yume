package eu.sendzik.yume.configuration

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "yume.location.home")
class HomeLocationConfiguration(
    val latitude: Double,
    val longitude: Double
)
