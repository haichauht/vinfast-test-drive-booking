import math
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


class MapProvider(Protocol):
    def distances_km(self, origin: Coordinates, destinations: list[Coordinates]) -> list[float]: ...


class HaversineMapProvider:
    """Offline fallback that calculates straight-line distance."""

    @staticmethod
    def distance_km(origin: Coordinates, destination: Coordinates) -> float:
        lat1 = math.radians(origin.latitude)
        lat2 = math.radians(destination.latitude)
        longitude_delta = math.radians(destination.longitude - origin.longitude)
        value = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(longitude_delta / 2) ** 2
        return 6371 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))

    def distances_km(self, origin: Coordinates, destinations: list[Coordinates]) -> list[float]:
        return [self.distance_km(origin, destination) for destination in destinations]
