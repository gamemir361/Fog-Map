# Fog of War E2E & Integrated Test Infrastructure Specification

## 1. Overview & Test Methodology

This document outlines the testing architecture, feature inventory, tier requirements, and verification methodology for the Fog of War System Enhancement in the urban exploration web application (`Fog-Map-agy`).

### Testing Methodology & Philosophy
- **Progressive Testability**: Tests are designed to validate currently available features as well as contract requirements for upcoming milestone components.
- **Independence & Isolation**: Each test case operates independently with isolated user IDs, preventing test-order dependencies and side effects.
- **Authoritative Expected Output Derivation**: Math calculations (e.g., Haversine distance formulas, circle area formulas $\pi \times r^2$, PostGIS EWKT geometries) are derived from mathematical specifications and project documentation (`PROJECT.md`, `ORIGINAL_REQUEST.md`).
- **Multi-Tier Validation Architecture**: Testing is organized into four distinct tiers ranging from low-level unit and configuration validation to full E2E parameter boundary testing and visual system contract verification.

---

## 2. Feature Inventory & Coverage Mapping

| # | Feature | Requirements / Specifications | Scope Tier | Key Test Verification Points |
|---|---------|-------------------------------|------------|------------------------------|
| 1 | **Centralized Fog Config** | `fogConfig.js` containing `FOG_CONFIG` (`discoveryRadiusMeters: 150`, `duplicateThresholdMeters: 50`, `fogColor: '#0f172a'`, `fogOpacity: 0.88`, `clearCenterOpacity: 0.0`, `edgeFeatherWidthPx: 40`, `blendingMode: 'destination-out'`, `enableNoise: true`, `noiseOpacity: 0.045`) | Tier 1, Tier 4 | Config schema completeness, parameter types, numerical boundaries, hex color validity. |
| 2 | **Backend Config Sync & Pytest Fix** | Update backend radius to 150.0m, update fallback sqm formula ($150^2 \times \pi = 70685.8347$), maintain 50.0m duplicate threshold, configure `pytest.ini` with `pythonpath = .` | Tier 1, Tier 2, Tier 3 | Haversine distance accuracy, default radius behavior, duplicate point filtering (<50m vs >50m), `pytest` execution stability. |
| 3 | **Atmospheric Canvas Overlay Engine** | `#0f172a` palette, multi-stage radial gradient edge feathering (30-50px), `destination-out` composite mode, 0% fog opacity at circle center | Tier 4 | Component props interface contract, blending mode specification, radial feathering parameter checks. |
| 4 | **Subtle Noise Effect & Performance** | Pre-rendered offscreen static noise tile, `source-atop` mapping, `enableNoise: true`, `noiseOpacity: 0.045` | Tier 4 | Noise toggle validity, noise opacity ranges, overlay layer layering contract. |
| 5 | **Integration & Code Quality** | API routes `/api/v1/fog/discover` & `/api/v1/fog/stats`, user gamification integration, backward compatibility with existing user discovery points | Tier 2, Tier 3 | API response status codes, payload contracts, score accumulation (+10 vs +0), PostGIS / SQLite fallback handling. |

---

## 3. Tier Requirements Breakdown

### Tier 1: Unit & Config Validation Tests
Focuses on individual helper functions, mathematical formulas, and static configuration files.
- **Haversine Distance Accuracy**: Verifies `get_distance_meters(lat1, lon1, lat2, lon2)` produces precise meter distances across short (~10-50m) and long (~100-1000m) geographic spans.
- **Fallback Area Calculation Math**: Validates area formula for 150.0m radius circle ($A = \pi \times 150^2 = 70685.8347\,\text{m}^2$) and legacy 250.0m circle ($A = 196349.54\,\text{m}^2$).
- **Frontend Config Contract Validation**: Tests `frontend/src/config/fogConfig.js` exported values against expected schema and bounds.

