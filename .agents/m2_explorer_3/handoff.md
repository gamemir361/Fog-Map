# Handoff Report: Offscreen Noise Generator & Canvas Overlay Performance Design

**Agent**: Explorer 3 (`teamwork_preview_explorer`)  
**Milestone**: M2 (Atmospheric Fog Canvas Engine)  
**Target File**: `frontend/src/components/FogCanvasOverlay.jsx`  

---

## 1. Observation

1. **Centralized Configuration**:
   - `frontend/src/config/fogConfig.js` (lines 20–30) exports `FOG_CONFIG`:
     ```javascript
     export const FOG_CONFIG = Object.freeze({
       discoveryRadiusMeters: 150,
       duplicateThresholdMeters: 50,
       fogColor: '#0f172a',
       fogOpacity: 0.88,
       clearCenterOpacity: 0.0,
       edgeFeatherWidthPx: 40,
       blendingMode: 'destination-out',
       enableNoise: true,
       noiseOpacity: 0.045,
     });
     ```
2. **Current Map Fog Rendering**:
   - `frontend/src/App.jsx` (lines 790–800) uses a React-Leaflet `<Polygon>` with `fillRule: 'evenodd'` and a CSS blur effect. SVG multi-ring polygon calculations (`turf.dissolve`) cause CPU bottlenecks during pan/zoom and lack custom compositing support for grain/noise layers.
3. **Project Architecture Specifications**:
   - `PROJECT.md` (line 5 & lines 38–40) specifies replacing the SVG polygon with `FogCanvasOverlay.jsx`, an offscreen pre-rendered 256x256 static noise canvas tiled over fog areas using `source-atop` at 60 FPS with `noiseOpacity: 0.045`.

---

## 2. Logic Chain

1. **Noise Tile Generation**:
   - **Reasoning**: Generating procedural noise per frame across a full-screen canvas (e.g., 1920x1080 = 2,073,600 pixels) requires calling `Math.random()` over 2 million times per frame, causing severe frame drops (< 15 FPS).
   - **Solution**: Pre-generate a 256x256 HTML5 canvas tile once at component mount using 32-bit typed array manipulation (`Uint32Array` or `Uint8ClampedArray`). Store the canvas pattern in a persistent ref (`noisePatternRef`) created via `ctx.createPattern(noiseCanvas, 'repeat')`.

2. **Canvas Composite Pass Architecture**:
   - **Step 1 (`source-over`)**: Fill visible canvas with solid atmospheric dark blue-gray (`rgba(15, 23, 42, 0.88)` / `fogColor` + `fogOpacity`).
   - **Step 2 (`destination-out`)**: For each discovered point within visible bounds, draw a multi-stage radial gradient circle. The gradient transitions from `rgba(0,0,0,1)` at the inner core (0% center opacity) to `rgba(0,0,0,0)` at `radiusPx`, creating soft organic edge feathering without dark seams when circles overlap.
   - **Step 3 (`source-atop`)**: Set `ctx.globalCompositeOperation = 'source-atop'`, set `ctx.fillStyle = noisePatternRef.current`, and execute `ctx.fillRect(0, 0, width, height)`.
   - **Reasoning**: `source-atop` draws the noise pattern ONLY where existing pixels are non-transparent. Where circles were cut out (`destination-out`, alpha = 0.0), noise will NOT be drawn. The noise opacity automatically scales with fog alpha along feathered edges.

3. **60 FPS Pan/Zoom Optimizations**:
   - **rAF Throttling**: Leaflet `move` and `zoom` events fire up to 100+ times per second. Wrapping the render call in `requestAnimationFrame` ensures at most 1 render pass per screen refresh frame (60 Hz / 120 Hz).
   - **Offscreen Double Buffering**: Draw the multi-pass sequence (`source-over` -> `destination-out` -> `source-atop`) into an offscreen canvas, then copy the result to the main map overlay canvas in a single `drawImage` call. This prevents visual flickering.
   - **Spatial Viewport Culling**: Filter `discoveredPoints` against `map.getBounds().pad(0.1)` so points outside the visible map viewport (+ 10% padding margin) are excluded from the circle rendering loop.
   - **Zero Per-Frame Allocation**: Reuse offscreen canvas instances, avoid re-instantiating `CanvasPattern` or arrays inside the animation loop.

---

## 3. Caveats

- **Device Pixel Ratio (DPR)**: High-DPI screens (Retina displays, mobile screens with DPR 2x or 3x) require scaling the canvas width/height by `window.devicePixelRatio` and context scaling by `dpr` to keep grain sharp and edges crisp without blur.
- **Leaflet Map Container Resize**: Resizing the browser window requires syncing canvas attributes (`width`, `height`) with the Leaflet map container dimensions.

---

## 4. Conclusion & Implementation Recommendations

`FogCanvasOverlay.jsx` should be implemented with the following architecture:

### 4.1 Offscreen Noise Generator (`createNoisePattern`)

```javascript
import { useEffect, useRef } from 'react';
import L from 'leaflet';

/**
 * Pre-renders a 256x256 static noise canvas tile and returns a CanvasPattern.
 */
export function createNoisePattern(ctx, size = 256, opacity = 0.045) {
  const noiseCanvas = document.createElement('canvas');
  noiseCanvas.width = size;
  noiseCanvas.height = size;
  const noiseCtx = noiseCanvas.getContext('2d');
  
  const imgData = noiseCtx.createImageData(size, size);
  const data32 = new Uint32Array(imgData.data.buffer);
  const alphaInt = Math.round(opacity * 255) << 24;
  
  for (let i = 0; i < data32.length; i++) {
    const val = (Math.random() * 255) | 0;
    // ABGR layout (Little Endian): Alpha in MSB, Blue, Green, Red
    data32[i] = alphaInt | (val << 16) | (val << 8) | val;
  }
  
  noiseCtx.putImageData(imgData, 0, 0);
  return ctx.createPattern(noiseCanvas, 'repeat');
}
```

