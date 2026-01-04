package eu.sendzik.yume.utils

import java.time.LocalDate
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

fun formatTimestampForLLM(value: LocalDateTime, timeOnly: Boolean = false): String {
    return value.format(DateTimeFormatter.ofPattern(if (timeOnly) "HH:mm:ss" else "EEEE yyyy-MM-dd HH:mm:ss"))
}

fun formatTimestampForLLM(value: LocalDate): String {
    return value.format(DateTimeFormatter.ofPattern("EEEE yyyy-MM-dd"))
}