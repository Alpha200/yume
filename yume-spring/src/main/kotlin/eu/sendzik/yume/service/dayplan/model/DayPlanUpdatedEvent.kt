package eu.sendzik.yume.service.dayplan.model

import eu.sendzik.yume.repository.dayplanner.model.DayPlan

data class DayPlanUpdatedEvent(
    val dayPlan: DayPlan,
)
