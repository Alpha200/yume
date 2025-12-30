package eu.sendzik.yume.client

import eu.sendzik.yume.client.model.OpenWeatherMapOneCallResult
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.service.annotation.GetExchange
import org.springframework.web.service.annotation.HttpExchange

@HttpExchange(accept = ["application/json"])
interface OpenWeatherMapClient {
    @GetExchange("onecall")
    fun oneCall(
        @RequestParam("appid") appId: String,
        @RequestParam("lat") latitude: Double,
        @RequestParam("lon") longitude: Double,
        @RequestParam("units") units: String = "metric",
    ): OpenWeatherMapOneCallResult
}