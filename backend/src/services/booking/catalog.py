from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import Any

from src.services.booking.common import iso, new_id
from src.services.booking.errors import BookingError
from src.services.booking.location import Coordinates, HaversineMapProvider

def _to_vietnam_time(iso_str: str) -> datetime:
    if iso_str.endswith("Z"):
        return datetime.fromisoformat(iso_str[:-1]).replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=7)))
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=7)))
    return dt.astimezone(timezone(timedelta(hours=7)))


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
            raise BookingError("VEHICLE_NOT_FOUND", "KhÃ´ng tÃ¬m tháº¥y máº«u xe.")
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
        limit: int = 5,
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
                raise BookingError("VEHICLE_NOT_FOUND", "KhÃ´ng tÃ¬m tháº¥y phiÃªn báº£n xe.")
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
                    raise BookingError(
                        "SHOWROOM_NOT_FOUND", "KhÃ´ng tÃ¬m tháº¥y showroom theo tÃªn hoáº·c Ä‘á»‹a chá»‰."
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
                    showrooms = [showroom for score, showroom in ranked if score > 0]
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
            values: list[Any] = [showroom_id, *variant_ids, iso(self.now())]
            date_sql, order_sql = "", "s.start_at"
            if preferred_date:
                date_sql = " AND substr(s.start_at,1,10)=?"
                values.append(preferred_date)
            if preferred_time:
                if not isinstance(preferred_time, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", preferred_time):
                    raise BookingError("INVALID_INPUT", "Preferred time must be a valid HH:MM value.")
                hour, minute = (int(x) for x in preferred_time.split(":"))
                target = hour * 60 + minute
                order_sql = f"ABS((CAST(substr(s.start_at,12,2) AS INTEGER)*60 + CAST(substr(s.start_at,15,2) AS INTEGER)) - {target}), s.start_at"
            slots = [
                dict(r)
                for r in c.execute(
                    f"SELECT s.*,d.asset_code,v.name variant_name FROM test_drive_slots s JOIN demo_vehicles d ON d.id=s.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id WHERE s.showroom_id=? AND d.variant_id IN ({marks}) AND s.status='available' AND s.start_at>? AND d.is_active=1 AND d.operational_status='available' AND d.battery_soc IS NOT NULL AND d.battery_soc>=d.minimum_booking_soc {date_sql} ORDER BY {order_sql} LIMIT ?",
                    (*values, min(limit, 5)),
                )
            ]
            WEEKDAYS_VI = {
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
                day_label = WEEKDAYS_VI[dt_start.weekday()]
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

        def normalize(value: str) -> set[str]:
            ascii_value = unicodedata.normalize("NFD", value.casefold())
            ascii_value = "".join(character for character in ascii_value if unicodedata.category(character) != "Mn")
            tokens = set(re.findall(r"[a-z0-9]+", ascii_value.replace("đ", "d")))
            ignored = {
                "duong",
                "phuong",
                "xa",
                "quan",
                "huyen",
                "thi",
                "tran",
                "thanh",
                "pho",
                "tp",
                "so",
            }
            return {token for token in tokens if token not in ignored and (len(token) > 1 or token.isdigit())}

        requested = normalize(address)
        candidate = normalize(f"{showroom.get('name', '')} {showroom.get('address', '')}")
        return len(requested & candidate)
