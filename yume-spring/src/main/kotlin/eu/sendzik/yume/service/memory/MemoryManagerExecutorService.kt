package eu.sendzik.yume.service.memory

import eu.sendzik.yume.agent.MemoryManagerAgent
import eu.sendzik.yume.utils.formatTimestampForLLM
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.scheduling.annotation.Async
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Service
class MemoryManagerExecutorService(
    private val memoryManagerAgent: MemoryManagerAgent,
    private val memorySummarizerService: MemorySummarizerService,
    private val memoryManagerService: MemoryManagerService,
    private val logger: KLogger,
) {
    private val lock = ReentrantLock()
    @Async
    fun updateMemoryWithTask(task: String) {
        lock.withLock {
            logger.info {"Updating memory with task: $task" }
            memoryManagerAgent.updateMemoryWithTask(
                currentDateTime = formatTimestampForLLM(LocalDateTime.now()),
                task = task,
                memories = memoryManagerService.getFormattedMemories(),
            )
        }

        memorySummarizerService.updateMemorySummaries()
    }

    @Scheduled(cron = $$"${yume.memory.janitor-cron}")
    fun runMemoryJanitor() {
        val result = lock.withLock {
            logger.info { "Starting memory janitor" }
            memoryManagerAgent.runMemoryJanitor(
                currentDateTime = formatTimestampForLLM(LocalDateTime.now()),
                memories = memoryManagerService.getFormattedMemories(),
            )
        }

        if (result.actionsTaken.isNotEmpty()) {
            logger.info { "Memory janitor made changes, updating memory summaries" }
            memorySummarizerService.updateMemorySummaries()

            logger.info { "Memory janitor actions taken: ${result.actionsTaken.joinToString("; ")}" }
            logger.info { "Reasoning: ${result.reasoning}" }
        }

        logger.info { "Finished memory janitor" }
    }
}