"""Read-only website catalogue and editorial content.

This module is deliberately independent from booking and Agent orchestration so
the public website contract can evolve without registering or invoking tools.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.config import get_settings
from src.models.site import CatalogSnapshot

REVISION = "2026-08-04"


def _media(url: str, alt: str, **extra: Any) -> dict[str, Any]:
    return {"url": url, "alt": alt, **extra}


_VEHICLES: list[dict[str, Any]] = [
    {"id": "vf3", "name": "VF 3", "category": "personal", "bodyType": "Mini eSUV", "seats": 4, "displayPrice": "Giá niêm yết · 299.000.000 VNĐ", "tagline": "Chất riêng trên mọi nẻo đường.", "specs": [("Quãng đường NEDC", "215 km"), ("Công suất tối đa", "32 kW")]},
    {"id": "vf5", "name": "VF 5", "category": "personal", "bodyType": "SUV hạng A", "seats": 5, "displayPrice": "Giá niêm yết · 529.000.000 VNĐ", "tagline": "Sống động từng nhịp phố.", "specs": [("Quãng đường NEDC", "326 km"), ("Công suất tối đa", "100 kW")]},
    {"id": "vf6", "name": "VF 6", "category": "personal", "bodyType": "SUV hạng B", "seats": 5, "displayPrice": "Giá niêm yết · 689.000.000 VNĐ", "tagline": "Mạnh mẽ và tinh tế.", "specs": [("Quãng đường NEDC", "460 km"), ("Công suất tối đa", "150 kW")]},
    {"id": "vf7", "name": "VF 7", "category": "personal", "bodyType": "SUV hạng C", "seats": 5, "displayPrice": "Giá niêm yết · 799.000.000 VNĐ", "tagline": "Dẫn lối đam mê.", "specs": [("Quãng đường WLTP", "431 km"), ("Công suất bản Plus", "260 kW")]},
    {"id": "vf-mpv-7", "name": "VF MPV 7", "category": "personal", "bodyType": "MPV điện gia đình", "seats": 7, "displayPrice": "Giá niêm yết · 750.000.000 VNĐ", "tagline": "Rộng rãi cho cả gia đình.", "specs": [("Quãng đường NEDC", "450 km"), ("Công suất tối đa", "150 kW")]},
    {"id": "vf8", "name": "VF 8", "category": "personal", "bodyType": "SUV hạng D", "seats": 5, "displayPrice": "Giá niêm yết · 1.020.000.000 VNĐ", "tagline": "Cùng bạn bứt phá mọi giới hạn.", "specs": [("Quãng đường bản Eco", "420 km"), ("Công suất bản Plus", "300 kW")]},
    {"id": "vf8-the-he-moi", "name": "VF 8 Thế hệ mới", "category": "personal", "bodyType": "SUV hạng D", "seats": 5, "displayPrice": "Liên hệ", "tagline": "Một nhịp nhìn mới.", "specs": [("Dẫn động", "AWD"), ("Nhiên liệu", "Điện")]},
    {"id": "vf9", "name": "VF 9", "category": "personal", "bodyType": "SUV hạng E", "seats": 7, "displayPrice": "Giá niêm yết · 1.499.000.000 VNĐ", "tagline": "Uy lực và tiện nghi.", "specs": [("Sức chứa", "7 chỗ"), ("Dẫn động", "AWD")]},
    {"id": "herio-green", "name": "Herio Green", "category": "fleet", "bodyType": "eSUV dịch vụ", "seats": 5, "displayPrice": "Chính sách dành cho kinh doanh", "tagline": "Bền bỉ cho nhịp vận hành.", "specs": [("Quãng đường NEDC", "326 km"), ("Công suất", "100 kW")]},
    {"id": "minio-green", "name": "Minio Green", "category": "fleet", "bodyType": "Mini car dịch vụ", "seats": 4, "displayPrice": "Chính sách dành cho kinh doanh", "tagline": "Nhỏ gọn, xoay trở tức thì.", "specs": [("Quãng đường NEDC", "210 km"), ("Công suất", "30 kW")]},
    {"id": "nerio-green", "name": "Nerio Green", "category": "fleet", "bodyType": "eSUV dịch vụ", "seats": 5, "displayPrice": "Chính sách dành cho kinh doanh", "tagline": "Không gian rộng, vận hành gọn.", "specs": [("Quãng đường tham chiếu", "318 km"), ("Công suất", "110 kW")]},
    {"id": "limo-green", "name": "Limo Green", "category": "fleet", "bodyType": "MPV điện dịch vụ", "seats": 7, "displayPrice": "Chính sách dành cho kinh doanh", "tagline": "Rộng rãi cho mọi hành trình.", "specs": [("Quãng đường NEDC", "450 km"), ("Công suất", "150 kW")]},
    {"id": "ec-van", "name": "EC Van", "category": "fleet", "bodyType": "Van điện chở hàng", "seats": 2, "displayPrice": "Chính sách dành cho kinh doanh", "tagline": "Giao hàng bằng năng lượng sạch.", "specs": [("Quãng đường NEDC", "175 km"), ("Khoang hàng", "2,6 m³")]},
    {"id": "ebus", "name": "VinFast eBus", "category": "fleet", "bodyType": "Xe buýt điện", "seats": 60, "displayPrice": "Liên hệ giải pháp vận tải", "tagline": "Thành phố chuyển động êm hơn.", "specs": [("Dung lượng pin", "359–422 kWh"), ("Sức chứa", "60–90")]} ,
]

_VEHICLE_MEDIA_EXTENSIONS = {
    "vf3": "png",
    "vf6": "png",
    "vf-mpv-7": "png",
    "vf9": "png",
    "herio-green": "png",
    "nerio-green": "png",
}

# The published studio assets mostly are isolated vehicle renders. Marking all
# of them as photos made the UI select object-fit: cover and crop/zoom the cars.
_VEHICLE_STUDIO_MODES = {
    "limo-green": "photo",
    "ebus": "photo",
}


for order, vehicle in enumerate(_VEHICLES, start=1):
    slug = vehicle["id"]
    media_extension = _VEHICLE_MEDIA_EXTENSIONS.get(slug, "webp")
    vehicle.update(
        navName=vehicle["name"],
        thumbnail=_media(f"/media/vehicles/{slug}/thumbnail.{media_extension}", vehicle["name"], focalPoint="50% 50%"),
        studioImage={
            "url": f"/media/vehicles/{slug}/studio.{media_extension}",
            "mode": _VEHICLE_STUDIO_MODES.get(slug, "cutout"),
        },
        shortSpecs=[{"label": label, "value": value} for label, value in vehicle.pop("specs")],
        featured=vehicle["category"] == "personal",
        testDriveEligible=slug not in {"ec-van", "ebus"},
        sortOrder=order * 10,
        revision=REVISION,
    )


_DETAILS: dict[str, dict[str, Any]] = {
    vehicle["id"]: {
        "description": vehicle["tagline"],
        "brochure": {"title": f"Thông tin sản phẩm {vehicle['name']}", "url": f"/media/brochures/{vehicle['id']}.pdf", "revision": REVISION},
        "specifications": [{"group": "Thông số chính", "items": deepcopy(vehicle["shortSpecs"])}],
        "colors": [],
        "chapters": [],
        "gallery": [],
        "presentationFilm": None,
        "motion": {"imageUrl": vehicle["studioImage"]["url"], "preset": "horizontal", "focalPoint": "50% 50%"},
    }
    for vehicle in _VEHICLES
}

for vehicle_id in ("vf8", "vf8-the-he-moi", "vf9"):
    extension = _VEHICLE_MEDIA_EXTENSIONS.get(vehicle_id, "webp")
    _DETAILS[vehicle_id]["presentationFilm"] = {
        "url": f"/media/vehicles/{vehicle_id}/presentation.mp4",
        "posterUrl": f"/media/vehicles/{vehicle_id}/thumbnail.{extension}",
        "mimeType": "video/mp4",
        "autoplayAllowed": True,
    }


_CONTENT: dict[str, dict[str, Any]] = {
    "home": {
        "revision": REVISION,
        "hero": {"eyebrow": "VinFast", "title": "Cùng bạn bứt phá mọi giới hạn", "copy": "Hệ sinh thái di chuyển điện thông minh.", "vehicleId": "vf7", "media": _media("/media/content/home/hero.webp", "Dải xe điện VinFast", focalPoint="50% 50%")},
        "stories": [],
        "testimonials": [
            {
                "quote": "Điều thuyết phục tôi không phải một con số đơn lẻ, mà là cảm giác chiếc xe phản hồi ngay và cabin vẫn yên tĩnh giữa giờ cao điểm.",
                "name": "Nguyễn Khánh Linh",
                "role": "Khách hàng VF 7 · TP. Hồ Chí Minh",
            },
            {
                "quote": "Tôi thử xe cùng cả gia đình. Chỉ sau một vòng lái, mọi người đã biết hàng ghế nào sẽ là chỗ quen thuộc của mình.",
                "name": "Trần Hoàng Phúc",
                "role": "Khách hàng VF 9 · Hà Nội",
            },
            {
                "quote": "Lịch thử xe được giữ đúng mẫu và đúng khung giờ. Tôi đến showroom, nhận xe và bắt đầu lái mà không phải chờ.",
                "name": "Lê Ngọc An",
                "role": "Khách hàng VF 6 · Đà Nẵng",
            },
        ],
        "sections": [{"id": "factory", "type": "mediaFeature", "title": "Năng lực sản xuất", "copy": "Công nghệ và quy trình sản xuất hiện đại.", "media": _media("/media/content/home/factory.jpg", "Nhà máy VinFast")}],
    },
    "charging": {
        "revision": REVISION,
        "hero": {"title": "Pin và trạm sạc", "copy": "Hạ tầng sạc cho hành trình liền mạch.", "media": _media("/media/content/charging/hero.webp", "Trạm sạc VinFast")},
        "network": {"title": "Mạng lưới sạc toàn quốc", "copy": "Các điểm sạc được phát triển tại nhiều tỉnh thành."},
        "chargingUnits": [
            {"power": "250 kW", "name": "Sạc siêu nhanh DC", "image": _media("/media/content/charging/250kw.webp", "Trụ sạc 250 kW"), "facts": ["Tủ đứng", "1 cổng / trụ", "200–1.000 VDC", "IP54"]},
            {"power": "150 kW", "name": "Sạc siêu nhanh DC", "image": _media("/media/content/charging/150kw.webp", "Trụ sạc 150 kW"), "facts": ["Tủ đứng", "2 cổng / trụ", "200–1.000 VDC", "IP54"]},
            {"power": "60 kW", "name": "Sạc nhanh DC", "image": _media("/media/content/charging/60kw.webp", "Trụ sạc 60 kW"), "facts": ["Tủ đứng", "2 cổng / trụ", "200–1.000 VDC", "IP54"]},
            {"power": "30 kW", "name": "Sạc nhanh DC", "image": _media("/media/content/charging/30kw.webp", "Trụ sạc 30 kW"), "facts": ["Treo tường hoặc tủ đứng", "1 cổng / trụ", "CAN Protocol", "IP54"]},
        ],
        "guideMedia": [], "brochure": {"title": "Dịch vụ pin ô tô điện", "url": "/media/brochures/charging.pdf", "revision": REVISION},
    },
    "after-sales": {
        "revision": REVISION, "effectiveAt": "2026-08-04T00:00:00+07:00",
        "hero": {"title": "Dịch vụ hậu mãi", "copy": "Đồng hành trong suốt vòng đời xe.", "media": _media("/media/content/after-sales/hero.webp", "Dịch vụ hậu mãi VinFast")},
        "warrantyTables": [
            {"term": "10 năm", "distance": "200.000 km", "models": "VF 8, VF 9, Lạc Hồng 900 LX"},
            {"term": "8 năm", "distance": "160.000 km", "models": "VF 3, VF 5, VF 6, VF 7, VF Minio Green, VF Herio Green, VF MPV 7, VF Nerio Green, VF Limo Green"},
            {"term": "7 năm", "distance": "160.000 km", "models": "VF EC Van"},
        ],
        "policies": [], "consultationMedia": _media("/media/content/after-sales/consultation.webp", "Tư vấn dịch vụ"),
        "brochure": {"title": "Chính sách bảo hành ô tô", "url": "/media/brochures/warranty.pdf", "revision": REVISION},
    },
}


class SiteCatalogService:
    def __init__(self, snapshot_path: Path | None = None, media_base_url: str | None = None) -> None:
        self._vehicles = deepcopy(_VEHICLES)
        self._details = deepcopy(_DETAILS)
        self._content = deepcopy(_CONTENT)
        self._media_base_url = (media_base_url or get_settings().media_base_url).rstrip("/")
        configured_path = snapshot_path or Path(os.getenv("SITE_CATALOG_PATH", "data/site_catalog.json"))
        if configured_path.is_file():
            self.import_snapshot(configured_path)

    def list_vehicles(self, *, category: str | None, featured: bool | None, test_drive_eligible: bool | None, limit: int) -> list[dict[str, Any]]:
        vehicles = self._vehicles
        if category is not None:
            vehicles = [item for item in vehicles if item["category"] == category]
        if featured is not None:
            vehicles = [item for item in vehicles if item["featured"] is featured]
        if test_drive_eligible is not None:
            vehicles = [item for item in vehicles if item["testDriveEligible"] is test_drive_eligible]
        return self._with_public_media_urls(deepcopy(sorted(vehicles, key=lambda item: item["sortOrder"])[:limit]))

    def get_vehicle(self, vehicle_id: str) -> dict[str, Any] | None:
        summary = next((item for item in self._vehicles if item["id"] == vehicle_id), None)
        result = None if summary is None else {**deepcopy(summary), **deepcopy(self._details[vehicle_id])}
        return self._with_public_media_urls(result)

    def get_content(self, page: str) -> dict[str, Any] | None:
        content = self._content.get(page)
        return self._with_public_media_urls(deepcopy(content)) if content is not None else None

    def _with_public_media_urls(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._with_public_media_urls(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._with_public_media_urls(item) for item in value]
        if isinstance(value, str) and value.startswith("/media/"):
            return f"{self._media_base_url}/{value.removeprefix('/media/')}"
        return value

    def snapshot(self) -> dict[str, Any]:
        return {"vehicles": deepcopy(self._vehicles), "details": deepcopy(self._details), "content": deepcopy(self._content)}

    def import_snapshot(self, source: Path, destination: Path | None = None) -> dict[str, int]:
        """Validate a CMS export and optionally publish normalized JSON atomically."""
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
            snapshot = CatalogSnapshot.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"Invalid site catalog snapshot: {exc}") from exc

        vehicle_ids = {item.id for item in snapshot.vehicles}
        if set(snapshot.details) != vehicle_ids:
            raise ValueError("Snapshot details must contain exactly one record for every vehicle")
        if not {"home", "charging", "after-sales"}.issubset(snapshot.content):
            raise ValueError("Snapshot is missing one or more required content pages")

        normalized = snapshot.model_dump(mode="json", by_alias=True)
        self._vehicles = normalized["vehicles"]
        self._details = normalized["details"]
        self._content = normalized["content"]
        if destination is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(f"{destination.suffix}.tmp")
            temporary.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(destination)
        return {"vehicles": len(self._vehicles), "contentPages": len(self._content)}

    @staticmethod
    def etag(value: Any) -> str:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return f'"{sha256(encoded).hexdigest()}"'


site_catalog_service = SiteCatalogService()
