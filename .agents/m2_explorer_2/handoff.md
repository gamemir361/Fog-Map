# Handoff Report: Atmospheric Fog Canvas Engine (Canvas 2D Math & Seam Elimination)

## 1. Observation

### Codebase & Configuration Analysis
- **`frontend/src/config/fogConfig.js`**: Contains centralized parameters:
  - `discoveryRadiusMeters`: 150
  - `duplicateThresholdMeters`: 50
  - `fogColor`: `'#0f172a'` (Dark blue-gray slate)
  - `fogOpacity`: 0.88
  - `clearCenterOpacity`: 0.0 (100% crystal clear center)
  - `edgeFeatherWidthPx`: 40
  - `blendingMode`: `'destination-out'`
  - `enableNoise`: true
  - `noiseOpacity`: 0.045
- **Current `App.jsx` implementation**: Uses Leaflet SVG `<Polygon>` with `evenodd` fill rule (lines 791-800). This approach lacks smooth radial gradient feathering, produces hard polygon edges, and causes performance drops on high point counts.
- **Goal for Milestone 2 (`FogCanvasOverlay.jsx`)**: Replace SVG polygon rendering with a high-performance Leaflet Canvas 2D overlay utilizing multi-stop radial gradients, single-pass `destination-out` compositing, and an offscreen static noise texture.

---

## 2. Logic Chain

### Step 1: Latitude & Zoom-Dependent Pixel Radius Calculation
To convert `discoveryRadiusMeters` (150m) to container pixel radius $R_{px}$ across all map zoom levels and latitude positions:
1. One degree of latitude corresponds to approximately $111,320 \text{ meters}$ anywhere on Earth:
   $$\Delta \text{lat} = \frac{R_m}{111,320} = \frac{150}{111,320} \approx 0.00134745^\circ$$
2. Using Leaflet's `map.latLngToContainerPoint`:
   - $P_{\text{center}} = \text{map.latLngToContainerPoint}([\text{lat}, \text{lon}])$
   - $P_{\text{edge}} = \text{map.latLngToContainerPoint}([\text{lat} + \Delta \text{lat}, \text{lon}])$
   - $R_{px} = \text{Math.hypot}(P_{\text{edge}}.x - P_{\text{center}}.x, \, P_{\text{edge}}.y - P_{\text{center}}.y)$
3. This calculation automatically incorporates Leaflet's zoom scale factor $2^z$ and Mercator latitude contraction ($\cos(\text{lat})$) without manual projection matrix math.

### Step 2: Multi-Stage Radial Gradient Edge Feathering Math
1. **Dynamic Feather Guard**:
   At low zoom levels where $R_{px} \le 40\text{px}$, the feather width must scale down proportionally to prevent $r_{\text{inner}} < 0$:
   $$W_{\text{feather}} = \min(\text{edgeFeatherWidthPx}, \, R_{px} \times 0.8)$$
   $$r_{\text{inner}} = \max(0, \, R_{px} - W_{\text{feather}})$$
   $$r_{\text{outer}} = R_{px}$$
2. **Radial Gradient Construction**:
   $$\text{grad} = \text{maskCtx.createRadialGradient}(x, y, r_{\text{inner}}, x, y, r_{\text{outer}})$$
3. **Multi-Stop S-Curve Alpha Transitions**:
   To produce a gaming-grade organic cloud edge with 100% crystal clear circle centers (0% fog opacity):
   - `0.00`: `rgba(255, 255, 255, 1.00)` — Center core (Fully cleared)
   - `0.25`: `rgba(255, 255, 255, 0.92)` — Inner feather shoulder
   - `0.60`: `rgba(255, 255, 255, 0.45)` — Midpoint transition
   - `0.85`: `rgba(255, 255, 255, 0.15)` — Outer feather tail
   - `1.00`: `rgba(255, 255, 255, 0.00)` — Unexplored boundary (Untouched fog)

### Step 3: Zero Dark Seam Artifact Elimination via Two-Pass Mask Canvas
- **Root Cause of Seam Artifacts**: Calling `destination-out` iteratively on the main fog canvas for each discovery circle causes multiplicative alpha subtraction:
  $$\alpha_{\text{final}} = \alpha_{\text{fog}} \times (1 - \alpha_1) \times (1 - \alpha_2)$$
  In overlapping feather regions, this compounding double-subtraction cuts fog opacity twice as deep, creating noticeable light leaks or dark seam halos along overlap boundaries.
- **Two-Pass Compositing Solution**:
  1. **Pass 1 (Mask Canvas)**: Maintain an offscreen canvas (`maskCanvas`) matching the viewport dimensions. Draw all discovery radial gradients onto `maskCanvas` using `maskCtx.globalCompositeOperation = 'lighter'`. Overlapping circles additively merge into a unified mask intensity $A_{\text{mask}}(x,y) \in [0.0, 1.0]$.
  2. **Pass 2 (Main Canvas Punch)**: Fill `mainCanvas` with solid atmospheric fog color (`#0f172a`, opacity 0.88). Perform a single `ctx.globalCompositeOperation = 'destination-out'` operation drawing `maskCanvas` onto `mainCanvas`:
     $$\alpha_{\text{fog, final}}(x,y) = \alpha_{\text{fog, initial}} \times (1 - A_{\text{mask}}(x,y))$$
  3. **Result**: Zero multiplicative compounding, zero seam artifacts, 100% smooth merged discovery shapes.

