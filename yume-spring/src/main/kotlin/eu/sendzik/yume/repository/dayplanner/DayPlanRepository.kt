package eu.sendzik.yume.repository.dayplanner

import eu.sendzik.yume.repository.dayplanner.model.DayPlan
import org.springframework.data.mongodb.repository.MongoRepository
import org.springframework.stereotype.Repository
import java.time.LocalDate

@Repository
interface DayPlanRepository : MongoRepository<DayPlan, String> {
    fun findByDate(date: LocalDate): DayPlan?
}
