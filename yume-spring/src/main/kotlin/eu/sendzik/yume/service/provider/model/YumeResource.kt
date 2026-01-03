package eu.sendzik.yume.service.provider.model

import eu.sendzik.yume.agent.model.YumeChatResource
import eu.sendzik.yume.service.provider.model.YumeResource.DAY_PLAN_TODAY
import eu.sendzik.yume.service.provider.model.YumeResource.DAY_PLAN_TOMORROW
import eu.sendzik.yume.service.provider.model.YumeResource.WEATHER_FORECAST

enum class YumeResource {
    LOCATION,
    WEATHER_FORECAST,
    DAY_PLAN_TODAY,
    DAY_PLAN_TOMORROW,
    USER_LANGUAGE,
    CURRENT_DATE_TIME,
    CALENDAR_NEXT_2_DAYS,
    SUMMARIZED_PREFERENCES,
    SUMMARIZED_OBSERVATIONS,
    SUMMARIZED_REMINDERS,
}

fun YumeChatResource.toYumeResource(): YumeResource {
    return when (this) {
        YumeChatResource.WEATHER_FORECAST -> WEATHER_FORECAST
        YumeChatResource.DAY_PLAN_TODAY -> DAY_PLAN_TODAY
        YumeChatResource.DAY_PLAN_TOMORROW -> DAY_PLAN_TOMORROW
    }
}