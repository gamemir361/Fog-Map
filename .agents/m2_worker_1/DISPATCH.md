## 2026-08-13T12:05:21Z
You are Worker 1 for Milestone 2 (teamwork_preview_worker) implementing Responsive HUD Safe-Zones, Side Drawer Refactor, and 44x44px Touch Targets for the Fog Map frontend.

Working Directory: d:/Fog-Map-agy/.agents/m2_worker_1
Original Request File: d:/Fog-Map-agy/.agents/ORIGINAL_REQUEST.md
Project Plan File: d:/Fog-Map-agy/PROJECT.md
Explorer 2 Survey Handoff: d:/Fog-Map-agy/.agents/explorer_survey_2/handoff.md

Instructions:
1. MUST read `d:/Fog-Map-agy/.agents/ORIGINAL_REQUEST.md` and `d:/Fog-Map-agy/PROJECT.md` first.
2. Read Explorer 2's detailed findings in `d:/Fog-Map-agy/.agents/explorer_survey_2/handoff.md`.
3. File ownership: You exclusively own `frontend/src/App.jsx` and `frontend/src/index.css`. Do not break existing map rendering or fog overlays.
4. Implement the following requirements:
   - **Responsive HUD Safe-Zone Spacing**:
     - In `index.css`: Add `--hud-safe-zone: 24px;` under `:root` and `--hud-safe-zone: 12px;` under `@media (max-width: 768px)`.
     - In `App.jsx`: Update floating HUD overlays (Top Bar, Quick Action Stack, Map Style Switcher, Status Toast Banner, Ambient Nudge) to use `var(--hud-safe-zone)` for offsets (top, bottom, left, right) instead of fixed 16px/20px offsets.
   - **Side Drawer Responsive Refactor**:
     - In `App.jsx` and/or `index.css`: Maintain `340px` desktop width anchored right. On mobile viewports (`@media (max-width: 768px)` or mobile drawer class `.mobile-bottom-sheet`), transition the side drawer into a floating mobile bottom sheet (full width `width: calc(100% - 2 * var(--hud-safe-zone))`, `left: var(--hud-safe-zone)`, `right: var(--hud-safe-zone)`, `bottom: var(--hud-safe-zone)`, `max-height: 80vh`, `border-radius: 20px`).
   - **44x44px Minimum Touch Targets (Acceptance Criterion 4)**:
     - Resize ALL interactive control buttons to have at least `min-width: 44px` and `min-height: 44px` (or `44x44px` touch targets):
       - Quick Action Stack buttons (Drawer toggle, Theme toggle, Center Tehran button): `width: 44px, height: 44px` (line 1058).
       - Search Mode toggle buttons (POIs vs Streets): minimum height `44px` / `padding: 10px 14px` (lines 618, 630).
       - Search Clear button (✕): minimum size `44x44px` hit target area (line 659).
       - Hamburger Drawer Toggle (☰): minimum size `44x44px` target area (line 672).
       - Category Pills: minimum height `44px` / `min-h-[44px]` with flex centering and touch padding (line 747).
       - Map Theme Switcher buttons (Google / Satellite / Carto): minimum height `44px` / hit target `44x44px` (line 1092).
       - Side Drawer buttons (Mode pickers, Route plan button, Close button ✕): minimum hit target area `44x44px`.
       - Leaflet POI Map Marker Icons (`createCustomCategoryIcon`): update divIcon `iconSize` to `[44, 44]` and `iconAnchor` to `[22, 22]` so touch targets meet the 44x44px standard on map taps.
   - **Glass Panel Layering & M3 Token Integration**:
     - Ensure floating containers use `.glass-panel` and leverage M3 theme variables (`var(--panel-glass)`, `var(--panel-border)`, `var(--text-main)`, `var(--text-sub)`).
5. Integrity Requirement:
   DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
6. Run `npm run build` inside `d:/Fog-Map-agy/frontend` to verify clean build output.
7. Write your full report to `d:/Fog-Map-agy/.agents/m2_worker_1/handoff.md` and update `progress.md`.
8. Send a message to parent with build status and summary.
