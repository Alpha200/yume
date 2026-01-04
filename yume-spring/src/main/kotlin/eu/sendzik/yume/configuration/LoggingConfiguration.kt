package eu.sendzik.yume.configuration

import io.github.oshai.kotlinlogging.KLogger
import io.github.oshai.kotlinlogging.slf4j.toKLogger
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.InjectionPoint
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.Scope

@Configuration
class LoggingConfiguration {
    @Bean
    @Scope("prototype")
    fun logger(injectionPoint: InjectionPoint): KLogger {
        return  LoggerFactory.getLogger(
            injectionPoint.methodParameter?.containingClass ?:injectionPoint.field?.declaringClass
        ).toKLogger()
    }
}