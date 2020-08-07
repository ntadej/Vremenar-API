"""Common models and data structures."""


class Coordinate:
    """Coordinate model."""

    def __init__(self, latitude: float, longitude: float):
        """Initialise coordinate model."""
        self.latitude: float = latitude
        self.longitude: float = longitude
