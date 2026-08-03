from __future__ import annotations

import json
import uuid
from typing import Any

from .database import connection


LOCATION_TYPES = {"FIXED_POINT","REGION","ROUTE","RANDOM_WORLD","MOVING","UNKNOWN"}
PRECISIONS = {"EXACT","APPROXIMATE","REGION_ONLY","UNKNOWN",None}
RESPAWN_MODES = {"FIXED","RANGE","CONDITIONAL","GLOBAL_POOL","UNKNOWN"}


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


def create_region(
    map_id: str,
    display_name: str,
    region_code: str | None = None,
    geometry_type: str = "UNKNOWN",
    geometry_json: dict[str, Any] | None = None,
    verification_status: str = "NEEDS_VERIFICATION",
    source_url: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    if geometry_type not in {"POINT","POLYGON","LINE","AREA_LABEL","UNKNOWN"}:
        raise ValueError("Unsupported geometry type")

    with connection() as con:
        if not con.execute("SELECT 1 FROM maps WHERE map_id=?", (map_id,)).fetchone():
            raise KeyError("Map not found")

        existing = con.execute(
            "SELECT map_region_id FROM map_regions WHERE map_id=? AND display_name=?",
            (map_id, display_name),
        ).fetchone()
        region_id = existing["map_region_id"] if existing else _id("MAPREGION")

        if not existing:
            con.execute(
                """INSERT INTO entities(entity_id,entity_type,canonical_name,slug,
                   verification_status,created_at,updated_at)
                   VALUES(?,?,?,lower(replace(?,' ','-')),?,datetime('now'),datetime('now'))""",
                (region_id, "MAP_REGION", display_name, display_name, verification_status),
            )

        con.execute(
            """INSERT INTO map_regions(
                 map_region_id,map_id,region_code,display_name,geometry_type,
                 geometry_json,verification_status,source_url,notes
               ) VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(map_id,display_name) DO UPDATE SET
                 region_code=excluded.region_code,
                 geometry_type=excluded.geometry_type,
                 geometry_json=excluded.geometry_json,
                 verification_status=excluded.verification_status,
                 source_url=excluded.source_url,
                 notes=excluded.notes""",
            (
                region_id,
                map_id,
                region_code,
                display_name,
                geometry_type,
                json.dumps(geometry_json) if geometry_json is not None else None,
                verification_status,
                source_url,
                notes,
            ),
        )
        con.commit()
    return get_region(region_id)


def get_region(map_region_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(
            """SELECT r.*,e.canonical_name
               FROM map_regions r
               JOIN entities e ON e.entity_id=r.map_region_id
               WHERE r.map_region_id=?""",
            (map_region_id,),
        ).fetchone()
        return dict(row) if row else None


def set_loot_source_location(
    loot_source_id: str,
    location_type: str,
    latitude: float | None = None,
    longitude: float | None = None,
    altitude: float | None = None,
    coordinate_precision: str | None = None,
    map_region_id: str | None = None,
    geometry_json: dict[str, Any] | None = None,
    verification_status: str = "NEEDS_VERIFICATION",
    source_url: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    location_type = location_type.upper()
    if location_type not in LOCATION_TYPES:
        raise ValueError("Unsupported location type")
    if coordinate_precision not in PRECISIONS:
        raise ValueError("Unsupported coordinate precision")
    if latitude is not None and not 0 <= latitude <= 100:
        raise ValueError("latitude must be between 0 and 100")
    if longitude is not None and not 0 <= longitude <= 100:
        raise ValueError("longitude must be between 0 and 100")
    if location_type == "FIXED_POINT" and (latitude is None or longitude is None):
        raise ValueError("Fixed points require latitude and longitude")

    with connection() as con:
        source = con.execute(
            "SELECT map_id FROM loot_sources WHERE loot_source_id=?",
            (loot_source_id,),
        ).fetchone()
        if not source:
            raise KeyError("Loot source not found")
        if map_region_id:
            region = con.execute(
                "SELECT map_id FROM map_regions WHERE map_region_id=?",
                (map_region_id,),
            ).fetchone()
            if not region:
                raise KeyError("Map region not found")
            if region["map_id"] != source["map_id"]:
                raise ValueError("Region and loot source must belong to the same map")

        location_id = _id("LOOTLOC")
        name = f"{loot_source_id} Location"
        con.execute(
            """INSERT INTO entities(entity_id,entity_type,canonical_name,slug,
               verification_status,created_at,updated_at)
               VALUES(?,?,?,lower(replace(?,' ','-')),?,datetime('now'),datetime('now'))""",
            (location_id, "LOOT_LOCATION", name, name, verification_status),
        )
        con.execute(
            """INSERT INTO loot_source_locations(
                 loot_source_location_id,loot_source_id,map_id,map_region_id,
                 location_type,latitude,longitude,altitude,coordinate_precision,
                 geometry_json,verification_status,source_url,notes
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                location_id,
                loot_source_id,
                source["map_id"],
                map_region_id,
                location_type,
                latitude,
                longitude,
                altitude,
                coordinate_precision,
                json.dumps(geometry_json) if geometry_json is not None else None,
                verification_status,
                source_url,
                notes,
            ),
        )
        con.commit()
    return get_location(location_id)


def get_location(location_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(
            """SELECT l.*,r.display_name AS region_name
               FROM loot_source_locations l
               LEFT JOIN map_regions r ON r.map_region_id=l.map_region_id
               WHERE l.loot_source_location_id=?""",
            (location_id,),
        ).fetchone()
        return dict(row) if row else None


def list_loot_source_locations(loot_source_id: str) -> list[dict[str, Any]]:
    with connection() as con:
        return [
            dict(row)
            for row in con.execute(
                """SELECT l.*,r.display_name AS region_name
                   FROM loot_source_locations l
                   LEFT JOIN map_regions r ON r.map_region_id=l.map_region_id
                   WHERE l.loot_source_id=?
                   ORDER BY l.location_type,l.latitude,l.longitude""",
                (loot_source_id,),
            )
        ]


def set_respawn_profile(
    loot_source_id: str,
    respawn_mode: str,
    minimum_seconds: int | None = None,
    maximum_seconds: int | None = None,
    initial_spawn_seconds: int | None = None,
    active_limit: int | None = None,
    requires_pickup: bool | None = None,
    requires_player_distance: bool | None = None,
    verification_status: str = "NEEDS_VERIFICATION",
    source_url: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    respawn_mode = respawn_mode.upper()
    if respawn_mode not in RESPAWN_MODES:
        raise ValueError("Unsupported respawn mode")
    for name, value in {
        "minimum_seconds": minimum_seconds,
        "maximum_seconds": maximum_seconds,
        "initial_spawn_seconds": initial_spawn_seconds,
        "active_limit": active_limit,
    }.items():
        if value is not None and value < 0:
            raise ValueError(f"{name} must be >= 0")
    if minimum_seconds is not None and maximum_seconds is not None and maximum_seconds < minimum_seconds:
        raise ValueError("maximum_seconds must be >= minimum_seconds")

    with connection() as con:
        if not con.execute(
            "SELECT 1 FROM loot_sources WHERE loot_source_id=?",
            (loot_source_id,),
        ).fetchone():
            raise KeyError("Loot source not found")

        existing = con.execute(
            "SELECT loot_source_respawn_profile_id FROM loot_source_respawn_profiles WHERE loot_source_id=?",
            (loot_source_id,),
        ).fetchone()
        profile_id = existing["loot_source_respawn_profile_id"] if existing else _id("RESPAWN")

        con.execute(
            """INSERT INTO loot_source_respawn_profiles(
                 loot_source_respawn_profile_id,loot_source_id,respawn_mode,
                 minimum_seconds,maximum_seconds,initial_spawn_seconds,active_limit,
                 requires_pickup,requires_player_distance,verification_status,
                 source_url,notes
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(loot_source_id) DO UPDATE SET
                 respawn_mode=excluded.respawn_mode,
                 minimum_seconds=excluded.minimum_seconds,
                 maximum_seconds=excluded.maximum_seconds,
                 initial_spawn_seconds=excluded.initial_spawn_seconds,
                 active_limit=excluded.active_limit,
                 requires_pickup=excluded.requires_pickup,
                 requires_player_distance=excluded.requires_player_distance,
                 verification_status=excluded.verification_status,
                 source_url=excluded.source_url,
                 notes=excluded.notes""",
            (
                profile_id,
                loot_source_id,
                respawn_mode,
                minimum_seconds,
                maximum_seconds,
                initial_spawn_seconds,
                active_limit,
                None if requires_pickup is None else int(requires_pickup),
                None if requires_player_distance is None else int(requires_player_distance),
                verification_status,
                source_url,
                notes,
            ),
        )
        con.commit()
    return get_respawn_profile(loot_source_id)


def get_respawn_profile(loot_source_id: str) -> dict[str, Any] | None:
    with connection() as con:
        row = con.execute(
            """SELECT * FROM loot_source_respawn_profiles
               WHERE loot_source_id=?""",
            (loot_source_id,),
        ).fetchone()
        return dict(row) if row else None


def get_loot_source_location_profile(loot_source_id: str) -> dict[str, Any] | None:
    with connection() as con:
        source = con.execute(
            """SELECT l.loot_source_id,e.canonical_name,l.map_id,l.source_group,
                      l.drop_color,l.has_ring,l.required_level,l.verification_status
               FROM loot_sources l
               JOIN entities e ON e.entity_id=l.loot_source_id
               WHERE l.loot_source_id=?""",
            (loot_source_id,),
        ).fetchone()
        if not source:
            return None
    return {
        "loot_source": dict(source),
        "locations": list_loot_source_locations(loot_source_id),
        "respawn": get_respawn_profile(loot_source_id),
    }
