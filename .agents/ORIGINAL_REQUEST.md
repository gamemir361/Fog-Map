# Original User Request

## Initial Request — 2026-08-06T13:11:20Z

Enhance and tune the Fog of War system in the urban exploration web application into a premium, gaming-grade atmospheric fog with centralized tuning parameters.

Working directory: d:/Fog-Map-agy

## Requirements

### R1. Centralized Fog Configuration & Tunable Parameters
Extract all fog tuning parameters into a dedicated frontend configuration module (`fogConfig.js`), allowing dynamic adjustments to discovery radius, duplicate thresholds, colors, feathering, and opacity without modifying rendering code.

### R2. Atmospheric Visual Upgrade & Edge Feathering
Replace pure black/dark gray fog with a premium dark blue-gray atmospheric palette (`rgba(15, 23, 42, 0.88)` / `#0f172a`). Improve edge transitions with multi-stage radial feathering so that cleared areas remain 100% sharp and clear while the fog border transitions smoothly into a soft, organic cloud boundary.

### R3. Optimized Radius & Overlap Balance
Tune default discovery radius to ~150 meters (from 250m) while ensuring 50m duplicate discovery threshold produces a smooth, unbroken exploration trail without visual gaps or artifacts.

### R4. Canvas Performance & Subtle Noise Effect
Implement high-performance Canvas-based rendering with lightweight edge noise/grain effect for organic fog visuals while maintaining solid 60 FPS on desktop and mobile devices.

## Acceptance Criteria

### Visual Quality & Design
- [ ] Fog color matches dark blue-gray palette (`#0f172a` / `rgba(15, 23, 42, 0.88)`).
- [ ] Center of explored circles remains 100% crystal clear (0% opacity fog).
- [ ] Fog edge features a soft multi-step feather gradient (width 30-50px).
- [ ] No visual dark seams or inverted overlapping circle artifacts exist when multiple discoveries overlap.

### Centralized Config & Engineering
- [ ] `fogConfig.js` (or `fogConfig.ts`) contains all tunable parameters (`discoveryRadiusMeters`, `duplicateThresholdMeters`, `edgeFeatherWidth`, `fogOpacity`, `fogColor`, `blendingMode`).
- [ ] Modifying parameters in `fogConfig.js` immediately updates map rendering and discovery behavior.

### Performance & Backward Compatibility
- [ ] Smooth 60 FPS map panning and zooming.
- [ ] Saved user discovery points continue to load and render seamlessly.
- [ ] Backend integration tests (`pytest`) and frontend Vite build (`npm run build`) pass cleanly.
