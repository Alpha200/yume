package eu.sendzik.yume.configuration

import com.github.benmanes.caffeine.cache.Caffeine
import org.springframework.cache.CacheManager
import org.springframework.cache.annotation.EnableCaching
import org.springframework.cache.caffeine.CaffeineCacheManager
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import java.util.concurrent.TimeUnit

@Configuration
@EnableCaching
class CacheConfiguration {
    @Bean
    fun cacheManager(): CacheManager {
        val cacheManager = CaffeineCacheManager()

        // Register garmin_snapshot cache with 10-minute TTL
        cacheManager.registerCustomCache(
            "garmin_snapshot",
            Caffeine.newBuilder()
                .expireAfterWrite(10, TimeUnit.MINUTES)
                .build()
        )

        // Set default TTL for other caches
        cacheManager.setCaffeine(
            Caffeine.newBuilder().expireAfterWrite(30, TimeUnit.SECONDS)
        )

        return cacheManager
    }
}