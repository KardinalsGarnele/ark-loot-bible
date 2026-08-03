from pydantic import BaseModel, ConfigDict, Field

class ItemSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str
    canonical_name: str
    slug: str | None = None
    verification_status: str
    game_title: str | None = None
    internal_name: str | None = None
    description: str | None = None
    stack_size: int | None = None
    weight: float | None = None
    quality_capable: int | None = None
    lifecycle_status: str
    category_code: str | None = None
    category_name: str | None = None

class Relationship(BaseModel):
    item_relationship_id: str
    relationship_type: str
    target_entity_id: str
    verification_status: str
    valid_from: str | None = None
    valid_to: str | None = None

class ItemDetail(ItemSummary):
    relationships: list[Relationship] = Field(default_factory=list)

class CreatureSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    creature_id: str
    canonical_name: str
    slug: str | None = None
    verification_status: str
    game_title: str | None = None
    internal_name: str | None = None
    description: str | None = None
    species_name: str | None = None
    tameable: int | None = None
    breedable: int | None = None
    diet_type: str | None = None
    temperament: str | None = None
    lifecycle_status: str

class CreatureVariant(BaseModel):
    variant_id: str
    canonical_name: str
    slug: str | None = None
    variant_type: str
    internal_name: str | None = None
    is_default: int
    lifecycle_status: str
    verification_status: str

class CreatureMapPresence(BaseModel):
    map_id: str
    canonical_name: str
    presence_type: str
    verification_status: str
    valid_from: str | None = None
    valid_to: str | None = None

class CreatureRelationship(BaseModel):
    creature_relationship_id: str
    relationship_type: str
    target_entity_id: str
    verification_status: str
    valid_from: str | None = None
    valid_to: str | None = None

class CreatureDetail(CreatureSummary):
    variants: list[CreatureVariant] = Field(default_factory=list)
    maps: list[CreatureMapPresence] = Field(default_factory=list)
    relationships: list[CreatureRelationship] = Field(default_factory=list)

class LootEntrySummary(BaseModel):
    loot_entry_id: str
    canonical_name: str
    item_id: str | None = None
    item_name: str | None = None
    blueprint_id: str | None = None
    blueprint_name: str | None = None
    entry_weight: float | None = None
    min_quantity: int | None = None
    max_quantity: int | None = None
    blueprint_chance: float | None = None
    effective_quality_min: float | None = None
    effective_quality_max: float | None = None
    verification_status: str

class LootSetDetail(BaseModel):
    loot_set_id: str
    canonical_name: str
    selection_weight: float | None = None
    min_rolls: int | None = None
    max_rolls: int | None = None
    verification_status: str
    entries: list[LootEntrySummary] = Field(default_factory=list)

class LootSourceSummary(BaseModel):
    loot_source_id: str
    canonical_name: str
    slug: str | None = None
    source_type: str
    map_id: str | None = None
    map_name: str | None = None
    description: str | None = None
    lifecycle_status: str
    verification_status: str

class LootSourceDetail(LootSourceSummary):
    sets: list[LootSetDetail] = Field(default_factory=list)

class ItemLootPath(BaseModel):
    item_id: str
    item_name: str
    blueprint_id: str | None = None
    blueprint_name: str | None = None
    loot_entry_id: str
    loot_set_id: str
    loot_set_name: str
    loot_source_id: str
    loot_source_name: str
    source_type: str
    verification_status: str

class SearchResult(BaseModel):
    entity_id: str
    entity_type: str
    canonical_name: str
    slug: str | None = None
    verification_status: str
    score: int
    path: str

class GraphNode(BaseModel):
    entity_id: str
    entity_type: str
    canonical_name: str
    slug: str | None = None
    verification_status: str

class GraphEdge(BaseModel):
    edge_type: str
    source_id: str
    target_id: str
    verification_status: str | None = None
    source_table: str

class GraphResponse(BaseModel):
    root: GraphNode
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)

class EntityProfile(BaseModel):
    entity: GraphNode
    details: dict = Field(default_factory=dict)
    graph: GraphResponse


class SourceCreate(BaseModel):
    source_id: str
    source_type: str
    title: str
    locator: str | None = None
    publisher: str | None = None
    notes: str | None = None

class SourceVersionCreate(BaseModel):
    content_text: str
    version_label: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None

class SourceHealthCheckCreate(BaseModel):
    check_status: str
    http_status: int | None = None
    response_time_ms: int | None = None
    content_hash_sha256: str | None = None
    notes: str | None = None

class ClaimEvidenceLinkCreate(BaseModel):
    source_version_id: str
    evidence_relation: str = "SUPPORTS"
    locator: str | None = None
    excerpt: str | None = None
    linked_by: str


class QualityCalculationRequest(BaseModel):
    source_quality_min_percent: float | None = None
    source_quality_max_percent: float | None = None
    item_quality_multiplier_percent: float | None = None
    additional_multiplier: float = 1.0
    rounding_digits: int = 2
    persist: bool = False
    notes: str | None = None

class QualityProfileCreate(BaseModel):
    quality_profile_id: str
    profile_code: str
    display_name: str
    source_quality_min_percent: float | None = None
    source_quality_max_percent: float | None = None
    difficulty_multiplier: float | None = None
    crate_quality_multiplier: float | None = None
    rounding_digits: int = 2
    verification_status: str = "NEEDS_VERIFICATION"
    source_url: str | None = None
    notes: str | None = None

class QualityProfileCalculationRequest(BaseModel):
    item_quality_multiplier_percent: float
    additional_multiplier: float | None = None
    persist: bool = False
    notes: str | None = None


class LootSourceQualityConfig(BaseModel):
    drop_color: str | None = None
    has_ring: bool | None = None
    required_level: int | None = None
    quality_profile_id: str | None = None

class LootEntryQualityMultiplier(BaseModel):
    item_quality_multiplier_percent: float | None = None

class LootQualityRecalculateRequest(BaseModel):
    persist_calculation_audits: bool = False
    notes: str | None = None


class LootSourceGroupConfig(BaseModel):
    source_group: str
    display_order: int | None = None


class MapRegionCreate(BaseModel):
    map_id: str
    display_name: str
    region_code: str | None = None
    geometry_type: str = "UNKNOWN"
    geometry_json: dict | None = None
    verification_status: str = "NEEDS_VERIFICATION"
    source_url: str | None = None
    notes: str | None = None

class LootSourceLocationCreate(BaseModel):
    location_type: str
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    coordinate_precision: str | None = None
    map_region_id: str | None = None
    geometry_json: dict | None = None
    verification_status: str = "NEEDS_VERIFICATION"
    source_url: str | None = None
    notes: str | None = None

class LootSourceRespawnConfig(BaseModel):
    respawn_mode: str
    minimum_seconds: int | None = None
    maximum_seconds: int | None = None
    initial_spawn_seconds: int | None = None
    active_limit: int | None = None
    requires_pickup: bool | None = None
    requires_player_distance: bool | None = None
    verification_status: str = "NEEDS_VERIFICATION"
    source_url: str | None = None
    notes: str | None = None
