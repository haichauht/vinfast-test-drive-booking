"""Copy frontend fallback images into the backend local media origin.

Production should upload the same destination keys to object storage/CDN.
Usage: python scripts/publish_site_media.py [frontend_root] [media_root]
"""

import os
import shutil
import sys
from pathlib import Path

VEHICLES = {
    "vf3": "src/media/local/vehicle-media/VF3/xám.png",
    "vf5": "src/media/local/vehicle-media/VF5/trắng.webp",
    "vf6": "src/media/local/by-model/vf6/studio.png",
    "vf7": "src/media/local/vehicle-media/VF7/product-CE18.webp",
    "vf-mpv-7": "src/media/local/by-model/vf-mpv-7/studio.png",
    "vf8": "src/media/local/vehicle-media/VF8/product-CE18.webp",
    "vf8-the-he-moi": "src/media/local/vehicle-media/VF8 All the new/VF8PH-23.webp",
    "vf9": "src/media/local/common/vf9-studio.png",
    "herio-green": "src/media/local/vehicle-media/Dịch vụ_Herio Green/trắng.png",
    "minio-green": "src/media/local/vehicle-media/Dịch vụ_MINIO Green/Minio.webp",
    "nerio-green": "src/media/local/common/nerio-green-studio.png",
    "limo-green": "src/media/local/by-model/limo-green/studio.webp",
    "ec-van": "src/media/local/vehicle-media/Dịch vụ_ EC Van/ecvan-jade.webp",
    "ebus": "src/media/local/by-model/ebus/studio.webp",
}

CONTENT = {
    "content/home/hero.webp": "src/media/local/common/vinfast-road-banner.webp",
    "content/home/factory.jpg": "src/media/local/vehicle-media/nha-may-vinfast.jpg",
    "content/after-sales/hero.webp": "src/media/local/common/after-sales-hero.webp",
    "content/after-sales/consultation.webp": "src/media/local/common/after-sales-consultation.webp",
    "content/charging/hero.webp": "src/media/local/vehicle-media/Trạm sạc/pin-tramsac-6_1660273722.png.webp",
    "content/charging/250kw.png": "src/media/local/vehicle-media/Trạm sạc/charger-250-cutout-v2.png",
    "content/charging/150kw.png": "src/media/local/vehicle-media/Trạm sạc/charger-150-cutout-v2.png",
    "content/charging/60kw.png": "src/media/local/vehicle-media/Trạm sạc/charger-60-cutout-v2.png",
    "content/charging/30kw.png": "src/media/local/vehicle-media/Trạm sạc/charger-30-cutout-v2.png",
}

COMMON_TO_VEHICLE_MEDIA = {
    "VF6/vf6-front-model-cutout.png": "src/media/local/common/vf6-front-model-cutout.png",
    "VF7 FMP/vf-mpv-7-model-cutout.png": "src/media/local/common/vf-mpv-7-model-cutout.png",
    "Dịch vụ_Limo Green/limo-green-studio.webp": "src/media/local/common/limo-green-studio.webp",
}

VIDEOS = {
    "vf8": "src/media/local/vehicle-media/VF8/VF8.mp4",
    "vf8-the-he-moi": "src/media/local/vehicle-media/VF8 All the new/VF8.mp4",
    "vf9": "src/media/local/vehicle-media/VF9/VF9.mp4",
}

LEGACY_KEYS = [
    "content/home/factory.webp",
    "content/charging/250kw.webp",
    "content/charging/150kw.webp",
    "content/charging/60kw.webp",
    "content/charging/30kw.webp",
    *[
        f"vehicles/{vehicle_id}/{name}.webp"
        for vehicle_id in ("vf3", "vf6", "vf-mpv-7", "vf9", "herio-green", "nerio-green")
        for name in ("thumbnail", "studio")
    ],
]


def _copy(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Missing source media: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main() -> int:
    frontend_root = Path(sys.argv[1] if len(sys.argv) > 1 else "../frontend").resolve()
    media_root = Path(sys.argv[2] if len(sys.argv) > 2 else os.getenv("MEDIA_ROOT", "data/media")).resolve()
    for legacy_key in LEGACY_KEYS:
        (media_root / legacy_key).unlink(missing_ok=True)
    for vehicle_id, relative_source in VEHICLES.items():
        source = frontend_root / relative_source
        extension = source.suffix.lower()
        _copy(source, media_root / "vehicles" / vehicle_id / f"thumbnail{extension}")
        _copy(source, media_root / "vehicles" / vehicle_id / f"studio{extension}")
    for destination, relative_source in CONTENT.items():
        _copy(frontend_root / relative_source, media_root / destination)
    vehicle_media_source = frontend_root / "src" / "media" / "local" / "vehicle-media"
    vehicle_media_destination = media_root / "vehicle-media"
    if vehicle_media_source.is_dir():
        shutil.copytree(vehicle_media_source, vehicle_media_destination, dirs_exist_ok=True)
    for destination, relative_source in COMMON_TO_VEHICLE_MEDIA.items():
        _copy(frontend_root / relative_source, vehicle_media_destination / destination)
    for vehicle_id, relative_source in VIDEOS.items():
        _copy(frontend_root / relative_source, media_root / "vehicles" / vehicle_id / "presentation.mp4")
    total = len(VEHICLES) * 2 + len(CONTENT) + len(COMMON_TO_VEHICLE_MEDIA) + len(VIDEOS)
    print(f"Published {total} files into {media_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