### Tier 2: Integration & API Endpoint Tests
Focuses on backend HTTP endpoints and database repository interactions.
- **`POST /api/v1/fog/discover` - First Discovery**: Verifies 200 OK, `status: "success"`, user points incremented by +10, and `coverage_stats` returned.
- **`POST /api/v1/fog/discover` - Duplicate Discovery (<50m)**: Verifies discovery within 50.0 meters of an existing centroid awards +0 points, keeps `areas_discovered` unchanged, and returns friendly Iranian Persian message ("مه به آرامی کنار رفت...").
- **`POST /api/v1/fog/discover` - Distinct Discovery (>50m)**: Verifies discovery >50.0 meters away awards +10 points, increments `areas_discovered`, and updates total coverage.
- **`GET /api/v1/fog/stats` - Coverage Payload**: Verifies response payload structure including `user_id`, `areas_discovered_count`, `total_area_sqm`, `total_area_sqkm`, `city_coverage_percentage`, `all_points`, and `geojson_geometry`.
- **Multi-User Isolation**: Ensures discoveries by one user do not pollute or alter scores/coverage of another user.

### Tier 3: E2E & Parameter Boundary Tests
Focuses on end-to-end user exploration scenarios, boundary conditions, and spatial overlap balance.
- **Duplicate Threshold Exact Boundary Testing**: Tests behavior at ~49.5m (duplicate threshold triggered) versus ~50.5m (new area discovered) relative to reference points.
- **150m Radius Spatial Coverage & Fallback Math**: Validates radius parameter passing (150.0m) and coverage area math across single and multiple discoveries.
- **Sequential Route Exploration Path**: Simulates a continuous street exploration trail (5 discovery points spaced 60m apart), verifying total accumulated score (= 50 points), centroid count (= 5), and progressive coverage expansion.
- **PostGIS EWKT & Fallback Resilience**: Tests repository polygon generation and coverage calculations under both PostGIS geography buffers and standard fallback geometry models.

### Tier 4: Visual/Performance & System Contract Verification
Focuses on design specifications, component prop interfaces, and cross-tier configuration synchronization.
- **Color Palette & Atmospheric Spec**: Validates `fogColor` equals `#0f172a` (dark blue-gray palette), `fogOpacity` equals `0.88`, and `clearCenterOpacity` equals `0.0`.
- **Feathering & Blending Specs**: Validates `edgeFeatherWidthPx` equals `40` (within required 30-50px range) and `blendingMode` equals `'destination-out'`.
- **Noise Effect Configuration**: Validates `enableNoise` equals `true` and `noiseOpacity` equals `0.045`.
- **Canvas Overlay Contract**: Validates `FogCanvasOverlay` required props (`discoveredPoints`, `showFog`, `fogConfig`) and Leaflet map event bindings.
- **Backend-Frontend Radius Alignment**: Verifies 150m radius parameter consistency between frontend `fogConfig.js` and backend `service.py`/`repository.py`.

---

## 4. Test Suite Structure & Execution Instructions

### Directory & File Structure
```
backend/
├── pytest.ini                            # Configured with pythonpath = .
├── run_e2e_tests.py                      # Dedicated E2E Test Suite Runner with Tier reporting
└── tests/
    └── integration/
        ├── test_fog_config_e2e.py        # Comprehensive Tiers 1-4 Test Suite
        ├── test_fog_router.py            # Basic fog router integration tests
        ├── test_exploration_router.py    # POI search and spatial query tests
        ├── test_missions_router.py       # Mission engine tests
        ├── test_routing_router.py        # Route planning tests
        └── test_users_router.py          # User profile tests
```

### Execution Commands
1. **Run Full Backend Pytest Suite**:
   ```bash
   cd backend
   pytest
   ```

2. **Run Dedicated E2E Test Suite with Tier Breakdown**:
   ```bash
   cd backend
   python run_e2e_tests.py
   ```

3. **Run Specific Fog E2E Tests**:
   ```bash
   cd backend
   pytest tests/integration/test_fog_config_e2e.py -v
   ```
