import json

import pytest
from src.services.site_catalog import SiteCatalogService


def test_snapshot_import_validates_and_publishes_atomically(tmp_path):
    service = SiteCatalogService()
    source = tmp_path / "source.json"
    destination = tmp_path / "published.json"
    source.write_text(json.dumps(service.snapshot(), ensure_ascii=False), encoding="utf-8")

    result = service.import_snapshot(source, destination)

    assert result == {"vehicles": 14, "contentPages": 3}
    assert json.loads(destination.read_text(encoding="utf-8"))["vehicles"][0]["id"] == "vf3"
    assert not destination.with_suffix(".json.tmp").exists()


def test_snapshot_import_rejects_missing_vehicle_detail(tmp_path):
    service = SiteCatalogService()
    snapshot = service.snapshot()
    snapshot["details"].pop("vf3")
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="exactly one record"):
        service.import_snapshot(source)


def test_service_boots_from_published_snapshot(tmp_path):
    initial = SiteCatalogService()
    source = tmp_path / "published.json"
    source.write_text(json.dumps(initial.snapshot(), ensure_ascii=False), encoding="utf-8")

    loaded = SiteCatalogService(snapshot_path=source)

    assert loaded.get_vehicle("vf7")["name"] == "VF 7"


def test_service_rewrites_media_urls_for_cdn():
    service = SiteCatalogService(media_base_url="https://cdn.example.com/assets")

    vehicle = service.get_vehicle("vf7")

    assert vehicle["thumbnail"]["url"] == "https://cdn.example.com/assets/vehicles/vf7/thumbnail.webp"
    assert vehicle["motion"]["imageUrl"] == "https://cdn.example.com/assets/vehicles/vf7/studio.webp"
