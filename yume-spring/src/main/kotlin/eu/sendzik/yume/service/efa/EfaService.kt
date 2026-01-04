package eu.sendzik.yume.service.efa

import eu.sendzik.yume.client.EfaClient
import eu.sendzik.yume.service.efa.model.JourneyPlan
import eu.sendzik.yume.service.efa.model.JourneyStep
import eu.sendzik.yume.service.efa.model.PublicTransportDeparture
import eu.sendzik.yume.service.efa.model.EfaLeg
import eu.sendzik.yume.service.efa.model.EfaLegLocation
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import kotlin.math.roundToInt

@Service
class EfaService(
    private val efaClient: EfaClient,
    @Value("\${yume.efa.client-id:CLIENTID}")
    private val efaClientId: String,
    @Value("\${yume.efa.client-name:yume}")
    private val efaClientName: String,
    private val logger: KLogger,
) {

    /**
     * Get the station ID from a station name using EFA stopfinder.
     *
     * @param stationName Name of the station (e.g., "Central Station")
     * @return Station ID or null if not found
     */
    fun getStationId(stationName: String): String? {
        return try {
            logger.debug { "Searching for station: $stationName" }

            val params = buildDefaultParams(
                "name_sf" to stationName,
                "type_sf" to "any"
            )

            val response = efaClient.stopFinderRequest(params)
            if (response != null) {
                val locations = response.locations

                if (locations.isNotEmpty()) {
                    // Filter for actual stops (type="stop"), prefer best matches
                    val stops = locations.filter { it.type == "stop" }

                    val bestStop = if (stops.isNotEmpty()) {
                        stops.maxByOrNull { it.matchQuality ?: 0.0 }
                    } else {
                        // If no stops found, try any location
                        locations.maxByOrNull { it.matchQuality ?: 0.0 }
                    }

                    val stationId = bestStop?.id
                    if (stationId != null) {
                        logger.debug { "Found station ID for '$stationName': $stationId" }
                    } else {
                        logger.debug { "Station '$stationName' not found" }
                    }
                    stationId
                } else {
                    logger.debug { "Station '$stationName' not found" }
                    null
                }
            } else {
                logger.error { "EFA API returned null response" }
                null
            }
        } catch (e: Exception) {
            logger.error(e) { "Error searching station: $stationName" }
            null
        }
    }

    /**
     * Get all serving lines for a station.
     *
     * @param stationId EFA station ID
     * @return List of line dictionaries with id, name, number, and destination
     */
    fun getServingLines(stationId: String): List<Map<String, Any>> {
        return try {
            logger.debug { "Fetching serving lines for station: $stationId" }

            val params = buildDefaultParams(
                "name_sl" to stationId,
                "type_sl" to "stop",
                "deleteAssignedStops_sl" to "1",
                "lineReqType" to "1",
                "lsShowTrainsExplicit" to "1",
                "mergeDir" to "false",
                "mode" to "odv",
                "sl3plusServingLinesMacro" to "1",
                "withoutTrains" to "0",
                "language" to "de",
                "version" to "11.0.6.72"
            )

            val response = efaClient.servingLinesRequest(params)
            if (response != null) {
                val lines = response.lines.map { line ->
                    mapOf(
                        "id" to (line.id ?: ""),
                        "name" to (line.name ?: ""),
                        "number" to (line.number ?: ""),
                        "disassembledName" to (line.disassembledName ?: ""),
                        "product" to mapOf(
                            "name" to (line.product?.name ?: ""),
                            "class" to (line.product?.clazz ?: 0)
                        )
                    )
                }
                logger.debug { "Found ${lines.size} serving lines" }
                lines
            } else {
                logger.error { "EFA API returned null response for serving lines" }
                emptyList()
            }
        } catch (e: Exception) {
            logger.error(e) { "Error fetching serving lines for station: $stationId" }
            emptyList()
        }
    }

    /**
     * Find a line ID by searching for line number or name.
     * Performs case-insensitive substring matching for flexibility.
     *
     * @param stationId EFA station ID
     * @param lineQuery Search string (e.g., "U47", "RB33", "ICE")
     * @return Line ID or null if not found
     */
    fun findLineId(stationId: String, lineQuery: String): String? {
        return try {
            val lines = getServingLines(stationId)
            val queryLower = lineQuery.lowercase()

            for (line in lines) {
                val number = (line["number"] as? String ?: "").lowercase()
                val disassembledName = (line["disassembledName"] as? String ?: "").lowercase()
                val name = (line["name"] as? String ?: "").lowercase()
                @Suppress("UNCHECKED_CAST")
                val product = line["product"] as? Map<String, Any> ?: emptyMap()
                val productName = (product["name"] as? String ?: "").lowercase()

                // Check if query is contained in any of these fields
                if (queryLower in number ||
                    queryLower in disassembledName ||
                    queryLower in name ||
                    queryLower in productName
                ) {
                    val lineId = line["id"] as? String
                    if (lineId != null) {
                        logger.debug { "Found line ID for '$lineQuery': $lineId" }
                    }
                    return lineId
                }
            }

            logger.debug { "Line matching '$lineQuery' not found at station $stationId" }
            null
        } catch (e: Exception) {
            logger.error(e) { "Error finding line ID for: $lineQuery" }
            null
        }
    }

    /**
     * Get departures for a station, optionally filtered by line and/or direction.
     *
     * @param stationId EFA station ID (if known)
     * @param stationName Station name (will be looked up if stationId not provided)
     * @param limit Maximum number of departures to return
     * @param lineQuery Optional line search query (e.g., "U47", "RB33", "ICE")
     * @param directionQuery Optional direction search query (e.g., "Berlin", "Hamburg")
     * @return List of PublicTransportDeparture objects
     */
    fun getDepartures(
        stationId: String? = null,
        stationName: String? = null,
        limit: Int = 10,
        lineQuery: String? = null,
        directionQuery: String? = null
    ): List<PublicTransportDeparture> {
        return try {
            // Resolve station ID if not provided
            val resolvedStationId = stationId ?: (stationName?.let { getStationId(it) })
            if (resolvedStationId == null) {
                logger.warn { "No station ID provided and could not resolve station name" }
                return emptyList()
            }

            logger.debug { "Fetching departures for station ID: $resolvedStationId" }

            // Get line ID if lineQuery is specified
            val lineId = if (!lineQuery.isNullOrBlank()) {
                val foundLineId = findLineId(resolvedStationId, lineQuery)
                if (foundLineId == null) {
                    logger.debug { "Could not find line matching '$lineQuery' at station $resolvedStationId" }
                    return emptyList()
                }
                foundLineId
            } else {
                null
            }

            val params = buildDepartureParams(resolvedStationId, limit)
            if (lineId != null) {
                params["line"] = lineId
            }

            val response = efaClient.departuresRequest(params)
            if (response != null) {
                val stopEvents = response.stopEvents
                val departures = mutableListOf<PublicTransportDeparture>()

                for (event in stopEvents) {
                    try {
                        val transportation = event.transportation
                        val location = event.location
                        val locationProps = location?.properties

                        val plannedTime = parseDepartureTimeIso(event.departureTimePlanned)
                        val estimatedTime = parseDepartureTimeIso(event.departureTimeEstimated)
                        val delay = calculateDelay(plannedTime, estimatedTime)

                        val destinationName = transportation?.destination?.name ?: "Unknown"

                        // Filter by direction if specified
                        if (directionQuery != null &&
                            directionQuery.lowercase() !in destinationName.lowercase()
                        ) {
                            continue
                        }

                        val departure = PublicTransportDeparture(
                            line = transportation?.number ?: "N/A",
                            destination = destinationName,
                            plannedTime = plannedTime ?: "N/A",
                            estimatedTime = estimatedTime,
                            delayMinutes = delay,
                            transportType = transportation?.product?.name ?: "Unknown",
                            platform = locationProps?.platform,
                            realtime = event.isRealtimeControlled
                        )
                        departures.add(departure)
                    } catch (e: Exception) {
                        logger.error(e) { "Error parsing departure" }
                        continue
                    }
                }

                logger.debug { "Found ${departures.size} departures" }
                departures
            } else {
                logger.error { "EFA API returned null response for departures" }
                emptyList()
            }
        } catch (e: Exception) {
            logger.error(e) { "Error fetching departures" }
            emptyList()
        }
    }

    /**
     * Get departures in a map format suitable for serialization.
     *
     * @param stationId EFA station ID
     * @param stationName Station name
     * @param limit Maximum number of departures
     * @param lineQuery Optional line search query
     * @param directionQuery Optional direction search query
     * @return Map with departure information
     */
    fun getDeparturesJson(
        stationId: String? = null,
        stationName: String? = null,
        limit: Int = 10,
        lineQuery: String? = null,
        directionQuery: String? = null
    ): Map<String, Any> {
        val departures = getDepartures(stationId, stationName, limit, lineQuery, directionQuery)
        return mapOf(
            "status" to (if (departures.isNotEmpty()) "success" else "no_departures"),
            "departures" to departures,
            "count" to departures.size
        )
    }

    /**
     * Search for full journeys between two points.
     *
     * @param origin Origin station name
     * @param destination Destination station name
     * @param searchForArrival Whether to search for arrival instead of departure
     * @param originType Type of origin location ("any" by default)
     * @param destinationType Type of destination location ("any" by default)
     * @param limit Maximum number of journeys to return
     * @param via Optional via location
     * @param viaType Type of via location
     * @param language Language code (default "de")
     * @return List of JourneyPlan objects
     */
    fun getJourneys(
        origin: String,
        destination: String,
        searchForArrival: Boolean = false,
        originType: String = "any",
        destinationType: String = "any",
        limit: Int = 3,
        via: String? = null,
        viaType: String = "any",
        language: String = "de"
    ): List<JourneyPlan> {
        return try {
            if (origin.isBlank() || destination.isBlank()) {
                logger.warn { "Origin and destination are required for journey search" }
                return emptyList()
            }

            val params = buildJourneyParams(
                origin, destination, searchForArrival, originType, destinationType,
                via, viaType, language
            )

            val response = efaClient.tripRequest(params)
            if (response != null) {
                val rawJourneys = response.journeys

                val effectiveLimit = if (limit <= 0) rawJourneys.size else limit

                val journeys = mutableListOf<JourneyPlan>()
                for (rawJourney in rawJourneys.take(effectiveLimit)) {
                    try {
                        val legs = rawJourney.legs
                        val steps = mutableListOf<JourneyStep>()

                        for (leg in legs) {
                            val step = parseJourneyStep(leg)
                            if (step != null) {
                                steps.add(step)
                            }
                        }

                        if (steps.isNotEmpty()) {
                            val totalDurationSeconds = legs.sumOf {
                                (it.duration ?: 0).toLong()
                            }
                            val journeyPlan = JourneyPlan(
                                lengthMinutes = secondsToMinutes(totalDurationSeconds.toInt()),
                                steps = steps
                            )
                            journeys.add(journeyPlan)
                        }
                    } catch (e: Exception) {
                        logger.error(e) { "Error parsing journey" }
                        continue
                    }
                }

                logger.debug { "Found ${journeys.size} journeys between '$origin' and '$destination'" }
                journeys
            } else {
                logger.error { "EFA API returned null response for journeys" }
                emptyList()
            }
        } catch (e: Exception) {
            logger.error(e) { "Error fetching journeys" }
            emptyList()
        }
    }

    // ==================== Helper Methods ====================

    private fun buildDefaultParams(vararg pairs: Pair<String, String>): MutableMap<String, String> {
        return mutableMapOf(
            "clientID" to efaClientId,
            "clientName" to efaClientName,
            "outputFormat" to "rapidJSON",
            *pairs
        )
    }

    private fun buildDepartureParams(stationId: String, limit: Int): MutableMap<String, String> {
        return buildDefaultParams(
            "name_dm" to stationId,
            "type_dm" to "any",
            "depType" to "stopEvents",
            "useRealtime" to "1",
            "canChangeMOT" to "0",
            "coordOutputFormat" to "WGS84[dd.ddddd]",
            "deleteAssignedStops_dm" to "1",
            "depSequence" to limit.toString(),
            "doNotSearchForStops" to "1",
            "genMaps" to "0",
            "imparedOptionsActive" to "1",
            "inclMOT_1" to "true",
            "inclMOT_2" to "true",
            "inclMOT_3" to "true",
            "inclMOT_4" to "true",
            "inclMOT_5" to "true",
            "inclMOT_6" to "true",
            "inclMOT_7" to "true",
            "inclMOT_8" to "true",
            "inclMOT_9" to "true",
            "inclMOT_10" to "true",
            "inclMOT_11" to "true",
            "inclMOT_13" to "true",
            "inclMOT_14" to "true",
            "inclMOT_15" to "true",
            "inclMOT_16" to "true",
            "inclMOT_17" to "true",
            "inclMOT_18" to "true",
            "inclMOT_19" to "true",
            "includeCompleteStopSeq" to "1",
            "includedMeans" to "checkbox",
            "itOptionsActive" to "1",
            "itdDateTimeDepArr" to "dep",
            "language" to "de",
            "locationServerActive" to "1",
            "maxTimeLoop" to "1",
            "mergeDep" to "1",
            "mode" to "direct",
            "ptOptionsActive" to "1",
            "serverInfo" to "1",
            "sl3plusDMMacro" to "1",
            "useAllStops" to "1",
            "useProxFootSearchDestination" to "true",
            "useProxFootSearchOrigin" to "true",
            "version" to "11.0.6.72"
        )
    }

    private fun buildJourneyParams(
        origin: String,
        destination: String,
        searchForArrival: Boolean,
        originType: String,
        destinationType: String,
        via: String?,
        viaType: String,
        language: String
    ): MutableMap<String, String> {
        val params = buildDefaultParams(
            "accessProfile" to "0",
            "allInterchangesAsLegs" to "1",
            "calcOneDirection" to "1",
            "changeSpeed" to "fast",
            "coordOutputDistance" to "1",
            "coordOutputFormat" to "WGS84[dd.ddddd]",
            "descWithCoordPedestrian" to "1",
            "genC" to "1",
            "genMaps" to "0",
            "imparedOptionsActive" to "1",
            "inclMOT_1" to "true",
            "inclMOT_2" to "true",
            "inclMOT_3" to "true",
            "inclMOT_4" to "true",
            "inclMOT_5" to "true",
            "inclMOT_6" to "true",
            "inclMOT_7" to "true",
            "inclMOT_8" to "true",
            "inclMOT_9" to "true",
            "inclMOT_10" to "true",
            "inclMOT_11" to "true",
            "inclMOT_13" to "true",
            "inclMOT_14" to "true",
            "inclMOT_15" to "true",
            "inclMOT_16" to "true",
            "inclMOT_17" to "true",
            "inclMOT_18" to "true",
            "inclMOT_19" to "true",
            "includedMeans" to "checkbox",
            "itOptionsActive" to "1",
            "itdTripDateTimeDepArr" to (if (searchForArrival) "arr" else "dep"),
            "language" to language,
            "lineRestriction" to "400",
            "locationServerActive" to "1",
            "name_destination" to destination,
            "name_origin" to origin,
            "ptOptionsActive" to "1",
            "routeType" to "LEASTTIME",
            "serverInfo" to "1",
            "sl3plusTripMacro" to "1",
            "trITMOTvalue100" to "15",
            "type_destination" to destinationType,
            "type_origin" to originType,
            "useProxFootSearchDestination" to "true",
            "useProxFootSearchOrigin" to "true",
            "useRealtime" to "1",
            "useUT" to "1",
            "version" to "11.0.6.72"
        )

        if (!via.isNullOrBlank()) {
            params["name_via"] = via
            params["type_via"] = viaType
        }

        return params
    }

    private fun parseDepartureTimeIso(timeStr: String?): String? {
        if (timeStr == null) return null
        return try {
            val dtUtc = LocalDateTime.parse(timeStr.replace('Z', ' ').trim(), DateTimeFormatter.ISO_DATE_TIME)
            dtUtc.format(DateTimeFormatter.ofPattern("HH:mm"))
        } catch (e: Exception) {
            logger.debug(e) { "Failed to parse time: $timeStr" }
            null
        }
    }

    private fun calculateDelay(plannedTime: String?, estimatedTime: String?): Int? {
        if (plannedTime == null || estimatedTime == null) return null
        return try {
            val planned = LocalDateTime.parse("2025-01-01T$plannedTime", DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            val estimated = LocalDateTime.parse("2025-01-01T$estimatedTime", DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            val delaySeconds = (estimated.toLocalTime().toSecondOfDay() - planned.toLocalTime().toSecondOfDay())
            (delaySeconds / 60).coerceAtLeast(0)
        } catch (e: Exception) {
            logger.debug(e) { "Failed to calculate delay" }
            null
        }
    }

    private fun secondsToMinutes(seconds: Int): Int {
        if (seconds <= 0) return 0
        val minutes = seconds.toDouble() / 60.0
        return if (minutes < 1) 1 else minutes.roundToInt()
    }

    private fun extractPlatform(location: EfaLegLocation?): String? {
        if (location == null) return null
        val platform = location.properties?.platform
        if (platform != null) return platform
        return location.parent?.properties?.platform
    }

    private fun parseLocationTime(
        location: EfaLegLocation?,
        preferredKey: String,
        fallbackKey: String? = null
    ): String? {
        if (location == null) return null
        val timeValue = when (preferredKey) {
            "departureTimePlanned" -> location.departureTimePlanned
            "departureTimeBaseTimetable" -> location.departureTimeBaseTimetable
            "departureTimeEstimated" -> location.departureTimeEstimated
            "arrivalTimePlanned" -> location.arrivalTimePlanned
            "arrivalTimeBaseTimetable" -> location.arrivalTimeBaseTimetable
            "arrivalTimeEstimated" -> location.arrivalTimeEstimated
            else -> null
        } ?: if (fallbackKey != null) {
            when (fallbackKey) {
                "departureTimePlanned" -> location.departureTimePlanned
                "departureTimeBaseTimetable" -> location.departureTimeBaseTimetable
                "departureTimeEstimated" -> location.departureTimeEstimated
                "arrivalTimePlanned" -> location.arrivalTimePlanned
                "arrivalTimeBaseTimetable" -> location.arrivalTimeBaseTimetable
                "arrivalTimeEstimated" -> location.arrivalTimeEstimated
                else -> null
            }
        } else null
        return parseDepartureTimeIso(timeValue)
    }

    private fun parseJourneyStep(leg: EfaLeg): JourneyStep? {
        return try {
            val transportation = leg.transportation
            val product = transportation?.product
            val productName = (product?.name ?: "").lowercase()
            val productClass = product?.clazz

            val mode = when {
                productName == "footpath" || productClass == 100 -> "walk"
                else -> transportation?.name
                    ?: product?.name
                    ?: "Unknown"
            }

            val line = when {
                productName == "footpath" || productClass == 100 -> null
                else -> transportation?.number
                    ?: transportation?.name
            }

            val originNode = leg.origin
            val destinationNode = leg.destination

            val departurePlanned =
                parseLocationTime(originNode, "departureTimePlanned", "departureTimeBaseTimetable")
            val departureEstimated = parseLocationTime(originNode, "departureTimeEstimated")
            val arrivalPlanned =
                parseLocationTime(destinationNode, "arrivalTimePlanned", "arrivalTimeBaseTimetable")
            val arrivalEstimated = parseLocationTime(destinationNode, "arrivalTimeEstimated")

            JourneyStep(
                mode = mode,
                line = line,
                origin = originNode?.name
                    ?: originNode?.disassembledName
                    ?: "Unknown",
                destination = destinationNode?.name
                    ?: destinationNode?.disassembledName
                    ?: "Unknown",
                departurePlanned = departurePlanned,
                departureEstimated = departureEstimated,
                arrivalPlanned = arrivalPlanned,
                arrivalEstimated = arrivalEstimated,
                platformOrigin = extractPlatform(originNode),
                platformDestination = extractPlatform(destinationNode),
                departureDelayMinutes = calculateDelay(departurePlanned, departureEstimated),
                arrivalDelayMinutes = calculateDelay(arrivalPlanned, arrivalEstimated),
                durationMinutes = secondsToMinutes(leg.duration ?: 0)
            )
        } catch (e: Exception) {
            logger.error(e) { "Error parsing journey step" }
            null
        }
    }
}


