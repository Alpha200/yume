package eu.sendzik.yume.repository.strava

import eu.sendzik.yume.service.strava.model.StravaCredentials
import org.springframework.data.mongodb.repository.MongoRepository

interface StravaCredentialsRepository : MongoRepository<StravaCredentials, String> {
    fun findByAthleteId(athleteId: Long): StravaCredentials?
}
