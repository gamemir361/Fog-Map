# Handoff Report: Milestone 3 Map Integration & Code Cleanup Analysis

## 1. Observation
Direct observations of source files in `d:/Fog-Map-agy`:

- **`frontend/src/App.jsx`**:
  - Line 2: Imports `Polygon` from `react-leaflet`: `import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap, Polyline, Polygon } from 'react-leaflet'`.
  - Line 7: Imports `@turf/turf`: `import * as turf from '@turf/turf'`.
  - Lines 10–16: Defines `const outerWorldRing = [...]`.
  - Lines 114–115: Defines unused state variables `const [routeWaypoints, setRouteWaypoints] = useState([])` and `const [routeMetrics, setRouteMetrics] = useState(null)`.
  - Lines 240–266: Computes `fogPositions` `useMemo` block using `turf.circle` (0.25km) and `turf.dissolve`.
  - Lines 269–316: Defines `MapClicker` component inline inside `App` render body, causing React hook static-component re-declaration on every render.
  - Lines 790–803: Renders SVG Leaflet `<Polygon key={discoveredPoints.length} positions={fogPositions} ... />`.

- **`frontend/src/config/fogConfig.js`**:
  - Exports frozen `FOG_CONFIG` object with parameters: `discoveryRadiusMeters: 150`, `duplicateThresholdMeters: 50`, `fogColor: '#0f172a'`, `fogOpacity: 0.88`, `clearCenterOpacity: 0.0`, `edgeFeatherWidthPx: 40`, `blendingMode: 'destination-out'`, `enableNoise: true`, `noiseOpacity: 0.045`.

- **`frontend/src/components/FogCanvasOverlay.jsx`**:
  - Defines `FogCanvasOverlay` component accepting `discoveredPoints`, `showFog`, and `fogConfig` props.
  - Uses HTML5 2D Canvas with two-pass composite rendering (`lighter` mask canvas + `destination-out` single pass blit) to achieve 0% center fog opacity, smooth radial edge feathering, and static noise grain overlay.

---

## 2. Logic Chain
1. **SVG Leaflet Polygon Replacement**:
   - The current `<Polygon>` in `App.jsx` relies on `turf.dissolve` to combine circle polygons. It suffers from seam artifacts, lacks edge feathering, and computes heavy geo-polygons on every discovery change.
   - `FogCanvasOverlay` replaces `<Polygon>` seamlessly inside `<MapContainer>` by taking `discoveredPoints`, `showFog`, and `fogConfig={FOG_CONFIG}` as props.
   - Removing `<Polygon>` eliminates the need for `@turf/turf`, `outerWorldRing`, and `fogPositions` in `App.jsx`, streamlining memory and CPU usage.

2. **Inline `MapClicker` Extraction**:
   - Defining `MapClicker` inside `App` causes React to re-instantiate the component on every `App` re-render. This violates React best practices and triggers ESLint warnings (`react/no-unstable-nested-components`).
   - Extracting `MapClicker` outside `App` and passing `pickingLocationFor` and callback props (`onSelectOrigin`, `onSelectDest`, `onDiscoverPoint`) fixes the warning and ensures stable component lifecycle.

3. **Unused State Variables (`routeWaypoints` & `routeMetrics`)**:
   - `routeWaypoints` and `routeMetrics` are updated in `handleDualPlanRoute` but omitted from JSX rendering, causing ESLint `no-unused-vars` warnings.
   - Adding a route details card in the UI drawer renders these metrics to the user, enhancing app features and resolving the warning.

---

## 3. Caveats
- `FogCanvasOverlay` depends on Leaflet map instance context (`useMap`). It must be rendered as a child of `<MapContainer>`.
- If custom fog tuning parameters are needed in the future, they should be updated in `fogConfig.js` rather than passed inline.

---

## 4. Conclusion
Replacing SVG Leaflet `<Polygon>` with `<FogCanvasOverlay>` and extracting `MapClicker` outside `App` with UI display of `routeMetrics` will resolve all M3 requirements cleanly, achieve 60 FPS Canvas rendering, and pass ESLint and Vite build checks without warnings.

---

## 5. Verification Method
1. **Files to Inspect**:
   - `frontend/src/App.jsx`
   - `frontend/src/config/fogConfig.js`
   - `frontend/src/components/FogCanvasOverlay.jsx`
2. **Build and Test Verification**:
   - `cd frontend && npm run build` (Must complete with exit code 0 and no ESLint errors/warnings).
   - `cd backend && pytest` (Must pass all integration tests).
3. **Invalidation Conditions**:
   - If `<Polygon>` or `@turf/turf` remains imported in `App.jsx`.
   - If `MapClicker` remains defined inside `App`.
   - If `npm run build` fails or outputs ESLint warnings for unused variables.
