package eu.sendzik.yume.tool

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool
import eu.sendzik.yume.service.efa.EfaService
import io.github.oshai.kotlinlogging.KLogger
import org.springframework.stereotype.Component

@Component
@Suppress("unused")
class EfaTools(
    private val efaService: EfaService,
    private val logger: KLogger,
) {

    /**
     * Get upcoming departures for a public transport station.
     * Supports filtering by line number/name and destination direction.
     */
    @Suppress("UNUSED")
    @Tool("Get upcoming departures for a public transport station with optional filtering by line and direction")
    fun getStationDepartures(
        @P("The name of the station (e.g., 'Essen Hauptbahnhof')")
        stationName: String,
        @P("Maximum number of departures to return (default: 10)")
        limit: Int = 10,
        @P("Optional filter by line (e.g., 'U47', 'RB33', 'ICE'). Substring match.")
        lineQuery: String? = null,
        @P("Optional filter by destination (e.g., 'Berlin', 'Köln'). Substring match.")
        directionQuery: String? = null
    ): String = runCatching {
        val result = efaService.getDeparturesJson(
            stationName = stationName,
            limit = limit,
            lineQuery = lineQuery,
            directionQuery = directionQuery
        )

        @Suppress("UNCHECKED_CAST")
        val departures = result["departures"] as? List<Any> ?: emptyList()
        val status = result["status"] as? String

        if (status == "no_departures" || departures.isEmpty()) {
            val filters = mutableListOf<String>()
            if (!lineQuery.isNullOrBlank()) {
                filters.add("line '$lineQuery'")
            }
            if (!directionQuery.isNullOrBlank()) {
                filters.add("direction '$directionQuery'")
            }

            return if (filters.isNotEmpty()) {
                "No departures found for $stationName with ${filters.joinToString(" and ")}"
            } else {
                "No upcoming departures found for $stationName"
            }
        }

        // Format the departures
        var formatted = "Departures from $stationName:\n"

        if (!lineQuery.isNullOrBlank() || !directionQuery.isNullOrBlank()) {
            val filters = mutableListOf<String>()
            if (!lineQuery.isNullOrBlank()) {
                filters.add("line $lineQuery")
            }
            if (!directionQuery.isNullOrBlank()) {
                filters.add("to $directionQuery")
            }
            formatted = "Departures from $stationName (${filters.joinToString(", ")}):\n"
        }

        departures.forEachIndexed { index, depObj ->
            @Suppress("UNCHECKED_CAST")
            val dep = depObj as? Map<String, Any> ?: return@forEachIndexed

            val line = dep["line"] as? String ?: "N/A"
            val destination = dep["destination"] as? String ?: "Unknown"
            val plannedTime = dep["planned_time"] as? String ?: "N/A"
            val estimatedTime = dep["estimated_time"] as? String
            val delay = (dep["delay_minutes"] as? Number)?.toInt() ?: 0
            val platform = dep["platform"] as? String ?: "—"
            val realtime = dep["realtime"] as? Boolean ?: false
            val transportType = dep["transport_type"] as? String ?: ""

            val realtimeStatus = if (realtime) "realtime" else "timetable"

            // Build the departure line
            val timeStr = if (estimatedTime != null && estimatedTime != plannedTime) {
                val delayStr = if (delay > 0) "+$delay min" else "$delay min"
                "$plannedTime ($estimatedTime, $delayStr)"
            } else {
                plannedTime
            }

            formatted += "${index + 1}. $line $transportType to $destination at $timeStr | Platform $platform ($realtimeStatus)\n"
        }

        formatted
    }.getOrElse {
        logger.error(it) { "Exception fetching departures" }
        "Error fetching departures for $stationName: ${it.message}"
    }

    /**
     * Fetch journey plans with detailed steps between two public transport stations.
     */
    @Suppress("UNUSED")
    @Tool("Fetch journey plans with detailed steps between two public transport stations")
    fun getJourneyOptions(
        @P("The starting station name or identifier (e.g., 'Essen Hauptbahnhof' or 'de:2892')")
        origin: String,
        @P("The destination station name or identifier (same format as origin)")
        destination: String,
        @P("Maximum number of journey options to return (default: 3, minimum: 1)")
        limit: Int = 3,
        @P("Optional intermediate station to route through")
        via: String? = null
    ): String = runCatching {
        if (origin.isBlank() || destination.isBlank()) {
            return "Origin and destination are both required to search for journeys."
        }

        val resolvedOrigin = resolveStationIdentifier(origin)
        val resolvedDestination = resolveStationIdentifier(destination)
        val resolvedVia = if (!via.isNullOrBlank()) resolveStationIdentifier(via) else null

        val journeys = efaService.getJourneys(
            origin = resolvedOrigin,
            destination = resolvedDestination,
            originType = inferStationType(resolvedOrigin),
            destinationType = inferStationType(resolvedDestination),
            via = resolvedVia,
            viaType = if (resolvedVia != null) inferStationType(resolvedVia) else "any",
            limit = maxOf(limit, 1)
        )

        if (journeys.isEmpty()) {
            val viaStr = if (!via.isNullOrBlank()) " via $via" else ""
            return "No journeys found from $origin to $destination$viaStr."
        }

        var formatted = "Journeys from $origin to $destination"
        if (!via.isNullOrBlank()) {
            formatted += " via $via"
        }
        formatted += ":\n"

        journeys.forEachIndexed { journeyIdx, journey ->
            val length = journey.lengthMinutes
            formatted += "\nOPTION ${journeyIdx + 1}: Total duration $length minutes\n"

            journey.steps.forEachIndexed { stepIdx, step ->
                val mode = step.mode
                val line = step.line
                val originName = step.origin
                val destinationName = step.destination
                val dep = step.departurePlanned
                val depEst = step.departureEstimated
                val arr = step.arrivalPlanned
                val arrEst = step.arrivalEstimated
                val depDelay = step.departureDelayMinutes
                val arrDelay = step.arrivalDelayMinutes
                val platformDep = step.platformOrigin
                val platformArr = step.platformDestination
                val duration = step.durationMinutes

                formatted += "\nStep ${stepIdx + 1}:\n"

                // Transport line information
                if (!line.isNullOrBlank()) {
                    formatted += "  Line: $mode $line\n"
                } else {
                    formatted += "  Mode: $mode\n"
                }

                // Check if origin and destination are the same (walk within station)
                if (originName == destinationName) {
                    formatted += "  Location: $originName\n"
                    formatted += "  Action: Walk to another platform or transfer point in $originName\n"
                } else {
                    formatted += "  From: $originName"
                    if (!platformDep.isNullOrBlank()) {
                        formatted += " (Platform $platformDep)"
                    }
                    formatted += "\n"
                    formatted += "  To: $destinationName"
                    if (!platformArr.isNullOrBlank()) {
                        formatted += " (Platform $platformArr)"
                    }
                    formatted += "\n"
                }

                // Departure time
                if (!dep.isNullOrBlank()) {
                    formatted += "  Depart: $dep"
                    if (!depEst.isNullOrBlank() && depEst != dep) {
                        val delayStr = if (depDelay != null && depDelay > 0) "+$depDelay" else "$depDelay"
                        formatted += " → Estimated: $depEst ($delayStr min delay)"
                    }
                    formatted += "\n"
                }

                // Arrival time
                if (!arr.isNullOrBlank()) {
                    formatted += "  Arrive: $arr"
                    if (!arrEst.isNullOrBlank() && arrEst != arr) {
                        val delayStr = if (arrDelay != null && arrDelay > 0) "+$arrDelay" else "$arrDelay"
                        formatted += " → Estimated: $arrEst ($delayStr min delay)"
                    }
                    formatted += "\n"
                }

                // Duration
                if (duration > 0) {
                    formatted += "  Duration: $duration minutes\n"
                }
            }
        }

        formatted.trim()
    }.getOrElse {
        logger.error(it) { "Exception fetching journeys" }
        "Error fetching journeys from $origin to $destination: ${it.message}"
    }

    // ==================== Helper Methods ====================

    private fun resolveStationIdentifier(nameOrId: String): String {
        if (nameOrId.isBlank()) {
            return nameOrId
        }

        val lowered = nameOrId.lowercase()
        if (lowered.startsWith("de:") || lowered.startsWith("coord:")) {
            return nameOrId
        }

        // Try to resolve station name to ID
        val stationId = efaService.getStationId(nameOrId)
        return stationId ?: nameOrId
    }

    private fun inferStationType(identifier: String): String {
        if (identifier.isBlank()) {
            return "any"
        }

        val lowered = identifier.lowercase()
        return when {
            lowered.startsWith("de:") -> "stop"
            lowered.startsWith("coord:") -> "coord"
            else -> "any"
        }
    }
}

