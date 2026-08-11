from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.services.booking.common import iso
from src.services.booking.errors import BookingError
from src.services.booking.location import Coordinates, HaversineMapProvider
from src.services.booking.location_normalizer import normalize_location_tokens

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
_SHOWROOM_TOKEN_CACHE: dict[str, tuple[tuple[str, str, str], frozenset[str]]] = {}


def _showroom_location_tokens(showroom: dict) -> frozenset[str]:
    """Return cached tokens; an updated showroom naturally gets a new cache key."""
    showroom_id = str(showroom.get("id", ""))
    version = (
        str(showroom.get("updated_at", "")),
        str(showroom.get("name", "")),
        str(showroom.get("address", "")),
    )
    cached = _SHOWROOM_TOKEN_CACHE.get(showroom_id)
    if cached is None or cached[0] != version:
        tokens = frozenset(normalize_location_tokens(f"{version[1]} {version[2]}"))
        _SHOWROOM_TOKEN_CACHE[showroom_id] = (version, tokens)
        return tokens
    return cached[1]


def _to_vietnam_time(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(VIETNAM_TZ)


class CatalogService:
    def list_active_vehicle_models(self) -> list[dict]:
        with self.db.connect() as c:
            models = [dict(row) for row in c.execute("SELECT * FROM vehicle_models WHERE is_active=1 ORDER BY code")]
            for model in models:
                model["variants"] = [
                    dict(row)
                    for row in c.execute(
                        "SELECT * FROM vehicle_variants WHERE model_id=? AND is_active=1 ORDER BY code", (model["id"],)
                    )
                ]
            return models

    def list_active_variants(self, model_id: str) -> list[dict]:
        with self.db.connect() as c:
            if not c.execute("SELECT 1 FROM vehicle_models WHERE id=? AND is_active=1", (model_id,)).fetchone():
                raise BookingError("MODEL_NOT_FOUND", "Không tìm thấy mẫu xe.")
            return [
                dict(row)
                for row in c.execute(
                    "SELECT * FROM vehicle_variants WHERE model_id=? AND is_active=1 ORDER BY code", (model_id,)
                )
            ]

    def list_active_showrooms(self) -> list[dict]:
        with self.db.connect() as c:
            return [dict(row) for row in c.execute("SELECT * FROM showrooms WHERE is_active=1 ORDER BY code")]

    def resolve_vehicle_model(self, query: str) -> dict:
        with self.db.connect() as c:
            row = c.execute(
                "SELECT * FROM vehicle_models WHERE is_active=1 AND (lower(code)=lower(?) OR lower(name)=lower(?))",
                (query, query),
            ).fetchone()
            if not row:
                row = c.execute(
                    "SELECT * FROM vehicle_models WHERE is_active=1 AND lower(name) LIKE lower(?) ORDER BY name LIMIT 1",
                    (f"%{query}%",),
                ).fetchone()
        if not row:
            raise BookingError("VEHICLE_NOT_FOUND", "Không tìm thấy mẫu xe.")
        return dict(row)

    def search_options(
        self,
        *,
        vehicle_model: str,
        vehicle_variant: str | None = None,
        showroom_id: str | None = None,
        showroom_query: str | None = None,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        preferred_date: str | None = None,
        preferred_time: str | None = None,
        limit: int = 24,
        **_: Any,
    ) -> dict:
        if (latitude is None) != (longitude is None):
            raise BookingError("INVALID_INPUT", "Latitude và longitude phải được cung cấp cùng nhau.")
        model = self.resolve_vehicle_model(vehicle_model)
        params: list[Any] = [model["id"]]
        variant_sql = ""
        if vehicle_variant:
            variant_sql = " AND (lower(v.code)=lower(?) OR lower(v.name)=lower(?))"
            params += [vehicle_variant, vehicle_variant]
        with self.db.connect() as c:
            variants = [
                dict(r)
                for r in c.execute(
                    "SELECT v.* FROM vehicle_variants v WHERE v.model_id=? AND v.is_active=1" + variant_sql, params
                )
            ]
            if vehicle_variant and not variants:
                raise BookingError("VEHICLE_NOT_FOUND", "Không tìm thấy phiên bản xe.")
            variant_ids = [v["id"] for v in variants]
            if not variant_ids:
                return {
                    "resolved_vehicle": model,
                    "license_requirement": model["required_license_class"],
                    "showrooms": [],
                    "slots": [],
                    "search_stage": "showroom_selection",
                    "missing_fields": [],
                }
            marks = ",".join("?" * len(variant_ids))
            if not showroom_id and showroom_query:
                showroom = c.execute(
                    "SELECT id FROM showrooms WHERE is_active=1 AND (lower(code)=lower(?) OR lower(name)=lower(?) OR lower(name) LIKE lower(?) OR lower(address) LIKE lower(?)) ORDER BY CASE WHEN lower(name)=lower(?) THEN 0 ELSE 1 END,name LIMIT 1",
                    (showroom_query, showroom_query, f"%{showroom_query}%", f"%{showroom_query}%", showroom_query),
                ).fetchone()
                if not showroom:
                    candidates = [
                        dict(row)
                        for row in c.execute("SELECT * FROM showrooms WHERE is_active=1").fetchall()
                    ]
                    ranked = sorted(
                        ((self._address_match_score(showroom_query, candidate), candidate) for candidate in candidates),
                        key=lambda item: item[0],
                        reverse=True,
                    )
                    showroom = next((candidate for score, candidate in ranked if score > 0), None)
                if not showroom:
                    raise BookingError(
                        "SHOWROOM_NOT_FOUND", "Không tìm thấy showroom theo tên hoặc địa chỉ."
                    )
                showroom_id = showroom["id"]
            if not showroom_id:
                rows = c.execute(
                    f"SELECT DISTINCT s.* FROM showrooms s JOIN demo_vehicles d ON d.showroom_id=s.id WHERE s.is_active=1 AND d.is_active=1 AND d.operational_status='available' AND d.battery_soc IS NOT NULL AND d.battery_soc>=d.minimum_booking_soc AND d.variant_id IN ({marks})",
                    variant_ids,
                ).fetchall()
                showrooms = [dict(r) for r in rows]
                if address:
                    ranked = sorted(
                        ((self._address_match_score(address, showroom), showroom) for showroom in showrooms),
                        key=lambda item: item[0],
                        reverse=True,
                    )
                    matched = [(score, showroom) for score, showroom in ranked if score > 0]
                    showrooms = [showroom for _, showroom in matched]
                if latitude is not None and longitude is not None:
                    origin = Coordinates(latitude, longitude)
                    destinations = [Coordinates(s["latitude"], s["longitude"]) for s in showrooms]
                    for s, distance in zip(
                        showrooms, self.map_provider.distances_km(origin, destinations), strict=True
                    ):
                        s["distance_km"] = round(distance, 2)
                    showrooms.sort(key=lambda x: x["distance_km"])
                return {
                    "resolved_vehicle": {**model, "variants": variants},
                    "license_requirement": model["required_license_class"],
                    "showrooms": showrooms[:limit],
                    "slots": [],
                    "search_stage": "showroom_selection",
                    "missing_fields": [],
                }
            selected = self._row(
                c.execute("SELECT * FROM showrooms WHERE id=? AND is_active=1", (showroom_id,)).fetchone()
            )
            if not selected:
                raise BookingError("SHOWROOM_NOT_FOUND", "Showroom not found.")
            now = iso(self.now())
            # Slot timestamps in the dataset may carry a local UTC offset (for
            # example +07:00) while `now` is stored as UTC. Comparing those ISO
            # strings lexicographically can make an already-past local slot look
            # newer than the UTC value. Normalize both operands in SQL instead.
            future_slot_sql = (
                "s.start_at::timestamptz > ?::timestamptz"
                if c.dialect == "postgres"
                else "datetime(s.start_at) > datetime(?)"
            )
            values: list[Any] = [showroom_id, *variant_ids, now, now]
            date_sql, order_sql = "", "s.start_at"
            if preferred_date:
                date_sql = " AND substr(s.start_at,1,10)=?"
                values.append(preferred_date)
            if preferred_time:
                if not isinstance(preferred_time, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", preferred_time):
                    raise BookingError("INVALID_INPUT", "Preferred time must be a valid HH:MM value.")
                hour, minute = (int(x) for x in preferred_time.split(":"))
                target = hour * 60 + minute
                slot_minutes_sql = (
                    "(EXTRACT(HOUR FROM s.start_at::timestamptz AT TIME ZONE 'Asia/Ho_Chi_Minh') * 60 "
                    "+ EXTRACT(MINUTE FROM s.start_at::timestamptz AT TIME ZONE 'Asia/Ho_Chi_Minh'))"
                    if c.dialect == "postgres"
                    else "(CAST(strftime('%H', datetime(s.start_at, '+7 hours')) AS INTEGER) * 60 "
                    "+ CAST(strftime('%M', datetime(s.start_at, '+7 hours')) AS INTEGER))"
                )
                order_sql = f"ABS({slot_minutes_sql} - ?), s.start_at"
                values.append(target)
            slots = [
                dict(r)
                for r in c.execute(
                    f"SELECT s.*,d.asset_code,v.name variant_name FROM test_drive_slots s JOIN demo_vehicles d ON d.id=s.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id WHERE s.showroom_id=? AND d.variant_id IN ({marks}) AND (s.status IN ('available','booked') OR (s.status='held' AND s.held_until>?)) AND {future_slot_sql} AND d.is_active=1 AND d.operational_status='available' AND d.battery_soc IS NOT NULL AND d.battery_soc>=d.minimum_booking_soc {date_sql} ORDER BY {order_sql} LIMIT ?",
                    (*values, min(max(limit, 1), 30)),
                )
            ]
            weekdays_vi = {
                0: "Thứ 2",
                1: "Thứ 3",
                2: "Thứ 4",
                3: "Thứ 5",
                4: "Thứ 6",
                5: "Thứ 7",
                6: "Chủ nhật"
            }
            for s in slots:
                dt_start = _to_vietnam_time(s["start_at"])
                dt_end = _to_vietnam_time(s["end_at"])
                s["start_at"] = dt_start.isoformat()
                s["end_at"] = dt_end.isoformat()
                day_label = weekdays_vi[dt_start.weekday()]
                date_str = dt_start.strftime("%d/%m")
                time_str = dt_start.strftime("%H:%M")
                s["formatted_schedule"] = f"{day_label}, {date_str} {time_str}"
        return {
            "resolved_vehicle": {**model, "variants": variants},
            "license_requirement": model["required_license_class"],
            "selected_showroom": selected,
            "showrooms": [],
            "slots": slots,
            "search_stage": "slot_selection",
            "missing_fields": [],
        }

    @staticmethod
    def _distance(a, b, c, d):
        return HaversineMapProvider.distance_km(Coordinates(a, b), Coordinates(c, d))

    @staticmethod
    def _address_match_score(address: str, showroom: dict) -> int:
        """Rank available showrooms by locality tokens without a remote geocoder."""

        requested = normalize_location_tokens(address)
        candidate = _showroom_location_tokens(showroom)
        return len(requested & candidate)
