package eu.sendzik.yume.component

import org.springframework.core.convert.converter.Converter
import org.springframework.security.core.GrantedAuthority
import org.springframework.security.core.authority.SimpleGrantedAuthority
import org.springframework.security.oauth2.jwt.Jwt
import org.springframework.stereotype.Component

@Component
class JwtAuthConverter: Converter<Jwt, Collection<GrantedAuthority>> {
    override fun convert(jwt: Jwt): Collection<SimpleGrantedAuthority> {
        val realmAccess = jwt.getClaimAsMap("realm_access")
        if (realmAccess.isNullOrEmpty()) {
            return listOf()
        }
        val roles = realmAccess["roles"] as List<String?>
        return roles.map({ role -> SimpleGrantedAuthority("ROLE_" + role?.uppercase()) })
    }
}