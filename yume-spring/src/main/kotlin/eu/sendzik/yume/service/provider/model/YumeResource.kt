package eu.sendzik.yume.service.provider.model

import eu.sendzik.yume.agent.model.YumeChatResource

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
    RECENT_SCHEDULER_EXECUTIONS,
    RECENT_GEOFENCE_EVENTS,
    RECENT_USER_INTERACTION,
    RECENT_SPORT_ACTIVITIES,
    USER_HEALTH_SNAPSHOT,
}

fun YumeChatResource.toYumeResource(): YumeResource {
    return when (this) {
        YumeChatResource.WEATHER_FORECAST -> YumeResource.WEATHER_FORECAST
        YumeChatResource.DAY_PLAN_TODAY -> YumeResource.DAY_PLAN_TODAY
        YumeChatResource.DAY_PLAN_TOMORROW -> YumeResource.DAY_PLAN_TOMORROW
        YumeChatResource.USER_HEALTH_SNAPSHOT -> YumeResource.USER_HEALTH_SNAPSHOT
    }
}