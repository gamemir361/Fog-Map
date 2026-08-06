# Project: Fog of War System Enhancement

## Architecture
- `frontend/src/config/fogConfig.js`: Centralized configuration module exporting `FOG_CONFIG` containing all fog parameters (`discoveryRadiusMeters`, `duplicateThresholdMeters`, `fogColor`, `fogOpacity`, `edgeFeatherWidthPx`, `clearCenterOpacity`, `blendingMode`, `enableNoise`, `noiseOpacity`).
- `frontend/src/components/FogCanvasOverlay.jsx`: Custom Leaflet Canvas overlay component rendering atmospheric dark blue-gray fog (`#0f172a` / `rgba(15, 23, 42, 0.88)`). Uses `ctx.globalCompositeOperation = 'destination-out'` with multi-stage radial gradient edge feathering (30-50px width) to guarantee 0% fog opacity at circle centers and eliminate dark seam artifacts when circles overlap. Includes an offscreen pre-rendered 256x256 static noise canvas tiled over fog areas using `source-atop` at 60 FPS.
- `frontend/src/App.jsx`: Main application component; imports `FOG_CONFIG`, replaces SVG Leaflet `<Polygon>` with `FogCanvasOverlay`, fixes ESLint errors (`MapClicker` component extraction, unused variables `routeWaypoints` & `routeMetrics`).
- `backend/app/modules/fog_of_war/service.py` & `repository.py`: Updates default discovery radius from 250.0m to 150.0m and fallback sqm calculation formula (`pi * 150^2` = 70685.8), maintaining 50.0m duplicate threshold.
- `backend/pytest.ini`: Configures `pythonpath = .` to enable direct `pytest` execution.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Centralized Fog Config | `fogConfig.js` containing all tunable parameters | M1 | R1, AC1 |
| 2 | Backend Config Sync & Pytest Fix | Update backend default radius to 150.0m, update fallback sqm calculation, add `pythonpath = .` to `pytest.ini` | M1 | R3, AC3 |
| 3 | Atmospheric Canvas Overlay Engine | `FogCanvasOverlay.jsx` with canvas rendering, `#0f172a` palette, multi-stage radial gradient edge feathering, destination-out hole punching (0% center opacity, zero seam artifacts) | M2 | R2, R4, AC2 |
| 4 | Subtle Noise Effect & Performance Tuning | Pre-rendered offscreen noise tile mapped with `source-atop`, maintaining 60 FPS panning/zooming | M2 | R4, AC4 |
| 5 | Integration & Code Quality Hardening | Replace SVG polygon in `App.jsx` with `FogCanvasOverlay`, fix ESLint errors (`MapClicker`, unused state), ensure saved user discovery points load/render smoothly | M3 | R3, AC3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Config & Backend Alignment | `fogConfig.js`, backend 150m radius sync, `pytest.ini` fix | none | DONE |
| 2 | M2: Atmospheric Fog Canvas Engine | `FogCanvasOverlay.jsx` implementation (radial feathering, noise effect, destination-out masking) | M1 | DONE |
| 3 | M3: Map Integration & Code Cleanup | `App.jsx` integration, ESLint fixes, backward compatibility verification | M2 | PLANNED |

## Interface Contracts
### `fogConfig.js` ↔ Map Components & Services
- Exports `FOG_CONFIG`:
  ```javascript
  export const FOG_CONFIG = {
    discoveryRadiusMeters: 150,
    duplicateThresholdMeters: 50,
    fogColor: '#0f172a',
    fogOpacity: 0.88,
    clearCenterOpacity: 0.0,
    edgeFeatherWidthPx: 40,
    blendingMode: 'destination-out',
    enableNoise: true,
    noiseOpacity: 0.045,
  };
  export default FOG_CONFIG;
  ```

### `FogCanvasOverlay.jsx` ↔ Leaflet Map (`App.jsx`)
- Props: `discoveredPoints` (array of `[lat, lon]` or `{lat, lon}`), `showFog` (boolean), `fogConfig` (object).
- Listens to Leaflet events (`move`, `zoom`, `viewreset`) and redrawing directly on Canvas 2D context.

## Code Layout
- `frontend/src/config/fogConfig.js`
- `frontend/src/components/FogCanvasOverlay.jsx`
- `frontend/src/App.jsx`
- `backend/pytest.ini`
- `backend/app/modules/fog_of_war/service.py`
- `backend/app/modules/fog_of_war/repository.py`
- `backend/app/modules/exploration/models.py`
