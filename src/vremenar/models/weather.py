"""Weather models."""

from pydantic import BaseModel, Field
from typing import Optional

from ..definitions import ObservationType


class WeatherCondition(BaseModel):
    """Weather condition model."""

    observation: ObservationType = Field(..., example=ObservationType.Recent)
    timestamp: str = Field(..., example='1604779200000')
    icon: str = Field(..., example='clear_night')
    temperature: float = Field(..., example=13)
    temperature_low: Optional[float] = Field(None, example=1)

    class Config:
        """Weather condition model config."""

        title: str = 'Weather condition'
