"""Alerts models."""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional

from ..definitions import LanguageID


class AlertType(str, Enum):
    """Alert type."""

    Generic = 'alert'
    Wind = 'wind'
    SnowIce = 'snow-ice'
    Thunderstorm = 'thunderstorm'
    Fog = 'fog'
    HighTemperature = 'high-temperature'
    LowTemperature = 'low-temperature'
    CoastalEvent = 'coastalevent'
    ForestFire = 'forest-fire'
    Avalanches = 'avalanches'
    Rain = 'rain'
    Flooding = 'flooding'
    RainFlood = 'rain-flood'


class AlertResponseType(str, Enum):
    """Alert response type."""

    Shelter = 'shelter'  # Take shelter in place or per instructions
    Evacuate = 'evacuate'  # Relocate as instructed in instructions
    Prepare = 'prepare'  # Make preparations per instructions
    Execute = 'execute'  # Execute a pre-planned activity identified in instructions
    Avoid = 'avoid'  # Avoid the subject event as per instructions
    Monitor = 'monitor'  # Attend to information sources as described in instructions
    AllClear = 'allclear'  # The subject event no longer poses a threat or concern and
    # any follow on action is described in instructions
    NoResponse = 'none'  # No recommended action


class AlertUrgency(str, Enum):
    """Alert urgency."""

    Immediate = 'immediate'  # Responsive action should be taken immediately.
    Expected = 'expected'  # Responsive action should be taken within the next hour.
    Future = 'future'  # Responsive action should be taken in the near future.
    Past = 'past'  # Responsive action no longer required.


class AlertSeverity(str, Enum):
    """Alert severity."""

    Minor = 'minor'  # green
    Moderate = 'moderate'  # yellow
    Severe = 'severe'  # orange
    Extreme = 'extreme'  # red


class AlertCertainty(str, Enum):
    """Alert certainty."""

    Observed = 'observed'
    Likely = 'likely'  # p > 50 %
    Possible = 'possible'  # p < 50 %
    Unlikely = 'unlikely'  # p < 5 %


class AlertArea(BaseModel):
    """Weather alert area model."""

    id: str = Field(..., example='SI801')
    name: str = Field(..., example='Obala Slovenije')

    class Config:
        """Weather alert area model config."""

        title: str = 'Alert area'


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
            ]
        ],
    )

    def base(self) -> AlertArea:
        """Return an instance of AlertArea."""
        return self.copy(exclude={'polygons'})

    class Config:
        """Weather alert area model with polygon(s) config."""

        title: str = 'Alert area with polygons'


class AlertInfo(BaseModel):
    """Weather alert info model."""

    id: str = Field(
        ...,
        title='Identifier',
        example=(
            '2.49.0.0.276.0.DWD.PVW.1645128360000'
            '.42042cce-2a7e-43ae-a64c-3fb693ea1495.MUL'
        ),
    )

    type: AlertType = Field(..., example=AlertType.Wind)
    urgency: AlertUrgency = Field(..., example=AlertUrgency.Immediate)
    severity: AlertSeverity = Field(..., example=AlertSeverity.Moderate)
    certainty: AlertCertainty = Field(..., example=AlertCertainty.Likely)
    response_type: AlertResponseType = Field(..., example=AlertResponseType.Prepare)

    onset: str = Field(..., example='1645286400000')
    ending: str = Field(..., example='1645311600000')

    event: str = Field(..., example='wind gusts')
    headline: str = Field(..., example='Official WARNING of WIND GUSTS')
    description: Optional[str] = Field(
        None,
        example=(
            'There is a risk of wind gusts (level 1 of 4).\n'
            'Max. gusts: ~ 60 km/h; Wind direction: south-west; '
            'Increased gusts: in exposed locations < 70 km/h'
        ),
    )
    instructions: Optional[str] = Field(
        None,
        example=(
            'NOTE: Be aware of the following possible dangers: '
            'Twigs or branches could fall down. Watch out for falling debris.'
        ),
    )

    class Config:
        """Weather alert extended info model config."""

        title: str = 'Alert information'


class AlertInfoExtended(AlertInfo):
    """Weather alert extended info model."""

    areas: list[AlertArea] = Field(..., example=[])
    sender_name: Optional[str] = Field(None, example='Deutscher Wetterdienst')
    web: Optional[str] = Field(None, example='https://www.wettergefahren.de')

    @classmethod
    def init(
        cls,
        dictionary: dict[str, Any],
        language: LanguageID,
        areas: dict[str, AlertAreaWithPolygon],
        **kwargs: Any,
    ) -> 'AlertInfoExtended':
        """Initialise from a dictionary."""
        lang: str = language.value
        en: str = LanguageID.English.value

        # translatable values
        kwargs.setdefault(
            'event',
            dictionary['event'][lang]
            if lang in dictionary['event']
            else dictionary['event'][en],
        )

        kwargs.setdefault(
            'headline',
            dictionary['headline'][lang]
            if lang in dictionary['headline']
            else dictionary['headline'][en],
        )

        if dictionary['description']:
            kwargs.setdefault(
                'description',
                dictionary['description'][lang]
                if lang in dictionary['description']
                else dictionary['description'][en],
            )

        if dictionary['instructions']:
            kwargs.setdefault(
                'instructions',
                dictionary['instructions'][lang]
                if lang in dictionary['instructions']
                else dictionary['instructions'][en],
            )

        if dictionary['sender_name']:
            kwargs.setdefault(
                'sender_name',
                dictionary['sender_name'][lang]
                if lang in dictionary['sender_name']
                else dictionary['sender_name'][en],
            )

        if dictionary['web']:
            kwargs.setdefault(
                'web',
                dictionary['web'][lang]
                if lang in dictionary['web']
                else dictionary['web'][en],
            )

        # areas
        areas_list = dictionary['areas']
        areas_list.sort()
        areas_objs = [areas[a].base() for a in areas_list]

        kwargs.setdefault('areas', areas_objs)

        # init
        return cls(
            id=dictionary['key'],
            type=dictionary['type'],
            urgency=dictionary['urgency'],
            severity=dictionary['severity'],
            certainty=dictionary['certainty'],
            response_type=dictionary['response_type'],
            onset=dictionary['onset'],
            ending=dictionary['expires'],
            **kwargs,
        )

    class Config:
        """Weather alert extended info model config."""

        title: str = 'Alert extended information'
