# Handoff Report: Fog Parameter & Configuration Survey

**Agent**: `explorer_survey_2` (survey explorer)  
**Task**: Centralized Fog Configuration & Parameter Survey  
**Date**: 2026-08-06  

---

## 1. Observation

### 1.1 Code Locations of Fog Parameters
- **Discovery Radius**:
  - `frontend/src/App.jsx:247`: `turf.circle([lon, lat], 0.25, { steps: 24, units: 'kilometers' })` — Hardcoded radius of `0.25` km (250 meters).
  - `backend/app/modules/exploration/models.py:18`: `radius = Column(Float, default=0.25)` — Default column value of 0.25 km.
  - `backend/app/modules/fog_of_war/service.py:36`: `repo.add_fog_discovery(user_id, lat, lon, radius_meters=250.0)` — Default parameter 250.0m.
  - `backend/app/modules/fog_of_war/repository.py:25`: `def add_fog_discovery(..., radius_meters: float = 250.0)`
  - `backend/app/modules/fog_of_war/repository.py:66`: Fallback sqm calculation `total_sqm = len(centroids) * 196349.5` (`pi * 250.0^2`).

- **Duplicate Discovery Threshold**:
  - `backend/app/modules/exploration/service.py:145`:
    ```python
    if get_distance_meters(lat, lon, area.lat, area.lon) < 50.0:
        should_give_points = False
        break
    ```
    Hardcoded 50.0 meters check for awarding XP points (`should_give_points`).
  - `backend/app/modules/fog_of_war/service.py:32`:
    ```python
    if distance < 50.0:
        should_give_points = False
        break
    ```

- **Fog Color**:
  - `frontend/src/App.jsx:796`: `fillColor: '#1a1a1a'` — Currently dark charcoal gray instead of target dark blue-gray palette (`#0f172a` / `rgba(15, 23, 42, 0.88)`).

- **Fog Opacity**:
  - `frontend/src/App.jsx:797`: `fillOpacity: 0.88`.

- **Blending Mode / Edge Feathering**:
  - `frontend/src/App.jsx:798-800`: `fillRule: 'evenodd'`, `className: 'fog-blur'`.
  - `frontend/src/index.css:135-139`:
    ```css
    .fog-blur {
      filter: blur(14px);
      pointer-events: none;
      transition: all 0.5s ease-in-out;
    }
    ```

### 1.2 Interactive Exploration Flow
1. User clicks map (`App.jsx:270-313`), firing `axios.post('/api/v1/exploration/fog/discover', { user_id: 1, lat, lon })`.
2. Backend checks distances to previous discovered points. If distance < 50m, `should_give_points = False` (0 XP delta).
3. Backend records point in database and returns `all_points` list `[{"lat": ..., "lon": ...}]`.
4. Frontend updates `discoveredPoints` state (`App.jsx:299-302`).
5. `useMemo` (`fogPositions` at `App.jsx:240-266`) generates turf circles for each point, dissolves them via `turf.dissolve`, prepends `outerWorldRing` (global inverted mask), and passes positions to Leaflet `<Polygon>` with `fillRule: 'evenodd'`.

### 1.3 Saved Discovery Data & Compatibility
- Database table `discovered_areas` stores `id`, `user_id`, `lat`, `lon`, `radius`, `discovered_at`.
- Table `user_fog_maps` stores PostGIS `unfogged_geometry` polygons.
- Frontend receives array of points `[{lat, lon}]` and re-generates Leaflet fog circles dynamically using Turf.js on each render.

### 1.4 Test Suite & Build Verification
- Command `$env:PYTHONPATH="."; pytest` in `backend` returned:
  `16 passed, 4 warnings in 9.77s`.
- Command `npm run build` in `frontend` returned:
  `✓ built in 253ms` producing `dist/index.html`, `dist/assets/index-BX08Aonx.css` (17.89 kB), `dist/assets/index-D-jkJPMn.js` (464.63 kB).

---

## 2. Logic Chain

