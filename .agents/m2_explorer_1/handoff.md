# Explorer 1 Handoff Report — Milestone 2: Atmospheric Fog Canvas Engine

## 1. Observation

### Codebase & Dependency Analysis
- **Dependencies (`frontend/package.json`)**:
  - `leaflet`: `^1.9.4`
  - `react-leaflet`: `^5.0.0`
  - `react`: `^19.2.7`
  - `@turf/turf`: `^7.3.5`
- **Current Fog Implementation (`frontend/src/App.jsx`)**:
  - Currently uses React Leaflet `<Polygon>` with Turf.js polygon union/dissolve (`turf.circle` + `turf.dissolve`).
  - Rendered via SVG overlay with `fillColor: '#1a1a1a'`, `fillOpacity: 0.88`, `fillRule: 'evenodd'`, `className: 'fog-blur'`.
  - Limitations of current SVG approach: Turf polygon union on every discovery click causes calculation lag, SVG stroke/blur CSS cannot produce multi-stage radial feathering, dark seam artifacts appear at circle boundaries, and cannot render noise texture.
- **Centralized Fog Configuration (`frontend/src/config/fogConfig.js`)**:
  - Exports `FOG_CONFIG` containing:
    - `discoveryRadiusMeters`: `150`
    - `duplicateThresholdMeters`: `50`
    - `fogColor`: `'#0f172a'`
    - `fogOpacity`: `0.88`
    - `clearCenterOpacity`: `0.0`
    - `edgeFeatherWidthPx`: `40`
    - `blendingMode`: `'destination-out'`
    - `enableNoise`: `true`
    - `noiseOpacity`: `0.045`

---

## 2. Logic Chain

### 2.1 Leaflet Canvas Overlay Architecture (`FogCanvasOverlay.jsx`)
To transition from heavy SVG polygon operations to a high-performance, 60 FPS HTML5 Canvas engine, we evaluate component design patterns for `react-leaflet` v5:

1. **React Leaflet Component Pattern**:
   - Create a functional component `<FogCanvasOverlay discoveredPoints={discoveredPoints} showFog={showFog} fogConfig={fogConfig} />` mounted inside `<MapContainer>`.
   - Access the active Leaflet map instance using the `useMap()` hook.

2. **DOM Canvas Mounting & Pane Placement**:
   - Create a `<canvas>` element dynamically inside a `useEffect` hook.
   - Attach canvas to a custom Leaflet pane: `map.createPane('fogPane')` with `zIndex: 450` (positioned above tilePane at `200` and overlayPane at `400`, but below markerPane at `600`).
   - Set `pane.style.pointerEvents = 'none'` and `canvas.style.pointerEvents = 'none'` so map clicks, dragging, and marker interactions pass directly through to Leaflet.
   - Position canvas: `position: absolute`, `top: 0`, `left: 0`, matching map container size.

3. **High-DPI / Retina Display Scaling (`window.devicePixelRatio`)**:
   - Retrieve `dpr = window.devicePixelRatio || 1`.
   - Get map pixel dimensions `size = map.getSize()`.
   - Set CSS display size: `canvas.style.width = `${size.x}px``, `canvas.style.height = `${size.y}px``.
   - Set internal backing store dimensions: `canvas.width = Math.round(size.x * dpr)`, `canvas.height = Math.round(size.y * dpr)`.
   - Scale 2D context by DPR: `ctx.scale(dpr, dpr)` during rendering to ensure pin-sharp rendering on High-DPI screens.

4. **Event Lifecycle & RAF Batching**:
   - Bind Leaflet map events: `map.on('move zoom viewreset resize moveend zoomend', handleMapEvent)`.
   - Use `requestAnimationFrame` (RAF) throttling for redraws so rapid `move` or `zoom` events during map panning only execute one canvas frame per refresh cycle.
   - Clean up event listeners and cancel pending RAF frame on component unmount.

### 2.2 Distance Projection (`metersToPixels`)
- Convert `fogConfig.discoveryRadiusMeters` (150m) into pixel radius `rPx` at any `(lat, lon)` on the map:
  ```js
  const getRadiusPx = (map, lat, lon, meters) => {
    const centerPoint = map.latLngToContainerPoint([lat, lon]);
    const earthRadius = 6378137;
    const dLon = (meters / (earthRadius * Math.cos((lat * Math.PI) / 180))) * (180 / Math.PI);
    const offsetPoint = map.latLngToContainerPoint([lat, lon + dLon]);
    return Math.hypot(offsetPoint.x - centerPoint.x, offsetPoint.y - centerPoint.y);
  };
  ```
- This accounts for Mercator scale variation across latitudes and zoom levels dynamically.

