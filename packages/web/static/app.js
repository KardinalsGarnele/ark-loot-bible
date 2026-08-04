const $ = (selector) => document.querySelector(selector);

const home = $("#home");
const entity = $("#entity");
const form = $("#search-form");
const input = $("#search");
const status = $("#status");
const results = $("#results");
const preview = $("#preview");

const labels = {
  CREATURE: "Creature",
  CREATURE_VARIANT: "Variant",
  ITEM: "Item",
  BLUEPRINT: "Blueprint",
  LOOT_SOURCE: "Loot Source",
  LOOT_SET: "Loot Set",
  LOOT_ENTRY: "Loot Entry",
  MAP: "Map",
  REGION: "Region",
  BOSS: "Boss",
  ENGRAM: "Engram",
  RESOURCE: "Resource",
};

const icons = {
  CREATURE: "◆",
  CREATURE_VARIANT: "◇",
  ITEM: "▣",
  BLUEPRINT: "▤",
  LOOT_SOURCE: "⬡",
  LOOT_SET: "⬢",
  LOOT_ENTRY: "⬟",
  MAP: "◫",
  REGION: "⌖",
  BOSS: "♜",
  ENGRAM: "◈",
  RESOURCE: "●",
};

const esc = (value) =>
  String(value ?? "").replace(
    /[&<>'"]/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
      })[character],
  );

const entityLabel = (type) => labels[type] || type || "Entity";
const entityIcon = (type) => icons[type] || "○";

const formatLabel = (value) =>
  String(value ?? "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());

const entityUrl = (id) => `#/entity/${encodeURIComponent(id)}`;

const badge = (verificationStatus = "UNKNOWN") => {
  const statusValue = String(verificationStatus).toUpperCase();
  const className = statusValue === "VERIFIED" ? "ok" : "warn";

  return `
    <span class="badge ${className}">
      ${esc(formatLabel(statusValue))}
    </span>
  `;
};

async function json(url) {
  const response = await fetch(url);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }

  return data;
}

function renderSearchResult(result) {
  return `
    <a
      class="card result result-card"
      href="${entityUrl(result.entity_id)}"
      aria-label="${esc(result.canonical_name)} öffnen"
    >
      <div class="result-card-top">
        <span class="entity-type">
          <span class="entity-icon" aria-hidden="true">
            ${entityIcon(result.entity_type)}
          </span>
          ${esc(entityLabel(result.entity_type))}
        </span>

        ${badge(result.verification_status)}
      </div>

      <div class="result-card-body">
        <h2>${esc(result.canonical_name)}</h2>
        <code>${esc(result.entity_id)}</code>
      </div>

      <div class="result-card-footer">
        <span>Details und Verbindungen ansehen</span>
        <span class="arrow" aria-hidden="true">→</span>
      </div>
    </a>
  `;
}

async function search(query = input.value.trim()) {
  results.innerHTML = "";

  if (!query) {
    status.textContent = "Suchbegriff eingeben.";
    return;
  }

  input.value = query;
  status.textContent = "Suche …";

  try {
    const data = await json(
      `/api/v1/search?q=${encodeURIComponent(query)}&include_unverified=${preview.checked}`,
    );

    status.textContent = data.length
      ? `${data.length} Ergebnis${data.length === 1 ? "" : "se"}`
      : "Keine passenden Datensätze.";

    results.innerHTML = data.map(renderSearchResult).join("");
  } catch (error) {
    status.textContent = `Fehler: ${error.message}`;
  }
}

function detailRows(details) {
  const skippedFields = new Set([
    "relationships",
    "variants",
    "maps",
    "sets",
    "loot_paths",
    "canonical_name",
    "slug",
    "verification_status",
    "entity_id",
    "entity_type",
  ]);

  const rows = Object.entries(details || {})
    .filter(([key, value]) => {
      return (
        !skippedFields.has(key) &&
        value !== null &&
        value !== "" &&
        typeof value !== "object"
      );
    })
    .slice(0, 16);

  if (!rows.length) {
    return `
      <p class="muted">
        Noch keine verifizierten Detailfelder vorhanden.
      </p>
    `;
  }

  return rows
    .map(
      ([key, value]) => `
        <div>
          <dt>${esc(formatLabel(key))}</dt>
          <dd>${esc(value)}</dd>
        </div>
      `,
    )
    .join("");
}

function normalizeRelationship(edge, currentEntityId, nodes) {
  const outgoing = edge.source_id === currentEntityId;
  const relatedEntityId = outgoing ? edge.target_id : edge.source_id;

  const relatedEntity = nodes[relatedEntityId] || {
    entity_id: relatedEntityId,
    canonical_name: relatedEntityId,
    entity_type: "ENTITY",
  };

  return {
    edge,
    outgoing,
    relatedEntityId,
    relatedEntity,
    group: edge.edge_type || "RELATED_TO",
  };
}