1. **Parameter Location & Hardcoding**:
   - Observations 1.1 show that discovery radius (250m / 0.25km) and duplicate threshold (50m) are currently hardcoded directly inside component rendering code (`App.jsx`), ORM models (`models.py`), and backend service methods (`service.py`).
   - Fog color (`#1a1a1a`) and opacity (`0.88`) are hardcoded in `App.jsx` pathOptions.

2. **Radius Reduction (250m -> 150m) & Overlap Balance**:
   - At 150m discovery radius and 50m duplicate threshold, two discovery points spaced 50m apart will have circle centers 50m apart. Since each circle has radius 150m, the overlap between consecutive circles is `(2 * 150) - 50 = 250 meters`.
   - Therefore, a 50m duplicate threshold ensures complete circle overlap with zero visual gaps or disconnected islands along an exploration path.

3. **Backward Compatibility Guarantee**:
   - Observation 1.3 confirms that saved user discovery points in `discovered_areas` store raw coordinate pairs (`lat`, `lon`).
   - When historical points are fetched via `GET /api/v1/fog/stats` or returned via `POST /api/v1/exploration/fog/discover`, the frontend calculates circle polygons dynamically using `FOG_CONFIG.discoveryRadiusMeters`.
   - Modifying the discovery radius to 150m in `fogConfig.js` will immediately and seamlessly update the rendered map radius for both historical and newly created discovery points without requiring any database schema migration or data transformation.

4. **Centralized Config Module Architecture**:
   - Creating `frontend/src/config/fogConfig.js` (or `.ts`) consolidates all visual and procedural parameters into a single source of truth:
     ```javascript
     export const FOG_CONFIG = {
       discoveryRadiusMeters: 150,
       duplicateThresholdMeters: 50,
       fogColor: '#0f172a',
       fogOpacity: 0.88,
       clearCenterOpacity: 0.0,
       edgeFeatherWidth: 40,
       blendingMode: 'evenodd',
       enableNoise: true,
       noiseOpacity: 0.04,
     };
     export default FOG_CONFIG;
     ```
   - Standard import path: `import FOG_CONFIG from './config/fogConfig'` (or `@/config/fogConfig`).

---

## 3. Caveats

- PostGIS fallback logic in `backend/app/modules/fog_of_war/repository.py:66` uses `196349.5` (`pi * 250^2`) for non-PostGIS fallback coverage area estimations. When backend default radius is updated to 150m, this fallback formula should be updated to `pi * 150^2` (`70685.8` sqm).
- Leaflet SVG `<Polygon>` with `filter: blur(14px)` provides soft edges, but for high-frequency noise/grain effect or multi-stage radial gradient feathering (Requirement R2/R4), a dedicated HTML5 `<canvas>` layer component or SVG filter element will yield superior performance and visual quality.

---

## 4. Conclusion

1. **Fog Parameters**: All 5 target parameters (radius, duplicate threshold, opacity, color, blending mode) are identified and isolated.
2. **Radius & Threshold**: Reducing radius from 250m to 150m while maintaining 50m duplicate threshold produces continuous overlapping circles with smooth visual coverage.
3. **Backward Compatibility**: Fully preserved. Stored points contain `(lat, lon)` coordinates; rendering logic re-computes Turf circles on-the-fly.
4. **Config Location**: Place `fogConfig.js` at `frontend/src/config/fogConfig.js`. Import directly into `App.jsx` or specialized `FogLayer` canvas components.

---

## 5. Verification Method

To verify these findings and check project integrity:

1. **Run Backend Tests**:
   ```powershell
   cd d:/Fog-Map-agy/backend
   $env:PYTHONPATH="."
   pytest
   ```
   *Expected Result*: All 16 tests pass.

2. **Run Frontend Production Build**:
   ```powershell
   cd d:/Fog-Map-agy/frontend
   npm run build
   ```
   *Expected Result*: Clean build without TypeScript/JSX syntax errors.

3. **Inspect File References**:
   - Check `frontend/src/App.jsx` at line 247 (`0.25` km) and line 796 (`#1a1a1a`).
   - Check `backend/app/modules/exploration/service.py` at line 145 (`50.0` meters).
