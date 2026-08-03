from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from .config import ROOT, settings
from .repository import get_item, list_items, get_creature, list_creatures, list_loot_sources, get_loot_source, get_item_loot_paths, global_search, get_entity_graph, get_entity_profile
from .review import create_review_case, list_review_cases, get_review_case, review_claim, decide_case, resolve_conflict
from .promotion import preview_promotion, promote_review, get_revisions
from .steward import get_steward_summary, list_ingestion_runs, get_review_workspace
from .source_workbench import list_sources, get_source_workspace, register_source, add_source_version, record_health_check, link_claim_evidence, compare_source_versions
from .content_pipeline import import_map_manifest, list_content_manifests, get_map_content
from .creature_content import import_creature_manifest, get_creature_content
from .item_content import import_item_manifest, get_item_content
from .loot_content import import_loot_manifest, get_loot_content
from .quality_engine import calculate_quality_range, create_profile, get_profile, list_profiles, calculate_from_profile
from .loot_quality import configure_loot_source_quality, set_entry_item_multiplier, recalculate_loot_source_quality, get_loot_source_quality, get_loot_entry_quality, list_loot_quality_matrix
from .loot_matrix import get_loot_matrix, export_loot_matrix_csv, export_loot_matrix_json
from .loot_groups import configure_loot_source_group, get_loot_source_group, ensure_map_groups, get_grouped_loot_matrix
from .loot_locations import create_region, set_loot_source_location, set_respawn_profile, get_loot_source_location_profile
from .blueprint_finder import search_blueprints, get_blueprint_profile
from .coverage import global_coverage, map_coverage, gaps
from .schemas import ItemDetail, ItemSummary, CreatureDetail, CreatureSummary, LootSourceSummary, LootSourceDetail, ItemLootPath, SearchResult, GraphResponse, EntityProfile, SourceCreate, SourceVersionCreate, SourceHealthCheckCreate, ClaimEvidenceLinkCreate, QualityCalculationRequest, QualityProfileCreate, QualityProfileCalculationRequest, LootSourceQualityConfig, LootEntryQualityMultiplier, LootQualityRecalculateRequest, LootSourceGroupConfig, MapRegionCreate, LootSourceLocationCreate, LootSourceRespawnConfig

app = FastAPI(title=settings.app_name, version=settings.app_version)
STATIC = ROOT / "packages/web/static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")

@app.get("/admin", include_in_schema=False)
def admin_console():
    return FileResponse(STATIC / "admin.html")

@app.get("/admin/sources", include_in_schema=False)
def source_console():
    return FileResponse(STATIC / "sources.html")


@app.get("/loot-matrix", include_in_schema=False)
def loot_matrix_page():
    return FileResponse(STATIC / "loot-matrix.html")


@app.get("/blueprint-finder", include_in_schema=False)
def blueprint_finder_page():
    return FileResponse(STATIC / "blueprint-finder.html")


@app.get("/coverage", include_in_schema=False)
def coverage_page():
    return FileResponse(STATIC / "coverage.html")

@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}

