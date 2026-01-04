package eu.sendzik.yume.service.memory

import eu.sendzik.yume.agent.MemorySummarizerAgent
import eu.sendzik.yume.service.memory.model.MemoryType
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import jakarta.annotation.PostConstruct
import org.springframework.scheduling.annotation.Async
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Service
class MemorySummarizerService(
    private val memorySummarizerAgent: MemorySummarizerAgent,
    private val memoryManagerService: MemoryManagerService,
    private val logger: KLogger,
) {
    private val memorySummaries = mutableMapOf<MemoryType, String>()
    private val lock = ReentrantLock()

    @Async
    fun updateMemorySummaries() {
        lock.withLock {
            for (entry in MemoryType.entries) {
                logger.info { "Updating memory summary for type ${entry.name}" }

                val formattedMemories = memoryManagerService.getCompactedFormattedMemories(entry)

                if (formattedMemories.isNotBlank()) {
                    val summary = memorySummarizerAgent.summarizeMemory(
                        currentDateTime = formatTimestampForLLM(LocalDateTime.now()),
                        memories = "${entry.name} MEMORIES:\n$formattedMemories",
                    )
                    memorySummaries[entry] = summary
                }
            }
        }
    }

    fun getMemorySummary(memoryType: MemoryType): String? {
        return memorySummaries[memoryType]
    }

    @PostConstruct
    fun init() {
        updateMemorySummaries()
    }
}