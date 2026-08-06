## 2026-08-06T10:11:18Z
You are teamwork_preview_worker for Milestone 3 (Map Integration & Code Cleanup).
Your working directory is: d:/Fog-Map-agy/.agents/worker_m3_1

MANDATORY READS:
- ORIGINAL_REQUEST.md: d:/Fog-Map-agy/.agents/ORIGINAL_REQUEST.md
- PROJECT.md: d:/Fog-Map-agy/PROJECT.md
- Explorer 1 Analysis: d:/Fog-Map-agy/.agents/explorer_m3_1/analysis.md
- Explorer 2 Analysis: d:/Fog-Map-agy/.agents/explorer_m3_2/analysis.md

WRITE OWNERSHIP:
You have exclusive write ownership for:
- frontend/src/App.jsx
- frontend/src/components/FogCanvasOverlay.jsx

TASKS:
1. In frontend/src/App.jsx:
   - Import FOG_CONFIG from './config/fogConfig' and FogCanvasOverlay from './components/FogCanvasOverlay'.
   - Remove Polygon from react-leaflet import list and remove `import * as turf from '@turf/turf'`.
   - Remove outerWorldRing declaration and fogPositions useMemo block.
   - Inside <MapContainer>, replace the Leaflet SVG <Polygon ... /> with:
     <FogCanvasOverlay discoveredPoints={discoveredPoints} showFog={showFog} fogConfig={FOG_CONFIG} />
   - Extract MapClicker component outside of the App component definition to fix React hooks nested component ESLint warning (pass props: pickingLocationFor, onSelectOrigin, onSelectDest, onDiscoverPoint).
   - Render routeMetrics & routeWaypoints in the UI drawer routing panel so route distance (km) and estimated duration (minutes) are displayed, eliminating the unused-vars ESLint warning.
   - Fix any synchronous setState inside effects in App.jsx if highlighted by ESLint.

2. In frontend/src/components/FogCanvasOverlay.jsx:
   - Remove unused React import from line 1 (`import React, { ... }` -> `import { useEffect, useRef, useCallback } from 'react'`).
   - Wrap `drawFog` function in `useCallback` (depending on discoveredPoints, showFog, fogConfig) or ensure `useEffect` dependencies pass ESLint without `react-hooks/exhaustive-deps` warning.

3. VERIFICATION & TESTS:
   - Run `npm run lint` in frontend directory. Ensure 0 errors and 0 warnings.
   - Run `npm run build` in frontend directory. Ensure clean Vite build with zero errors.
   - Run `pytest` in backend directory. Ensure 31/31 tests pass.
   - Run `python backend/run_e2e_tests.py` if present.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

4. REPORTING:
   - Write your changes and test/build command outputs to d:/Fog-Map-agy/.agents/worker_m3_1/changes.md and handoff.md.
   - Send a message back with your verification results.
