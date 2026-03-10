package eu.sendzik.yume.repository.memory.model
fun MemoryEntry.toDocument(): MemoryDocument = when (this) {
    is UserPreferenceEntry -> MemoryDocument(
        id = id,
        type = type,
        content = content,
        place = place,
        createdAt = createdAt,
        modifiedAt = modifiedAt
    )
    is UserObservationEntry -> MemoryDocument(
        id = id,
        type = type,
        content = content,
        place = place,
        createdAt = createdAt,
        modifiedAt = modifiedAt,
        observationDate = observationDate
    )
    is ReminderEntry -> MemoryDocument(
        id = id,
        type = type,
        content = content,
        place = place,
        createdAt = createdAt,
        modifiedAt = modifiedAt,
        reminderOptions = reminderOptions
    )
}
fun MemoryDocument.toEntry(): MemoryEntry = when (type) {
    "user_preference" -> UserPreferenceEntry(
        id = id,
        content = content,
        place = place,
        createdAt = createdAt,
        modifiedAt = modifiedAt
    )
    "user_observation" -> UserObservationEntry(
        id = id,
        content = content,
        place = place,
        createdAt = createdAt,
        modifiedAt = modifiedAt,
        observationDate = observationDate ?: error("observationDate missing for user_observation $id")
    )
    "reminder" -> ReminderEntry(
        id = id,
        content = content,
        place = place,
        createdAt = createdAt,
        modifiedAt = modifiedAt,
        reminderOptions = reminderOptions ?: error("reminderOptions missing for reminder $id")
    )
    else -> error("Unknown memory type: $type")
}
