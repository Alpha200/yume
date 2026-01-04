package eu.sendzik.yume.configuration

import eu.sendzik.yume.component.JwtAuthConverter
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.config.Customizer
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter
import org.springframework.security.web.SecurityFilterChain


@Configuration
@EnableMethodSecurity(prePostEnabled = true)
class WebSecurityConfig {
    @Bean
    fun filterChain(
        http: HttpSecurity,
        jwtAuthConverter: JwtAuthConverter
    ): SecurityFilterChain {
        val jwtConverter = JwtAuthenticationConverter().apply {
            setJwtGrantedAuthoritiesConverter(jwtAuthConverter)
        }

        http.authorizeHttpRequests { authorize ->
            authorize.requestMatchers("/webhook/**").authenticated()
        }.httpBasic(Customizer.withDefaults())

        http.authorizeHttpRequests { authorize ->
            authorize
                .requestMatchers("/auth/config").permitAll()
                .anyRequest().authenticated()
        }.oauth2ResourceServer { oauth2 ->
            oauth2.jwt { jwt -> jwt.jwtAuthenticationConverter(jwtConverter) }
        }

        return http.build()
    }
}