### 2.3 2D Canvas Composite Rendering Pipeline
1. **Offscreen Noise Canvas Pre-rendering**:
   - Create a static 256x256 offscreen canvas once (using `useMemo` or static cache).
   - Generate fine grain noise pixels: `imageData` with random grayscale alpha (`Math.random() * 255`).
   - Convert to `CanvasPattern`: `ctx.createPattern(noiseCanvas, 'repeat')`.

2. **Layer 1 — Unexplored Atmospheric Fog Fill**:
   - `ctx.clearRect(0, 0, width, height)`
   - Set base fog: `ctx.fillStyle = fogConfig.fogColor` (`#0f172a`), `ctx.globalAlpha = fogConfig.fogOpacity` (`0.88`).
   - `ctx.fillRect(0, 0, width, height)`.

3. **Layer 2 — Destination-Out Hole Punching with Radial Feathering**:
   - Set `ctx.globalCompositeOperation = 'destination-out'`.
   - Set `ctx.globalAlpha = 1.0`.
   - For each point in `discoveredPoints`:
     - Determine center point `(x, y) = map.latLngToContainerPoint([lat, lon])`.
     - Determine outer radius `rPx = getRadiusPx(map, lat, lon, fogConfig.discoveryRadiusMeters)`.
     - Determine inner crystal-clear radius `rInner = Math.max(0, rPx - fogConfig.edgeFeatherWidthPx)`.
     - Create radial gradient:
       `grad = ctx.createRadialGradient(x, y, rInner, x, y, rPx)`
       `grad.addColorStop(0.0, 'rgba(0, 0, 0, 1.0)')` (100% carved out, 0% fog opacity at center)
       `grad.addColorStop(0.7, 'rgba(0, 0, 0, 0.85)')` (smooth organic curve)
       `grad.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)')` (0% carved out, seamless transition to base fog)
     - `ctx.fillStyle = grad; ctx.beginPath(); ctx.arc(x, y, rPx, 0, Math.PI * 2); ctx.fill();`
   - *Why `destination-out` eliminates dark seams*: Subtraction of alpha across overlapping radial gradients merges additively in destination-out mode, guaranteeing zero seam artifacts and no inverted dark spots.

4. **Layer 3 — Organic Grain Noise Application**:
   - Set `ctx.globalCompositeOperation = 'source-atop'`.
   - Set `ctx.globalAlpha = fogConfig.noiseOpacity` (`0.045`).
   - Set `ctx.fillStyle = noisePattern`.
   - `ctx.fillRect(0, 0, width, height)`.
   - Reset `ctx.globalCompositeOperation = 'source-over'`.

---

## 3. Caveats

- **Leaflet Map Container Bounds**: Canvas position uses `latLngToContainerPoint`. Canvas must remain synced with map container size during window resizes (`resize` event).
- **React 19 Hooks Compatibility**: Ensure `useMap()` is called strictly within child components of `<MapContainer>`.
- **Large Dataset Scalability**: Iterating through `discoveredPoints` during `move` events is fast for thousands of points. For >10,000 points, viewport spatial filtering (`map.getBounds().contains()`) can be added to skip points outside visible map bounds.

---

## 4. Conclusion

The recommended architecture for `FogCanvasOverlay.jsx` relies on a React Leaflet functional component using `useMap()` with direct canvas DOM rendering attached to a custom `fogPane` (`zIndex: 450`, `pointerEvents: 'none'`).

Key design highlights:
- **Zero Seams & 100% Clear Center**: `destination-out` blending mode with multi-stage radial gradient (`0.0 -> 0.7 -> 1.0` stop curve).
- **60 FPS Performance**: RAF-throttled canvas rendering triggered by Leaflet map events (`move`, `zoom`, `viewreset`, `resize`).
- **High-DPI Support**: DPR scaling (`window.devicePixelRatio`) prevents blurriness on Retina displays.
- **Grain Texture**: Pre-rendered offscreen noise texture blended via `source-atop`.
- **Clean Lifecycle**: Automatic detachment of DOM canvas and map event handlers on unmount.

---

## 5. Verification Method

1. **Vite Build Verification**:
   Run `npm run build` inside `frontend/` to confirm zero JSX syntax or compilation errors.
2. **ESLint Verification**:
   Run `npm run lint` inside `frontend/` to ensure clean linting without unused variables or unhandled hooks.
3. **Pytest Verification**:
   Run `pytest` inside `backend/` to verify all backend tests pass without regression.
4. **Visual Inspection**:
   - Verify fog color is dark blue-gray (`#0f172a` / `rgba(15, 23, 42, 0.88)`).
   - Verify center of cleared circles is crystal clear (0% opacity fog).
   - Verify overlapping cleared circles do not produce dark seams or inverted circle artifacts.
