package eu.sendzik.yume.service.memory.model

enum class MemoryType(val id: String) {
    OBSERVATION("user_observation"),
    PREFERENCE("user_preference"),
    REMINDER("reminder"),
}