"""Alerts models."""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any


class AlertType(str, Enum):
    """Alert type."""

    Generic = "alert"
    Wind = "wind"
    SnowIce = "snow-ice"
    Thunderstorm = "thunderstorm"
    Fog = "fog"
    HighTemperature = "high-temperature"
    LowTemperature = "low-temperature"
    CoastalEvent = "coastalevent"
    ForestFire = "forest-fire"
    Avalanches = "avalanches"
    Rain = "rain"
    Flooding = "flooding"
    RainFlood = "rain-flood"


class AlertResponseType(str, Enum):
    """Alert response type."""

    Shelter = "shelter"  # Take shelter in place or per instructions
    Evacuate = "evacuate"  # Relocate as instructed in instructions
    Prepare = "prepare"  # Make preparations per instructions
    Execute = "execute"  # Execute a pre-planned activity identified in instructions
    Avoid = "avoid"  # Avoid the subject event as per instructions
    Monitor = "monitor"  # Attend to information sources as described in instructions
    AllClear = "allclear"  # The subject event no longer poses a threat or concern and
    # any follow on action is described in instructions
    NoResponse = "none"  # No recommended action


class AlertUrgency(str, Enum):
    """Alert urgency."""

    Immediate = "immediate"  # Responsive action should be taken immediately.
    Expected = "expected"  # Responsive action should be taken within the next hour.
    Future = "future"  # Responsive action should be taken in the near future.
    Past = "past"  # Responsive action no longer required.


class AlertSeverity(str, Enum):
    """Alert severity."""

    Minor = "minor"  # yellow
    Moderate = "moderate"  # orange
    Severe = "severe"  # red
    Extreme = "extreme"  # violet


class AlertCertainty(str, Enum):
    """Alert certainty."""

    Observed = "observed"
    Likely = "likely"  # p > 50 %
    Possible = "possible"  # p < 50 %
    Unlikely = "unlikely"  # p < 5 %


class AlertArea(BaseModel):
    """Weather alert area model."""

    id: str = Field(..., example="SI801")  # noqa: A003
    name: str = Field(..., example="Obala Slovenije")

    class Config:
        """Weather alert area model config."""

        title: str = "Alert area"


class AlertAreaWithPolygon(AlertArea):
    """Weather alert area model with polygon(s)."""

    polygons: list[list[list[float]]] = Field(
        ...,
        example=[
            [
                [13.725456655646438, 45.6015000758004],
                [13.725431248605672, 45.59967654614104],
                [13.581904223456036, 45.4818292464459],
                [13.579022245313693, 45.48186228804809],
                [13.509123210003622, 45.51205472154453],
                [13.384515640404798, 45.56587815045958],
                [13.628708047547093, 45.63156076582936],
                [13.725456655646438, 45.6015000758004],
            ],
        ],
    )

    def base(self) -> AlertArea:
        """Return an instance of AlertArea."""
        return self.copy(exclude={"polygons"})

    class Config:
        """Weather alert area model with polygon(s) config."""

        title: str = "Alert area with polygons"


class AlertInfo(BaseModel):
    """Weather alert info model."""

    id: str = Field(  # noqa: A003
        ...,
        title="Identifier",
        example=(
            "2.49.0.0.276.0.DWD.PVW.1645128360000"
            ".42042cce-2a7e-43ae-a64c-3fb693ea1495.MUL"
        ),
    )

    type: AlertType = Field(..., example=AlertType.Wind)  # noqa: A003
    urgency: AlertUrgency = Field(..., example=AlertUrgency.Immediate)
    severity: AlertSeverity = Field(..., example=AlertSeverity.Moderate)
    certainty: AlertCertainty = Field(..., example=AlertCertainty.Likely)
    response_type: AlertResponseType = Field(..., example=AlertResponseType.Prepare)

    areas: list[AlertArea] = Field(..., example=[])

    onset: str = Field(..., example="1645286400000")
    ending: str = Field(..., example="1645311600000")

    event: str = Field(..., example="wind gusts")
    headline: str = Field(..., example="Official WARNING of WIND GUSTS")
    description: str | None = Field(
        None,
        example=(
            "There is a risk of wind gusts (level 1 of 4).\n"
            "Max. gusts: ~ 60 km/h; Wind direction: south-west; "
            "Increased gusts: in exposed locations < 70 km/h"
        ),
    )
    instructions: str | None = Field(
        None,
        example=(
            "NOTE: Be aware of the following possible dangers: "
            "Twigs or branches could fall down. Watch out for falling debris."
        ),
    )
    sender_name: str | None = Field(None, example="Deutscher Wetterdienst")
    web: str | None = Field(None, example="https://www.wettergefahren.de")

    @classmethod
    def init(
        cls,
        info: dict[str, Any],
        localised: dict[str, Any],
        alert_areas: set[str],
        areas: dict[str, AlertAreaWithPolygon] | None = None,
        **kwargs: dict[str, Any] | list[AlertArea],
    ) -> "AlertInfo":
        """Initialise from a dictionary."""
        # translatable values
        kwargs.setdefault(
            "event",
            localised["event"][0].upper() + localised["event"][1:],
        )
        kwargs.setdefault("headline", localised["headline"])

        if "description" in localised and localised["description"]:
            kwargs.setdefault("description", localised["description"])

        if "instructions" in localised and localised["instructions"]:
            kwargs.setdefault("instructions", localised["instructions"])

        if "sender_name" in localised and localised["sender_name"]:
            kwargs.setdefault("sender_name", localised["sender_name"])

        if "web" in localised and localised["web"]:
            kwargs.setdefault("web", localised["web"])

        # areas
        areas_objs = []
        if areas is not None and alert_areas:
            areas_list = list(alert_areas)
            areas_list.sort()
            areas_objs = [areas[a].base() for a in areas_list]
        kwargs.setdefault("areas", areas_objs)

        # init
        return cls(
            id=info["id"],
            type=info["type"],
            urgency=info["urgency"],
            severity=info["severity"],
            certainty=info["certainty"],
            response_type=info["response_type"],
            onset=info["onset"],
            ending=info["expires"],
            **kwargs,
        )

    class Config:
        """Weather alert extended info model config."""

        title: str = "Alert information"
