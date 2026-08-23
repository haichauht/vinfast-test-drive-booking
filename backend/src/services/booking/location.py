import functools
import json
import math
import urllib.parse
import urllib.request
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


def _fetch_nominatim_coordinates(query_str: str) -> Coordinates | None:
    # 1. Thử qua Photon Geocoder (OpenStreetMap engine phản hồi nhanh và ổn định)
    photon_url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(query_str)}&limit=1"
    req_photon = urllib.request.Request(
        photon_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VinFast/1.0"}
    )
    try:
        with urllib.request.urlopen(req_photon, timeout=6) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            features = data.get("features", [])
            if features and len(features) > 0:
                coords = features[0]["geometry"]["coordinates"]
                return Coordinates(latitude=float(coords[1]), longitude=float(coords[0]))
    except Exception:
        pass

    # 2. Dự phòng qua Nominatim OSM server
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query_str)}&countrycodes=vn&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "VinFast-Booking-Agent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                return Coordinates(latitude=float(data[0]["lat"]), longitude=float(data[0]["lon"]))
    except Exception:
        pass
    return None


PROVINCE_COORDINATES: dict[str, tuple[float, float]] = {
    "bắc giang": (21.2731, 106.1946),
    "bac giang": (21.2731, 106.1946),
    "bắc ninh": (21.1861, 106.0763),
    "bac ninh": (21.1861, 106.0763),
    "hà nội": (21.0285, 105.8542),
    "ha noi": (21.0285, 105.8542),
    "hồ chí minh": (10.7769, 106.7009),
    "ho chi minh": (10.7769, 106.7009),
    "hải phòng": (20.8449, 106.6881),
    "hai phong": (20.8449, 106.6881),
    "đà nẵng": (16.0544, 108.2022),
    "da nang": (16.0544, 108.2022),
    "cần thơ": (10.0452, 105.7469),
    "can tho": (10.0452, 105.7469),
    "quảng ninh": (20.9599, 107.0425),
    "thanh hóa": (19.8067, 105.7851),
    "nghệ an": (18.6734, 105.6813),
    "thừa thiên huế": (16.4637, 107.5909),
    "huế": (16.4637, 107.5909),
    "lạng sơn": (21.8474, 106.7583),
    "thái nguyên": (21.5928, 105.8442),
    "phú thọ": (21.3228, 105.4019),
    "vĩnh phúc": (21.3089, 105.6049),
    "hải dương": (20.9373, 106.3146),
    "hưng yên": (20.6464, 106.0511),
    "thái bình": (20.4463, 106.3365),
    "nam định": (20.4200, 106.1683),
    "ninh bình": (20.2506, 105.9744),
    "hà nam": (20.5452, 105.9126),
    "hoà bình": (20.8172, 105.3378),
    "sơn la": (21.3257, 103.9188),
    "lai châu": (22.3963, 103.4588),
    "điện biên": (21.3860, 103.0230),
    "lào cai": (22.4854, 103.9707),
    "yên bái": (21.7051, 104.8753),
    "hà giang": (22.8233, 104.9839),
    "tuyên quang": (21.8236, 105.2158),
    "cao bằng": (22.6658, 106.2573),
    "bắc kạn": (22.1481, 105.8347),
    "quảng bình": (17.4764, 106.5985),
    "quảng trị": (16.7454, 107.1853),
    "quảng nam": (15.5736, 108.4740),
    "quảng ngãi": (15.1205, 108.7924),
    "bình định": (13.7830, 109.2197),
    "phú yên": (13.0882, 109.0924),
    "khánh hòa": (12.2388, 109.1967),
    "ninh thuận": (11.5653, 108.9882),
    "bình thuận": (10.9333, 108.1000),
    "kon tum": (14.3497, 108.0004),
    "gia lai": (13.9833, 108.0000),
    "đắk lắk": (12.6667, 108.0500),
    "đắk nông": (12.0000, 107.6833),
    "lâm đồng": (11.9404, 108.4583),
    "bình phước": (11.5333, 106.8833),
    "tây ninh": (11.3000, 106.1000),
    "bình dương": (11.1667, 106.6500),
    "đồng nai": (10.9500, 106.8167),
    "bà rịa vũng tàu": (10.5000, 107.1667),
    "vũng tàu": (10.3460, 107.0843),
    "long an": (10.5333, 106.4000),
    "tiền giang": (10.4167, 106.3667),
    "bến tre": (10.2333, 106.3833),
    "trà vinh": (9.9333, 106.3333),
    "vĩnh long": (10.2500, 105.9667),
    "đồng tháp": (10.4667, 105.6333),
    "an giang": (10.3833, 105.4333),
    "kiên giang": (10.0167, 105.0833),
    "hậu giang": (9.7833, 105.4667),
    "sóc trăng": (9.6000, 105.9833),
    "bạc liêu": (9.2833, 105.7167),
    "cà mau": (9.1769, 105.1500),
}

LOCALITY_COORDINATES: dict[str, tuple[float, float]] = {
    # Deterministic fallback for common booking localities. This also keeps
    # local/test behavior useful when the external geocoder is unavailable.
    "quận 7": (10.7340, 106.7210),
    "quan 7": (10.7340, 106.7210),
}


@functools.lru_cache(maxsize=512)
def resolve_address_coordinates(address: str) -> Coordinates | None:
    if not address:
        return None
    clean_addr = address.strip()
    normalized = clean_addr.lower()

    # 1. Nếu từ khóa tra cứu trùng khớp hoàn toàn tên Tỉnh / Thành phố chính (0ms L1 memory lookup)
    if normalized in PROVINCE_COORDINATES:
        lat, lon = PROVINCE_COORDINATES[normalized]
        return Coordinates(latitude=lat, longitude=lon)
    if normalized in LOCALITY_COORDINATES:
        lat, lon = LOCALITY_COORDINATES[normalized]
        return Coordinates(latitude=lat, longitude=lon)

    # 2. Ưu tiên Dynamic Geocoding (OpenStreetMap API với timeout 10s)
    coords = _fetch_nominatim_coordinates(clean_addr)
    if coords:
        return coords

    if "," in clean_addr:
        space_addr = clean_addr.replace(",", " ")
        coords = _fetch_nominatim_coordinates(space_addr)
        if coords:
            return coords
        parts = [p.strip() for p in clean_addr.split(",") if p.strip()]
        for part in parts:
            coords = _fetch_nominatim_coordinates(part)
            if coords:
                return coords

    # 3. Fallback L1: Nếu API không trả về kết quả, mới quét tên Tỉnh / Thành phố lân cận
    for key, (lat, lon) in PROVINCE_COORDINATES.items():
        if key in normalized:
            return Coordinates(latitude=lat, longitude=lon)

    return None