@app.get("/api/v1/items", response_model=list[ItemSummary])
def items(q: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return list_items(q=q, limit=limit, offset=offset)

@app.get("/api/v1/items/{item_id}", response_model=ItemDetail)
def item(item_id: str):
    value = get_item(item_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return value

@app.get("/api/v1/creatures", response_model=list[CreatureSummary])
def creatures(q: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return list_creatures(q=q, limit=limit, offset=offset)

@app.get("/api/v1/creatures/{creature_id}", response_model=CreatureDetail)
def creature(creature_id: str):
    value = get_creature(creature_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Creature not found")
    return value

@app.get("/api/v1/loot-sources", response_model=list[LootSourceSummary])
def loot_sources(q: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return list_loot_sources(q=q, limit=limit, offset=offset)

@app.get("/api/v1/loot-sources/{loot_source_id}", response_model=LootSourceDetail)
def loot_source(loot_source_id: str):
    value=get_loot_source(loot_source_id)
    if value is None: raise HTTPException(status_code=404, detail="Loot source not found")
    return value

@app.get("/api/v1/items/{item_id}/loot-paths", response_model=list[ItemLootPath])
def item_loot_paths(item_id: str):
    if get_item(item_id) is None: raise HTTPException(status_code=404, detail="Item not found")
    return get_item_loot_paths(item_id)

@app.get("/api/v1/search", response_model=list[SearchResult])
def search(q: str = Query(..., min_length=1, max_length=120), limit: int = Query(25, ge=1, le=100), include_unverified: bool = False):
    return global_search(q=q, limit=limit, include_unverified=include_unverified)

@app.get("/api/v1/graph/{entity_id}", response_model=GraphResponse)
def entity_graph(entity_id: str, depth: int = Query(1, ge=1, le=3)):
    value = get_entity_graph(entity_id, depth=depth)
    if value is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return value

@app.get("/api/v1/entities/{entity_id}", response_model=EntityProfile)
def entity_profile(entity_id: str, depth: int = Query(1, ge=1, le=3)):
    value = get_entity_profile(entity_id, depth=depth)
    if value is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return value

@app.get("/api/v1/reviews")
def reviews(status: str | None = None, assigned_to: str | None = None, limit: int = Query(100, ge=1, le=500)):
    return list_review_cases(status=status, assigned_to=assigned_to, limit=limit)

@app.post("/api/v1/reviews/import-records/{import_record_id}")
def open_review(import_record_id: str, priority: int = Query(50, ge=0, le=100), assigned_to: str | None = None):
    try: return create_review_case(import_record_id, priority, assigned_to)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))

@app.get("/api/v1/reviews/{review_case_id}")
def review_detail(review_case_id: str):
    value=get_review_case(review_case_id)
    if value is None: raise HTTPException(status_code=404, detail="Review case not found")
    return value

@app.post("/api/v1/reviews/{review_case_id}/claims/{claim_candidate_id}")
def claim_decision(review_case_id: str, claim_candidate_id: str, reviewer: str, decision: str, normalized_value: str | None = None, notes: str | None = None):
    try: return review_claim(review_case_id, claim_candidate_id, reviewer, decision, normalized_value, notes)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))

@app.post("/api/v1/reviews/{review_case_id}/decision")
def case_decision(review_case_id: str, reviewer: str, decision: str, notes: str | None = None):
    try: return decide_case(review_case_id, reviewer, decision, notes)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))

@app.post("/api/v1/reviews/conflicts/{conflict_id}/resolve")
def conflict_resolution(conflict_id: str, reviewer: str, notes: str):
    try: return resolve_conflict(conflict_id, reviewer, notes)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/v1/promotions/{review_case_id}/preview")
def promotion_preview(review_case_id: str, actor: str = "api-preview"):
    try: return preview_promotion(review_case_id, actor)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))

@app.post("/api/v1/promotions/{review_case_id}")
def promotion_commit(review_case_id: str, actor: str, expected_row_version: int | None = None):
    try: return promote_review(review_case_id, actor, expected_row_version)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))

@app.get("/api/v1/entities/{entity_id}/revisions")
def entity_revisions(entity_id: str):
    return get_revisions(entity_id)


@app.get("/api/v1/admin/summary")
def steward_summary():
    return get_steward_summary()

@app.get("/api/v1/admin/imports")
def steward_imports(limit: int = Query(50, ge=1, le=500)):
    return list_ingestion_runs(limit=limit)

