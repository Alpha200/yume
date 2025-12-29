package eu.sendzik.yume

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.ConfigurationPropertiesScan
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.boot.runApplication
import org.springframework.scheduling.annotation.EnableAsync
import org.springframework.scheduling.annotation.EnableScheduling

@ConfigurationPropertiesScan
@SpringBootApplication
@EnableScheduling
@EnableAsync
class YumeApplication

fun main(args: Array<String>) {
	runApplication<YumeApplication>(*args)
}
