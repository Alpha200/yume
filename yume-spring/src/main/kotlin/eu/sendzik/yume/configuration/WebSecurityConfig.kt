package eu.sendzik.yume.configuration

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter
import org.springframework.security.web.SecurityFilterChain


@Configuration
@EnableMethodSecurity(prePostEnabled = true)
class WebSecurityConfig {
    @Bean
    fun filterChain(http: HttpSecurity): SecurityFilterChain? {
        val jwtConverter = JwtAuthenticationConverter().apply {
            setJwtGrantedAuthoritiesConverter(JwtAuthConverter())
        }

        http.authorizeHttpRequests { authorize ->
            authorize.anyRequest().authenticated()
        }.oauth2ResourceServer { oauth2 ->
            oauth2.jwt { jwt -> jwt.jwtAuthenticationConverter(jwtConverter) }
        }
        return http.build()
    }
}