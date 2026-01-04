package eu.sendzik.yume.service.matrix

import eu.sendzik.yume.configuration.MatrixConfiguration
import eu.sendzik.yume.service.matrix.model.UserMessageEvent
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
    }

    private suspend fun handleRoomMessage(
        event: ClientEvent.RoomEvent<RoomMessageEventContent.TextBased.Text>,
        roomId: RoomId
    ) {
        if (event.sender == userId) {
            logger.debug {"Received own message, ignoring. Event id: ${event.id}" }
            return
        }

        logger.debug {"Starting to process message with event id ${event.id}" }

        val body = event.content.body
        val messageTimestamp = LocalDateTime.ofEpochSecond(event.originTimestamp / 1000, 0, OffsetDateTime.now().offset)

        matrixRestClient.room.setTyping(roomId, userId, true, timeout = 60000)

        applicationEventPublisher.publishEvent(
            UserMessageEvent(
                timestamp = messageTimestamp,
                message = body
            )
        )
    }
}