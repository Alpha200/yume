package eu.sendzik.yume.configuration

import eu.sendzik.yume.converter.SchedulerRunStatusReadConverter
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.data.mongodb.core.convert.MongoCustomConversions

@Configuration
class MongoConfiguration {

    @Bean
    fun mongoCustomConversions(): MongoCustomConversions {
        return MongoCustomConversions(
            listOf(
                SchedulerRunStatusReadConverter()
            )
        )
    }
}