@app.get("/api/v1/admin/reviews/{review_case_id}/workspace")
def steward_review_workspace(review_case_id: str):
    value = get_review_workspace(review_case_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Review case not found")
    return value


@app.get("/api/v1/sources")
def source_list(stale_days: int = Query(30, ge=1, le=3650), stale_only: bool = False):
    return list_sources(stale_days=stale_days, stale_only=stale_only)

@app.post("/api/v1/sources")
def source_create(payload: SourceCreate):
    return register_source(**payload.model_dump())

@app.get("/api/v1/sources/{source_id}")
def source_workspace(source_id: str):
    value = get_source_workspace(source_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return value

@app.post("/api/v1/sources/{source_id}/versions")
def source_version_create(source_id: str, payload: SourceVersionCreate):
    try:
        return add_source_version(source_id=source_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.post("/api/v1/sources/{source_id}/health-checks")
def source_health_create(source_id: str, payload: SourceHealthCheckCreate):
    try:
        return record_health_check(source_id=source_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.post("/api/v1/claims/{claim_candidate_id}/evidence")
def claim_evidence_create(claim_candidate_id: str, payload: ClaimEvidenceLinkCreate):
    try:
        return link_claim_evidence(claim_candidate_id=claim_candidate_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/sources/{source_id}/compare")
def source_compare(source_id: str, left: str, right: str, compared_by: str = "api"):
    try:
        return compare_source_versions(source_id, left, right, compared_by)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.get("/api/v1/content-manifests")
def content_manifest_list():
    return list_content_manifests()

@app.post("/api/v1/content-manifests/import")
def content_manifest_import(path: str, commit: bool = False, actor: str = "api-content-importer"):
    try:
        return import_map_manifest(path, commit=commit, actor=actor)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Manifest file not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/maps/{map_id}/content")
def map_content(map_id: str):
    value = get_map_content(map_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Map not found")
    return value


@app.post("/api/v1/creature-content/import")
def creature_content_import(path: str, commit: bool = False, actor: str = "api-creature-importer"):
    try: return import_creature_manifest(path, commit=commit, actor=actor)
    except FileNotFoundError: raise HTTPException(status_code=404, detail="Manifest file not found")

@app.get("/api/v1/creatures/{creature_id}/content")
def creature_content(creature_id: str):
    value=get_creature_content(creature_id)
    if value is None: raise HTTPException(status_code=404, detail="Creature not found")
    return value


@app.post("/api/v1/item-content/import")
def item_content_import(path: str, commit: bool = False, actor: str = "api-item-importer"):
    try:
        return import_item_manifest(path, commit=commit, actor=actor)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Manifest file not found")

@app.get("/api/v1/items/{item_id}/content")
def item_content(item_id: str):
    value = get_item_content(item_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return value


@app.post("/api/v1/loot-content/import")
def loot_content_import(path: str, commit: bool = False, actor: str = "api-loot-importer"):
    try:
        return import_loot_manifest(path, commit=commit, actor=actor)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Manifest file not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/loot-sources/{loot_source_id}/content")
def loot_content(loot_source_id: str):
    value = get_loot_content(loot_source_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Loot source not found")
    return value


@app.post("/api/v1/quality/calculate")
def quality_calculate(payload: QualityCalculationRequest):
    try:
        return calculate_quality_range(
            payload.source_quality_min_percent,
            payload.source_quality_max_percent,
            payload.item_quality_multiplier_percent,
            payload.additional_multiplier,
            payload.rounding_digits,
            payload.persist,
            None,
            payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/quality-profiles")
def quality_profile_list():
    return list_profiles()

@app.post("/api/v1/quality-profiles")
def quality_profile_create(payload: QualityProfileCreate):
    try:
        return create_profile(
            payload.quality_profile_id,payload.profile_code,payload.display_name,
            payload.source_quality_min_percent,payload.source_quality_max_percent,
            payload.difficulty_multiplier,payload.crate_quality_multiplier,
            payload.rounding_digits,payload.verification_status,payload.source_url,payload.notes
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/quality-profiles/{profile_id}")
def quality_profile_get(profile_id: str):
    value=get_profile(profile_id)
    if value is None: raise HTTPException(status_code=404, detail="Quality profile not found")
    return value

@app.post("/api/v1/quality-profiles/{profile_id}/calculate")
def quality_profile_calculate(profile_id: str, payload: QualityProfileCalculationRequest):
    try:
        return calculate_from_profile(
            profile_id,
            payload.item_quality_multiplier_percent,
            payload.additional_multiplier,
            payload.persist,
            payload.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/v1/loot-quality")
def loot_quality_matrix(drop_color: str | None = None, has_ring: bool | None = None):
    return list_loot_quality_matrix(drop_color=drop_color, has_ring=has_ring)

@app.get("/api/v1/loot-sources/{loot_source_id}/quality")
def loot_source_quality_get(loot_source_id: str):
    value = get_loot_source_quality(loot_source_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Loot source not found")
    return value

@app.put("/api/v1/loot-sources/{loot_source_id}/quality")
def loot_source_quality_put(loot_source_id: str, payload: LootSourceQualityConfig):
    try:
        return configure_loot_source_quality(loot_source_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/loot-entries/{loot_entry_id}/quality")
def loot_entry_quality_get(loot_entry_id: str):
    value = get_loot_entry_quality(loot_entry_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Loot entry not found")
    return value

@app.put("/api/v1/loot-entries/{loot_entry_id}/quality-multiplier")
def loot_entry_quality_multiplier_put(loot_entry_id: str, payload: LootEntryQualityMultiplier):
    try:
        return set_entry_item_multiplier(loot_entry_id, payload.item_quality_multiplier_percent)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.post("/api/v1/loot-sources/{loot_source_id}/quality/recalculate")
def loot_source_quality_recalculate(loot_source_id: str, payload: LootQualityRecalculateRequest):
    try:
        return recalculate_loot_source_quality(loot_source_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/v1/loot-matrix")
def loot_matrix(
    map_id: str | None = None,
    drop_color: str | None = None,
    has_ring: bool | None = None,
    required_level_min: int | None = Query(None, ge=0),
    verification_status: str | None = None,
    source_group: str | None = None,
):
    return get_loot_matrix(
        map_id=map_id,
        drop_color=drop_color,
        has_ring=has_ring,
        required_level_min=required_level_min,
        verification_status=verification_status,
        source_group=source_group,
    )

@app.get("/api/v1/loot-matrix/export.csv")
def loot_matrix_csv(
    map_id: str | None = None,
    drop_color: str | None = None,
    has_ring: bool | None = None,
    required_level_min: int | None = Query(None, ge=0),
    verification_status: str | None = None,
    source_group: str | None = None,
):
    content = export_loot_matrix_csv(
        map_id=map_id,
        drop_color=drop_color,
        has_ring=has_ring,
        required_level_min=required_level_min,
        verification_status=verification_status,
        source_group=source_group,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=ark-loot-matrix.csv"},
    )

@app.get("/api/v1/loot-matrix/export.json")
def loot_matrix_json(
    map_id: str | None = None,
    drop_color: str | None = None,
    has_ring: bool | None = None,
    required_level_min: int | None = Query(None, ge=0),
    verification_status: str | None = None,
    source_group: str | None = None,
):
    content = export_loot_matrix_json(
        map_id=map_id,
        drop_color=drop_color,
        has_ring=has_ring,
        required_level_min=required_level_min,
        verification_status=verification_status,
        source_group=source_group,
    )
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=ark-loot-matrix.json"},
    )


@app.put("/api/v1/loot-sources/{loot_source_id}/group")
def loot_source_group_put(loot_source_id: str, payload: LootSourceGroupConfig):
    try:
        return configure_loot_source_group(
            loot_source_id, payload.source_group, payload.display_order
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/loot-sources/{loot_source_id}/group")
def loot_source_group_get(loot_source_id: str):
    value = get_loot_source_group(loot_source_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Loot source not found")
    return value

@app.get("/api/v1/maps/{map_id}/loot-groups")
def map_loot_groups(map_id: str, include_empty: bool = True):
    try:
        return get_grouped_loot_matrix(map_id, include_empty=include_empty)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/v1/map-regions")
def map_region_create(payload: MapRegionCreate):
    try:
        return create_region(**payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.post("/api/v1/loot-sources/{loot_source_id}/locations")
def loot_source_location_create(loot_source_id: str, payload: LootSourceLocationCreate):
    try:
        return set_loot_source_location(loot_source_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.put("/api/v1/loot-sources/{loot_source_id}/respawn")
def loot_source_respawn_put(loot_source_id: str, payload: LootSourceRespawnConfig):
    try:
        return set_respawn_profile(loot_source_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/loot-sources/{loot_source_id}/location-profile")
def loot_source_location_profile_get(loot_source_id: str):
    value = get_loot_source_location_profile(loot_source_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Loot source not found")
    return value


@app.get("/api/v1/blueprints")
def blueprint_search(
    q: str | None = None,
    map_id: str | None = None,
    source_group: str | None = None,
    drop_color: str | None = None,
    has_ring: bool | None = None,
    required_level_max: int | None = Query(None, ge=0),
    verification_status: str | None = None,
):
    return search_blueprints(
        query=q,
        map_id=map_id,
        source_group=source_group,
        drop_color=drop_color,
        has_ring=has_ring,
        required_level_max=required_level_max,
        verification_status=verification_status,
    )

@app.get("/api/v1/blueprints/{blueprint_id}")
def blueprint_profile(blueprint_id: str):
    value = get_blueprint_profile(blueprint_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return value


@app.get("/api/v1/coverage")
def coverage_global():
    return global_coverage()

@app.get("/api/v1/coverage/gaps")
def coverage_gaps(limit: int = Query(100, ge=1, le=1000)):
    return gaps(limit)

@app.get("/api/v1/maps/{map_id}/coverage")
def coverage_map(map_id: str):
    value=map_coverage(map_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Map not found")
    return value
