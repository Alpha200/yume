package eu.sendzik.yume.client.model

data class HomeAssistantState(
    val state: String,
    val attributes: Map<String, Any>
)
