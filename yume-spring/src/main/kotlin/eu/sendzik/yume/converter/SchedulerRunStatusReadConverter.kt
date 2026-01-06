package eu.sendzik.yume.converter

import eu.sendzik.yume.repository.scheduler.model.SchedulerRunStatus
import org.springframework.core.convert.converter.Converter
import org.springframework.data.convert.ReadingConverter

@ReadingConverter
class SchedulerRunStatusReadConverter : Converter<String, SchedulerRunStatus?> {
    override fun convert(source: String): SchedulerRunStatus? {
        return SchedulerRunStatus.entries.firstOrNull { it.value == source }
    }
}