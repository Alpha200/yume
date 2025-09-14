from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherForecast:
    """A single weather forecast entry."""
    datetime: str
    condition: str
    temperature: Optional[float] = None
    wind_speed: Optional[float] = None
