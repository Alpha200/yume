package eu.sendzik.yume.configuration

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "yume.matrix")
class MatrixConfiguration(
    val room: String,
    val homeserverUrl: String,
    val userId: String,
    val password: String,
)