### Step 4: Offscreen Static Grain Noise Overlay
1. Pre-render a 256x256 static noise canvas once (`noiseCanvasRef`).
2. After punching holes with `destination-out`, set `mainCtx.globalCompositeOperation = 'source-atop'`.
3. Draw noise pattern (`ctx.createPattern(noiseCanvas, 'repeat')`) at `fogConfig.noiseOpacity` (0.045).
4. `source-atop` ensures noise grain is rendered **only** on unexplored fog clouds ($\alpha > 0$) and never inside cleared discovery holes ($\alpha = 0$).

### Step 5: 60 FPS Performance & Spatial Culling Optimization
1. **Spatial Culling**: Calculate bounding box of current map viewport with a 2x discovery radius margin ($P_{\text{margin}} \approx 2 \times \Delta \text{lat}$). Discard points outside bounds before canvas rendering.
2. **Buffer Persistence**: Keep `canvasRef`, `maskCanvasRef`, and `noiseCanvasRef` persistent. Reallocate canvas dimensions only when `map.getSize()` changes.
3. **Leaflet Event Hooks**: Bind `drawFog` to Leaflet map events: `'move zoom viewreset resize'`.

---

## 3. Caveats

1. **High-DPI Display Scaling (Retina)**:
   - On screens with `devicePixelRatio > 1` (e.g. mobile phones or Mac Retina), Canvas 2D default DPR scale can cause slight fuzziness if canvas dimensions are not scaled by `window.devicePixelRatio`.
   - *Recommendation*: Set `canvas.width = size.x * dpr` and `ctx.scale(dpr, dpr)` if crisp rendering on mobile screens is desired.
2. **Empty Discovery Array**:
   - If `discoveredPoints` is empty `[]`, `FogCanvasOverlay` should render full solid dark blue-gray fog covering the entire canvas.
3. **Data Format Normalization**:
   - `discoveredPoints` from API or state may contain either tuples `[lat, lon]` or objects `{ lat, lon }`. The component must check both formats safely:
     `const lat = Array.isArray(pt) ? pt[0] : (pt.lat ?? pt[0]);`

---

## 4. Conclusion & Implementation Blueprint

We recommend implementing `FogCanvasOverlay.jsx` with the following clean, self-contained architecture:

