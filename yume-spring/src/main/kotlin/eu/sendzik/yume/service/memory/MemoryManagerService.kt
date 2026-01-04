package eu.sendzik.yume.service.memory

import eu.sendzik.yume.repository.memory.*
import eu.sendzik.yume.repository.memory.model.ReminderEntry
import eu.sendzik.yume.repository.memory.model.ReminderOptions
import eu.sendzik.yume.repository.memory.model.UserObservationEntry
import eu.sendzik.yume.repository.memory.model.UserPreferenceEntry
import eu.sendzik.yume.repository.memory.model.MemoryEntry
import eu.sendzik.yume.service.memory.model.MemoryType
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.util.*

@Service
class MemoryManagerService(
    private val memoryRepository: RagMemoryRepository
) {
    fun upsertUserPreference(
        content: String,
        memoryId: String? = null,
        place: String? = null
    ): String {
        val now = LocalDateTime.now()
        val id = memoryId ?: UUID.randomUUID().toString()

        val entry = UserPreferenceEntry(
            id = id,
            content = content,
            place = place,
            createdAt = memoryId?.let {
                memoryRepository.findById(it).orElse(null)?.createdAt
            } ?: now,
            modifiedAt = now
        )

        memoryRepository.save(entry)
        return id
    }

    fun upsertUserObservation(
        content: String,
        observationDate: LocalDateTime,
        memoryId: String? = null,
        place: String? = null
    ): String {
        val now = LocalDateTime.now()
        val id = memoryId ?: UUID.randomUUID().toString()

        val entry = UserObservationEntry(
            id = id,
            content = content,
            place = place,
            observationDate = observationDate,
            createdAt = memoryId?.let {
                memoryRepository.findById(it).orElse(null)?.createdAt
            } ?: now,
            modifiedAt = now
        )

        memoryRepository.save(entry)
        return id
    }

    fun upsertReminder(
        content: String,
        reminderOptions: ReminderOptions,
        memoryId: String? = null,
        place: String? = null
    ): String {
        val now = LocalDateTime.now()
        val id = memoryId ?: UUID.randomUUID().toString()

        val entry = ReminderEntry(
            id = id,
            content = content,
            place = place,
            reminderOptions = reminderOptions,
            createdAt = memoryId?.let {
                memoryRepository.findById(it).orElse(null)?.createdAt
            } ?: now,
            modifiedAt = now
        )

        memoryRepository.save(entry)
        return id
    }

    fun deleteMemory(memoryId: String): Boolean {
        return if (memoryRepository.existsById(memoryId)) {
            memoryRepository.deleteById(memoryId)
            true
        } else {
            false
        }
    }

    fun resetRagDatabase() {
        memoryRepository.resetRagDatabase()
    }

    fun getAllMemories(): List<MemoryEntry> {
        return memoryRepository.findAll().toList()
    }

    fun getMemoryById(id: String): MemoryEntry? {
        return memoryRepository.findById(id).orElse(null)
    }

    fun getMemoriesByType(type: MemoryType): List<MemoryEntry> {
        return memoryRepository.findAllByMemoryType(type.id)
    }

    fun getFormattedMemories(): String {
        val memories = getAllMemories()
        return memories.joinToString ("\n\n") { it.toFormattedString(compact = false) }
    }

    fun getCompactedFormattedMemories(memoryType: MemoryType): String {
        val memories = getMemoriesByType(memoryType)
        return memories.joinToString ("\n\n") { it.toFormattedString(compact = true) }
    }

    fun getFormattedRelevantMemories(message: String): String {
        val relevantMemories = memoryRepository.searchAll(message)
        val groupedMemories = relevantMemories.groupBy {
            when (it) {
                is UserPreferenceEntry -> MemoryType.PREFERENCE
                is UserObservationEntry -> MemoryType.OBSERVATION
                is ReminderEntry -> MemoryType.REMINDER
            }
        }

        return groupedMemories.map { (type, memories) ->
            "=== ${type.name} MEMORIES ===\n" + memories.joinToString("\n---\n") { memory -> memory.toFormattedString(compact = true) }
        }.joinToString("\n")
    }
}