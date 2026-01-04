package eu.sendzik.yume.client

import eu.sendzik.yume.service.efa.model.EfaDeparturesResponse
import eu.sendzik.yume.service.efa.model.EfaJourneyResponse
import eu.sendzik.yume.service.efa.model.EfaServingLinesResponse
import eu.sendzik.yume.service.efa.model.EfaStopFinderResponse
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.service.annotation.GetExchange

interface EfaClient {

    @GetExchange("/XML_STOPFINDER_REQUEST")
    fun stopFinderRequest(
        @RequestParam params: Map<String, String>
    ): EfaStopFinderResponse?

    @GetExchange("/XML_SERVINGLINES_REQUEST")
    fun servingLinesRequest(
        @RequestParam params: Map<String, String>
    ): EfaServingLinesResponse?

    @GetExchange("/XML_DM_REQUEST")
    fun departuresRequest(
        @RequestParam params: Map<String, String>
    ): EfaDeparturesResponse?

    @GetExchange("/XML_TRIP_REQUEST2")
    fun tripRequest(
        @RequestParam params: Map<String, String>
    ): EfaJourneyResponse?
}