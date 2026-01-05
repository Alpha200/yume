package eu.sendzik.yume.configuration

import eu.sendzik.yume.repository.scheduler.model.SchedulerRunStatus
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.core.convert.converter.Converter
import org.springframework.data.mongodb.core.convert.MongoCustomConversions

@Configuration
class MongoConfiguration {

    @Bean
    fun mongoCustomConversions(): MongoCustomConversions {
        return MongoCustomConversions(
            listOf(
                StringToSchedulerRunStatusConverter()
            )
        )
    }

    class StringToSchedulerRunStatusConverter : Converter<String, SchedulerRunStatus> {
        override fun convert(source: String): SchedulerRunStatus? {
            return SchedulerRunStatus.fromValue(source)
        }
    }
}

