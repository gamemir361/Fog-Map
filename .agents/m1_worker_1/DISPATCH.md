## 2026-08-13T15:21:34Z
<USER_REQUEST>
You are Worker 1 (teamwork_preview_worker) executing Milestone 1 (M1: UrbanExplorer Tokens, CSS Variables & Typography Scale) for the Fog Map frontend.

Working Directory: d:/Fog-Map-agy/.agents/m1_worker_1
Original Request File: d:/Fog-Map-agy/.agents/ORIGINAL_REQUEST.md
Project Plan File: d:/Fog-Map-agy/PROJECT.md
Explorer Survey Handoff: d:/Fog-Map-agy/.agents/explorer_survey_1/handoff.md

Instructions:
1. MUST read `d:/Fog-Map-agy/.agents/ORIGINAL_REQUEST.md` and `d:/Fog-Map-agy/PROJECT.md` first.
2. Read Explorer 1's detailed findings in `d:/Fog-Map-agy/.agents/explorer_survey_1/handoff.md`.
3. File ownership: You exclusively own `frontend/src/index.css` and `frontend/index.html`. Do not touch other files.
4. Implement the following in `frontend/src/index.css`:
   - Google Fonts `@import`: Import `Fira Sans` (weights 400, 500, 600, 700, 800), `Inter` (weights 300, 400, 500, 600, 700), and `Vazirmatn` (weights 300, 400, 500, 700, 900) with `display=swap`.
   - Dark Mode Tokens (`:root`):
     `--md-sys-color-primary: #89ceff;`
     `--md-sys-color-primary-container: #0ea5e9;`
     `--md-sys-color-surface: #0f1418;`
     `--md-sys-color-surface-container-high: #1b2024;`
     `--md-sys-color-vibrant-emerald: #10b981;`
     `--md-sys-color-amber-gold: #f59e0b;`
     `--bg-dark: var(--md-sys-color-surface);`
     `--panel-glass: rgba(27, 32, 36, 0.82);`
     `--panel-border: rgba(137, 206, 255, 0.15);`
     `--accent-cyan: var(--md-sys-color-primary);`
     `--accent-emerald: var(--md-sys-color-vibrant-emerald);`
     `--accent-amber: var(--md-sys-color-amber-gold);`
     `--text-main: #f8fafc;`
     `--text-sub: #94a3b8;`
     `--font-heading: 'Fira Sans', 'Vazirmatn', sans-serif;`
     `--font-body: 'Inter', 'Vazirmatn', sans-serif;`
     `--font-tech: 'Inter', 'Vazirmatn', sans-serif;`
   - Light Mode Tokens (`[data-theme="light"]`):
     `--md-sys-color-primary: #0284c7;`
     `--md-sys-color-primary-container: #e0f2fe;`
     `--md-sys-color-surface: #f8fafc;`
     `--md-sys-color-surface-container-high: #ffffff;`
     `--md-sys-color-vibrant-emerald: #059669;`
     `--md-sys-color-amber-gold: #d97706;`
     `--bg-dark: var(--md-sys-color-surface);`
     `--panel-glass: rgba(255, 255, 255, 0.88);`
     `--panel-border: rgba(14, 165, 233, 0.2);`
     `--accent-cyan: var(--md-sys-color-primary);`
     `--text-main: #0f172a;`
     `--text-sub: #475569;`
   - Glassmorphism Panel Base:
     Update `.glass-panel` to set `backdrop-filter: blur(12px);` and `-webkit-backdrop-filter: blur(12px);`, background: `var(--panel-glass)`, border: `1px solid var(--panel-border)`.
   - Typography Utility Classes:
     Set `h1, h2, h3, h4, h5, h6, .font-heading` to use `font-family: var(--font-heading);`.
     Set `.tech-badge, .metadata-tag, .font-tech` to use `font-family: var(--font-tech);`.
5. Integrity Requirement:
   DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
6. Run `npm run build` inside `d:/Fog-Map-agy/frontend` to verify clean build output.
7. Write your full report to `d:/Fog-Map-agy/.agents/m1_worker_1/handoff.md` and update `progress.md`.
8. Send a message to parent with build status and summary.
</USER_REQUEST>