### 4.2 Composite Pass Rendering & Optimizations

```javascript
/**
 * Main offscreen render routine executed on requestAnimationFrame.
 */
function renderFogLayer({
  offscreenCtx,
  visibleCtx,
  width,
  height,
  dpr,
  map,
  discoveredPoints,
  fogConfig,
  noisePattern,
}) {
  const {
    fogColor = '#0f172a',
    fogOpacity = 0.88,
    discoveryRadiusMeters = 150,
    edgeFeatherWidthPx = 40,
    enableNoise = true,
  } = fogConfig;

  // 1. Clear offscreen buffer
  offscreenCtx.clearRect(0, 0, width * dpr, height * dpr);
  offscreenCtx.save();
  offscreenCtx.scale(dpr, dpr);

  // 2. Base Fog Fill (source-over)
  offscreenCtx.globalCompositeOperation = 'source-over';
  offscreenCtx.fillStyle = fogColor;
  offscreenCtx.globalAlpha = fogOpacity;
  offscreenCtx.fillRect(0, 0, width, height);
  offscreenCtx.globalAlpha = 1.0;

  // 3. Hole Punch Discovered Areas (destination-out)
  offscreenCtx.globalCompositeOperation = 'destination-out';

  // Spatial Culling: only draw points within current viewport + 10% pad
  const bounds = map.getBounds().pad(0.1);
  const zoom = map.getZoom();
  const centerLat = map.getCenter().lat;

  // Calculate radius in pixels for 150 meters at current zoom/latitude
  const targetLatLng = L.latLng(centerLat, map.getCenter().lng);
  const destLatLng = L.GeometryUtil 
    ? L.GeometryUtil.destination(targetLatLng, 90, discoveryRadiusMeters)
    : L.latLng(centerLat, map.getCenter().lng + (discoveryRadiusMeters / 111320) / Math.cos(centerLat * Math.PI / 180));
  
  const p1 = map.latLngToContainerPoint(targetLatLng);
  const p2 = map.latLngToContainerPoint(destLatLng);
  const radiusPx = Math.max(15, Math.hypot(p2.x - p1.x, p2.y - p1.y));
  const innerRadiusPx = Math.max(0, radiusPx - edgeFeatherWidthPx);

  for (let i = 0; i < discoveredPoints.length; i++) {
    const pt = discoveredPoints[i];
    const lat = Array.isArray(pt) ? pt[0] : pt.lat;
    const lng = Array.isArray(pt) ? pt[1] : pt.lon;

    if (!bounds.contains([lat, lng])) continue;

    const point = map.latLngToContainerPoint([lat, lng]);

    const grad = offscreenCtx.createRadialGradient(
      point.x, point.y, innerRadiusPx,
      point.x, point.y, radiusPx
    );
    grad.addColorStop(0, 'rgba(0, 0, 0, 1)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    offscreenCtx.fillStyle = grad;
    offscreenCtx.beginPath();
    offscreenCtx.arc(point.x, point.y, radiusPx, 0, Math.PI * 2);
    offscreenCtx.fill();
  }

  // 4. Noise Grain Overlay (source-atop)
  if (enableNoise && noisePattern) {
    offscreenCtx.globalCompositeOperation = 'source-atop';
    offscreenCtx.fillStyle = noisePattern;
    offscreenCtx.fillRect(0, 0, width, height);
  }

  offscreenCtx.restore();

  // 5. Flip offscreen buffer to visible canvas
  visibleCtx.clearRect(0, 0, width * dpr, height * dpr);
  visibleCtx.drawImage(offscreenCtx.canvas, 0, 0);
}
```

### 4.3 60 FPS Event Throttling Hook

```javascript
// Schedule rendering using requestAnimationFrame
const rAFRef = useRef(null);

const scheduleRedraw = useCallback(() => {
  if (rAFRef.current !== null) return;
  rAFRef.current = requestAnimationFrame(() => {
    rAFRef.current = null;
    renderFogLayer(/* params */);
  });
}, [/* dependencies */]);

// Leaflet event hooks
useMapEvents({
  move: scheduleRedraw,
  zoom: scheduleRedraw,
  viewreset: scheduleRedraw,
  resize: scheduleRedraw,
});
```

---

## 5. Verification Method

1. **Build Verification**:
   - Run `npm run build` in `frontend/` to ensure no JSX/syntax or bundle compilation errors.
2. **Visual Inspection**:
   - Verify that non-explored map areas present a dark blue-gray `#0f172a` overlay with subtle uniform grain noise.
   - Verify that discovered circular areas cut through fog down to 0% opacity with smooth edge feathering.
   - Verify that noise grain appears strictly on remaining fog areas and NEVER inside cleared circles.
3. **Performance Verification**:
   - Use browser DevTools Performance Panel during rapid map panning and zooming:
     - Frame rate maintains 60 FPS (frame time < 16.6ms).
     - Garbage collection pauses are minimized (zero per-frame array/canvas allocations).