function groupRelationships(edges, currentEntityId, nodes) {
  const groups = new Map();

  edges
    .map((edge) => normalizeRelationship(edge, currentEntityId, nodes))
    .forEach((relationship) => {
      if (!groups.has(relationship.group)) {
        groups.set(relationship.group, []);
      }

      groups.get(relationship.group).push(relationship);
    });

  return [...groups.entries()].sort(([left], [right]) =>
    left.localeCompare(right),
  );
}

function renderRelationship(relationship) {
  const {
    edge,
    outgoing,
    relatedEntityId,
    relatedEntity,
  } = relationship;

  return `
    <a
      href="${entityUrl(relatedEntityId)}"
      class="connection"
    >
      <span class="direction" aria-hidden="true">
        ${outgoing ? "→" : "←"}
      </span>

      <span class="connection-icon" aria-hidden="true">
        ${entityIcon(relatedEntity.entity_type)}
      </span>

      <div class="connection-content">
        <strong>${esc(relatedEntity.canonical_name)}</strong>

        <small>
          ${esc(entityLabel(relatedEntity.entity_type))}
          ·
          ${outgoing ? "Ausgehend" : "Eingehend"}
        </small>
      </div>

      ${badge(edge.verification_status || "UNKNOWN")}
    </a>
  `;
}

function renderRelationshipGroups(edges, currentEntityId, nodes) {
  if (!edges.length) {
    return `
      <p class="muted">
        Noch keine Verbindungen erfasst.
      </p>
    `;
  }

  return groupRelationships(edges, currentEntityId, nodes)
    .map(
      ([edgeType, relationships]) => `
        <section class="relationship-group">
          <div class="relationship-group-title">
            <h3>${esc(formatLabel(edgeType))}</h3>
            <span>${relationships.length}</span>
          </div>

          <div class="connections">
            ${relationships.map(renderRelationship).join("")}
          </div>
        </section>
      `,
    )
    .join("");
}

function renderRelationshipSummary(edges, currentEntityId) {
  if (!edges.length) {
    return "";
  }

  const outgoingCount = edges.filter(
    (edge) => edge.source_id === currentEntityId,
  ).length;

  const incomingCount = edges.length - outgoingCount;

  return `
    <div class="relationship-summary">
      <span>
        <strong>${edges.length}</strong>
        Verbindungen
      </span>

      <span>
        <strong>${outgoingCount}</strong>
        ausgehend
      </span>

      <span>
        <strong>${incomingCount}</strong>
        eingehend
      </span>
    </div>
  `;
}

async function showEntity(id) {
  home.hidden = true;
  entity.hidden = false;

  entity.innerHTML = `
    <p class="status">
      Entity wird geladen …
    </p>
  `;

  try {
    const profile = await json(
      `/api/v1/entities/${encodeURIComponent(id)}?depth=2`,
    );

    const currentEntity = profile.entity;
    const edges = profile.graph?.edges || [];
    const graphNodes = profile.graph?.nodes || [];

    const nodes = Object.fromEntries(
      graphNodes.map((node) => [node.entity_id, node]),
    );

    entity.innerHTML = `
      <a class="back" href="#/">
        ← Zur Suche
      </a>

      <header class="entity-head">
        <div class="entity-title">
          <span class="entity-type">
            <span class="entity-icon" aria-hidden="true">
              ${entityIcon(currentEntity.entity_type)}
            </span>

            ${esc(entityLabel(currentEntity.entity_type))}
          </span>

          <h1>${esc(currentEntity.canonical_name)}</h1>
          <code>${esc(currentEntity.entity_id)}</code>
        </div>

        ${badge(currentEntity.verification_status)}
      </header>

      ${renderRelationshipSummary(edges, id)}

      <section class="panel">
        <div class="section-title">
          <h2>Überblick</h2>
          <span>${esc(entityLabel(currentEntity.entity_type))}</span>
        </div>

        <dl class="facts">
          ${detailRows(profile.details)}
        </dl>
      </section>

      <section class="panel">
        <div class="section-title">
          <h2>Verbindungen</h2>
          <span>${edges.length} Kanten</span>
        </div>

        <div class="relationship-groups">
          ${renderRelationshipGroups(edges, id, nodes)}
        </div>
      </section>
    `;

    document.title = `${currentEntity.canonical_name} · ARK Loot Bible`;
  } catch (error) {
    entity.innerHTML = `
      <a class="back" href="#/">
        ← Zur Suche
      </a>

      <p class="status">
        ${esc(error.message)}
      </p>
    `;
  }
}

function route() {
  const entityMatch = location.hash.match(/^#\/entity\/(.+)$/);

  if (entityMatch) {
    showEntity(decodeURIComponent(entityMatch[1]));
    return;
  }

  home.hidden = false;
  entity.hidden = true;
  document.title = "ARK Loot Bible";

  const query = new URLSearchParams(
    location.hash.split("?")[1] || "",
  ).get("q");

  if (query) {
    search(query);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const query = input.value.trim();

  if (!query) {
    return;
  }

  history.replaceState(
    null,
    "",
    `#/search?q=${encodeURIComponent(query)}`,
  );

  search(query);
});

window.addEventListener("hashchange", route);

json("/health")
  .then((health) => {
    $("#version").textContent = `v${health.version}`;
  })
  .catch(() => {});

route();