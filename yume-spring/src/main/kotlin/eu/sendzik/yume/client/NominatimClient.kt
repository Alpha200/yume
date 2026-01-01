package eu.sendzik.yume.client

import eu.sendzik.yume.client.model.NominatimReverseGeocodeResult
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.service.annotation.GetExchange
import org.springframework.web.service.annotation.HttpExchange

@HttpExchange
interface NominatimClient {
    @GetExchange("reverse")
    fun reverseGeocode(
        @RequestParam("lat") latitude: Double,
        @RequestParam("lon") longitude: Double,
        @RequestParam("format") format: String = "jsonv2",
    ): NominatimReverseGeocodeResult
}