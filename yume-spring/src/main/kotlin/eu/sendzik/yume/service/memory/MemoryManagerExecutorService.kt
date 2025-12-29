package eu.sendzik.yume.service.memory

import eu.sendzik.yume.agent.MemoryManagerAgent
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.scheduling.annotation.Async
import org.springframework.stereotype.Service
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

@Service
class MemoryManagerExecutorService(
    private val memoryManagerAgent: MemoryManagerAgent,
    private val logger: KLogger,
) {
    private val lock = ReentrantLock()
    @Async
    fun updateMemoryWithTask(task: String) {
        lock.withLock {
            logger.info {"Updating memory with task: $task" }
            memoryManagerAgent.updateMemoryWithTask(task)
        }
    }
}