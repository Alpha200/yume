package eu.sendzik.yume.service.matrix

import eu.sendzik.yume.configuration.MatrixConfiguration
import eu.sendzik.yume.repository.conversation.model.ConversationHistoryEntryType
import eu.sendzik.yume.service.conversation.ConversationHistoryManagerService
import eu.sendzik.yume.service.matrix.model.UserMessageEvent
import eu.sendzik.yume.service.matrix.model.UserReactionEvent
import io.github.oshai.kotlinlogging.KLogger
import io.ktor.http.Url
import jakarta.annotation.PostConstruct
import jakarta.annotation.PreDestroy
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import net.folivo.trixnity.clientserverapi.client.MatrixAuthProvider
import net.folivo.trixnity.clientserverapi.client.MatrixClientServerApiClient
import net.folivo.trixnity.clientserverapi.client.MatrixClientServerApiClientImpl
import net.folivo.trixnity.clientserverapi.client.classicInMemory
import net.folivo.trixnity.clientserverapi.model.authentication.IdentifierType
import net.folivo.trixnity.core.model.RoomId
import net.folivo.trixnity.core.model.UserId
import net.folivo.trixnity.core.model.events.ClientEvent
import net.folivo.trixnity.core.model.events.m.ReactionEventContent
import net.folivo.trixnity.core.model.events.m.room.RoomMessageEventContent
import net.folivo.trixnity.core.subscribeEvent
import org.springframework.context.ApplicationEventPublisher
import org.springframework.stereotype.Service
import java.time.Instant
import java.time.LocalDateTime
import java.time.OffsetDateTime

@Service
class MatrixClientService(
    private val logger: KLogger,
    private val matrixConfiguration: MatrixConfiguration,
    private val applicationEventPublisher: ApplicationEventPublisher,
    private val conversationHistoryManagerService: ConversationHistoryManagerService,
) {
    private lateinit var matrixRestClient : MatrixClientServerApiClient

    private val scopeJob: Job = SupervisorJob()
    private val scope = CoroutineScope(scopeJob + Dispatchers.IO)
    private val userId = UserId(matrixConfiguration.userId)

    @PostConstruct
    fun startMatrixClient() {
        scope.launch {
            val accessToken = performLogin()
            initializeMatrixClient(accessToken)
            subscribeToRoomEvents()
            matrixRestClient.sync.start()
        }
    }

    @PreDestroy
    fun stopMatrixClient() {
        runBlocking {
            try {
                matrixRestClient.sync.stop()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
        scopeJob.cancel()
    }

    suspend fun sendMessageToRoom(message: String) {
        matrixRestClient.room.sendMessageEvent(
            RoomId(matrixConfiguration.room),
            RoomMessageEventContent.TextBased.Text(body = message)
        ).getOrThrow()

        matrixRestClient.room.setTyping(RoomId(matrixConfiguration.room), userId, false)
    }

    private suspend fun performLogin(): String {
        val loginClient = MatrixClientServerApiClientImpl(
            baseUrl = Url(matrixConfiguration.homeserverUrl)
        )

        val loginResponse = loginClient.authentication.login(
            identifier = IdentifierType.User(matrixConfiguration.userId),
            password = matrixConfiguration.password,
            deviceId = null,
            initialDeviceDisplayName = "Yume"
        ).getOrThrow()

        return loginResponse.accessToken
    }

    private fun initializeMatrixClient(accessToken: String) {
        matrixRestClient = MatrixClientServerApiClientImpl(
            baseUrl = Url(matrixConfiguration.homeserverUrl),
            authProvider = MatrixAuthProvider.classicInMemory(accessToken)
        )
    }

    private suspend fun subscribeToRoomEvents() {
        val roomId = RoomId(matrixConfiguration.room)
        val startTime = Instant.now()

        matrixRestClient.sync.subscribeEvent<RoomMessageEventContent.TextBased.Text, ClientEvent.RoomEvent<RoomMessageEventContent.TextBased.Text>> { event ->
            if (event.roomId == roomId && Instant.ofEpochMilli(event.originTimestamp) > startTime) {
                handleRoomMessage(event, roomId)
            }
        }

        matrixRestClient.sync.subscribeEvent<ReactionEventContent, ClientEvent.RoomEvent<ReactionEventContent>> { event ->
            if (event.roomId == roomId && Instant.ofEpochMilli(event.originTimestamp) > startTime) {
                handleReactionEvent(event, roomId)
            }
        }
    }

    private suspend fun handleReactionEvent(event: ClientEvent.RoomEvent<ReactionEventContent>, roomId: RoomId) {
        if (event.sender == userId) {
            logger.debug {"Received own reaction, ignoring. Event id: ${event.id}" }
            return
        }

        val reaction = event.content.relatesTo?.key
        val relatedEventId = event.content.relatesTo?.eventId

        if (reaction == null || relatedEventId == null) {
            logger.warn { "Received reaction event with missing data. Event id: ${event.id}" }
            return
        }

        logger.debug { "Processing reaction '$reaction' for event $relatedEventId" }

        // Look up the original message from the database
        val historyEntry = conversationHistoryManagerService.findByEventId(relatedEventId.full)

        if (historyEntry == null) {
            logger.warn { "Could not find related message for event $relatedEventId in database. Reaction will be ignored." }
            return
        }

        val reactionTimestamp = LocalDateTime.ofEpochSecond(
            event.originTimestamp / 1000,
            0,
            OffsetDateTime.now().offset
        )

        logger.debug { "Publishing UserReactionEvent for reaction '$reaction' on message: ${historyEntry.content}" }

        applicationEventPublisher.publishEvent(
            UserReactionEvent(
                timestamp = reactionTimestamp,
                reaction = reaction,
                relatedMessage = historyEntry.content,
                relatedEventId = relatedEventId.full
            )
        )
    }

    private suspend fun handleRoomMessage(
        event: ClientEvent.RoomEvent<RoomMessageEventContent.TextBased.Text>,
        roomId: RoomId
    ) {
        val body = event.content.body
        val messageTimestamp = LocalDateTime.ofEpochSecond(event.originTimestamp / 1000, 0, OffsetDateTime.now().offset)

        if (event.sender == userId) {
            // Save bot's own messages (system messages) to conversation history with event ID
            logger.debug {"Received own message, saving to history. Event id: ${event.id}" }
            conversationHistoryManagerService.addEntry(
                body,
                ConversationHistoryEntryType.SYSTEM_MESSAGE,
                messageTimestamp,
                event.id.full
            )
            return
        }

        logger.debug {"Starting to process user message with event id ${event.id}" }

        matrixRestClient.room.setTyping(roomId, userId, true, timeout = 60000)

        applicationEventPublisher.publishEvent(
            UserMessageEvent(
                timestamp = messageTimestamp,
                message = body,
                eventId = event.id.full
            )
        )
    }
}