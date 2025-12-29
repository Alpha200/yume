package eu.sendzik.yume.configuration

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties("yume.scheduler")
class SchedulerConfiguration(
    val delaySeconds: Long,
    val minTemporalDistanceMinutes: Long
)

