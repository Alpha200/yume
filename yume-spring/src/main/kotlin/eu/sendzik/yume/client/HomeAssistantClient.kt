package eu.sendzik.yume.client

import eu.sendzik.yume.client.model.HomeAssistantState
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.service.annotation.GetExchange

interface HomeAssistantClient {
    @GetExchange("api/states/{entityId}")
    fun getStateForEntity(@PathVariable entityId: String): HomeAssistantState
}