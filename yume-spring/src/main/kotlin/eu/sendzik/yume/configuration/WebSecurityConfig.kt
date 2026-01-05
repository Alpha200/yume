package eu.sendzik.yume.configuration

import eu.sendzik.yume.component.JwtAuthConverter
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.core.annotation.Order
import org.springframework.security.config.Customizer
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.core.userdetails.User
import org.springframework.security.core.userdetails.UserDetailsService
import org.springframework.security.crypto.factory.PasswordEncoderFactories
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter
import org.springframework.security.provisioning.InMemoryUserDetailsManager
import org.springframework.security.web.SecurityFilterChain


@Configuration
@EnableMethodSecurity(prePostEnabled = true)
class WebSecurityConfig {
    @Bean
    fun userDetailsService(
        @Value($$"${spring.security.user.name}") username: String,
        @Value($$"${spring.security.user.password}") password: String,
    ): UserDetailsService {
        return InMemoryUserDetailsManager().apply {
            val pwEncoder = PasswordEncoderFactories.createDelegatingPasswordEncoder()
            createUser(
                User.withUsername(username)
                    .password(pwEncoder.encode(password))
                    .build()
            )
        }
    }

    @Bean
    @Order(1)
    fun webhookFilterChain(http: HttpSecurity): SecurityFilterChain {
        http
            .securityMatcher("/webhook/**")
            .authorizeHttpRequests { authorize ->
                authorize.anyRequest().authenticated()
            }
            .httpBasic(Customizer.withDefaults())
            .csrf { it.disable() }

        return http.build()
    }

    @Bean
    @Order(2)
    fun mainFilterChain(
        http: HttpSecurity,
        jwtAuthConverter: JwtAuthConverter
    ): SecurityFilterChain {
        val jwtConverter = JwtAuthenticationConverter().apply {
            setJwtGrantedAuthoritiesConverter(jwtAuthConverter)
        }

        http
            .authorizeHttpRequests { authorize ->
                authorize
                    .requestMatchers("/auth/config").permitAll()
                    .anyRequest().authenticated()
            }
            .oauth2ResourceServer { oauth2 ->
                oauth2.jwt { jwt -> jwt.jwtAuthenticationConverter(jwtConverter) }
            }
            .csrf { it.disable() }

        return http.build()
    }
}