```jsx
import React, { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import FOG_CONFIG from '../config/fogConfig';

/**
 * FogCanvasOverlay - Atmospheric Canvas 2D Fog of War Overlay Component
 *
 * Renders gaming-grade dark blue-gray fog (#0f172a) with multi-stage radial feathering,
 * zero-seam destination-out hole punching, and offscreen static noise overlay.
 */
export const FogCanvasOverlay = ({
  discoveredPoints = [],
  showFog = true,
  fogConfig = FOG_CONFIG,
}) => {
  const map = useMap();
  const canvasRef = useRef(null);
  const maskCanvasRef = useRef(null);
  const noiseCanvasRef = useRef(null);

  // Initialize offscreen mask and noise canvases
  useEffect(() => {
    if (!maskCanvasRef.current) {
      maskCanvasRef.current = document.createElement('canvas');
    }

    // Pre-render static 256x256 noise canvas
    const noiseCanvas = document.createElement('canvas');
    noiseCanvas.width = 256;
    noiseCanvas.height = 256;
    const nCtx = noiseCanvas.getContext('2d');
    const imgData = nCtx.createImageData(256, 256);
    const noiseAlpha = Math.floor(255 * (fogConfig.noiseOpacity ?? 0.045));

    for (let i = 0; i < imgData.data.length; i += 4) {
      const val = Math.floor(Math.random() * 255);
      imgData.data[i] = val;     // R
      imgData.data[i + 1] = val; // G
      imgData.data[i + 2] = val; // B
      imgData.data[i + 3] = noiseAlpha;
    }
    nCtx.putImageData(imgData, 0, 0);
    noiseCanvasRef.current = noiseCanvas;
  }, [fogConfig.noiseOpacity]);

  // Main Fog Canvas Drawing Function
  const drawFog = () => {
    const canvas = canvasRef.current;
    if (!canvas || !showFog) return;

    const ctx = canvas.getContext('2d');
    const size = map.getSize();
    const dpr = window.devicePixelRatio || 1;

    // Synchronize Canvas Dimensions
    if (canvas.width !== size.x * dpr || canvas.height !== size.y * dpr) {
      canvas.width = size.x * dpr;
      canvas.height = size.y * dpr;
    }

    const maskCanvas = maskCanvasRef.current;
    if (maskCanvas.width !== size.x * dpr || maskCanvas.height !== size.y * dpr) {
      maskCanvas.width = size.x * dpr;
      maskCanvas.height = size.y * dpr;
    }

    const maskCtx = maskCanvas.getContext('2d');

    // Reset scales & clear frames
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    maskCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.clearRect(0, 0, size.x, size.y);
    maskCtx.clearRect(0, 0, size.x, size.y);

    // Step A: Fill main canvas with solid atmospheric fog color
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = fogConfig.fogColor || '#0f172a';
    ctx.globalAlpha = fogConfig.fogOpacity ?? 0.88;
    ctx.fillRect(0, 0, size.x, size.y);

    if (!discoveredPoints || discoveredPoints.length === 0) return;

    // Step B: Build merged discovery mask on maskCanvas using 'lighter'
    maskCtx.globalCompositeOperation = 'lighter';

    const bounds = map.getBounds();
    const radiusMeters = fogConfig.discoveryRadiusMeters || 150;
    const featherWidthPx = fogConfig.edgeFeatherWidthPx ?? 40;

    const latDelta = radiusMeters / 111320;
    const padLat = latDelta * 2;
    const padLon = latDelta * 2;

    for (let i = 0; i < discoveredPoints.length; i++) {
      const pt = discoveredPoints[i];
      const lat = Array.isArray(pt) ? pt[0] : (pt.lat ?? pt[0]);
      const lon = Array.isArray(pt) ? pt[1] : (pt.lon ?? pt[1]);

      if (lat === undefined || lon === undefined) continue;

      // Spatial viewport culling
      if (
        lat < bounds.getSouth() - padLat ||
        lat > bounds.getNorth() + padLat ||
        lon < bounds.getWest() - padLon ||
        lon > bounds.getEast() + padLon
      ) {
        continue;
      }

      const centerPt = map.latLngToContainerPoint([lat, lon]);
      const edgePt = map.latLngToContainerPoint([lat + latDelta, lon]);
      const rPx = Math.hypot(edgePt.x - centerPt.x, edgePt.y - centerPt.y);

      if (rPx <= 0) continue;

      const feather = Math.min(featherWidthPx, rPx * 0.8);
      const rInner = Math.max(0, rPx - feather);
      const rOuter = rPx;

      const grad = maskCtx.createRadialGradient(
        centerPt.x, centerPt.y, rInner,
        centerPt.x, centerPt.y, rOuter
      );

      grad.addColorStop(0.00, 'rgba(255, 255, 255, 1.00)');
      grad.addColorStop(0.25, 'rgba(255, 255, 255, 0.92)');
      grad.addColorStop(0.60, 'rgba(255, 255, 255, 0.45)');
      grad.addColorStop(0.85, 'rgba(255, 255, 255, 0.15)');
      grad.addColorStop(1.00, 'rgba(255, 255, 255, 0.00)');

      maskCtx.fillStyle = grad;
      maskCtx.beginPath();
      maskCtx.arc(centerPt.x, centerPt.y, rOuter, 0, Math.PI * 2);
      maskCtx.fill();
    }

    // Step C: Punch merged holes in main fog canvas via destination-out
    ctx.globalCompositeOperation = fogConfig.blendingMode || 'destination-out';
    ctx.globalAlpha = 1.0;
    ctx.drawImage(maskCanvas, 0, 0, size.x, size.y);

    // Step D: Apply noise overlay on remaining fog clouds using source-atop
    if (fogConfig.enableNoise && noiseCanvasRef.current) {
      ctx.globalCompositeOperation = 'source-atop';
      ctx.globalAlpha = 1.0;
      const pattern = ctx.createPattern(noiseCanvasRef.current, 'repeat');
      if (pattern) {
        ctx.fillStyle = pattern;
        ctx.fillRect(0, 0, size.x, size.y);
      }
    }

    // Reset composite operation
    ctx.globalCompositeOperation = 'source-over';
  };

  useEffect(() => {
    drawFog();

    let animationFrameId;
    const handleMapChange = () => {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = requestAnimationFrame(drawFog);
    };

    map.on('move zoom viewreset resize', handleMapChange);
    return () => {
      cancelAnimationFrame(animationFrameId);
      map.off('move zoom viewreset resize', handleMapChange);
    };
  }, [map, discoveredPoints, showFog, fogConfig]);

  if (!showFog) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 400,
      }}
    />
  );
};

export default FogCanvasOverlay;
```

---

## 5. Verification Method

To verify the implementation independently once built by Implementer 1:

1. **Frontend Build Check**:
   Run `npm run build` inside `frontend/` to ensure syntax, React hooks, and Leaflet event bindings pass without compilation or bundler errors.
2. **Visual Verification on Map**:
   - Check that center of cleared discovery circles shows 100% underlying tile map (0% fog opacity).
   - Verify fog edge displays a soft 40px feather gradient transitioning smoothly to dark blue-gray `#0f172a`.
   - Click multiple adjacent map locations to form overlapping circles: confirm zero dark seams or light leak artifacts exist at circle intersections.
3. **Parameter Tuning Invalidation Check**:
   - Change `discoveryRadiusMeters` to `200` or `edgeFeatherWidthPx` to `60` in `fogConfig.js` and verify map overlay instantly reflects updated radius and feather width without code changes.
