# Project: UrbanExplorer Design System Integration

## Architecture
- `frontend/src/index.css`: Material 3 tokens, font imports (Fira Sans, Inter, Vazirmatn), glassmorphism styles (`blur(12px)`), responsive HUD safe-zone variables (`--hud-safe-zone`), marker pulse/glow animations, typography scale (`--font-heading`, `--font-tech`), 300ms transitions.
- `frontend/src/App.jsx`: Responsive HUD layout (24px desktop / 12px mobile safe-zones), 340px desktop side drawer / floating mobile sheet, 44x44px hit targets on all controls/pills/buttons, theme switching alignment (`data-theme`), glass panel layering.
- `frontend/src/components/*`: POI popups, AuthModal, TrackingConfirmModal, LandingPage styled with frosted glass, Fira Sans titles, Inter badges, 300ms transitions.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | M3 Color Tokens & CSS Variables | Define Material 3 color tokens (#89ceff, #0ea5e9, #0f1418, surface-container-high, vibrant-emerald, amber-gold) for Light/Dark themes in index.css | M1 | R1, AC1 |
| 2 | Fira Sans & Inter Typography Scale | Google Fonts loading for Fira Sans (headings) and Inter (technical badges/metadata) in index.css | M1 | R1, AC2 |
| 3 | Frosted Glassmorphism Utility | Standardized .glass-panel backdrop-filter: blur(12px) and border styling | M1 | R1, AC3 |
| 4 | Responsive HUD Safe-Zone Spacing | Safe-Zone spacing variables (24px desktop / 12px mobile) applied across top bar, quick actions, switcher, toast, nudge | M2 | R2, AC3 |
| 5 | Side Drawer Responsive Refactor | 340px desktop side drawer transitioning to floating mobile sheet on narrow viewports | M2 | R2, AC3 |
| 6 | 44x44px Touch Targets | Resize all interactive map control buttons, category pills, search toggles, hamburger menu, and marker targets to >= 44x44px | M2 | R2, AC4 |
| 7 | Smooth 300ms Transitions | Add standard 300ms transitions for theme toggling, drawer slides, button hovers, and UI panels | M3 | R3, AC3 |
| 8 | Map Marker Pulse/Glow Animations | CSS keyframe glow/pulse animation for map markers and active category highlights | M3 | R3, AC3 |
| 9 | POI Popup & Modal Polish | Refactor POI popups, AuthModal, TrackingConfirmModal, and LandingPage with typography scale, glassmorphism, and Light/Dark mode token alignment | M3 | R3, AC1-3 |
| 10| Clean Vite Build Verification | Ensure npm run build completes cleanly with zero errors | M3 | AC5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Tokens, CSS Variables & Typography | M3 color tokens, Fira Sans & Inter font loading, index.css CSS variables, glassmorphism base | none | DONE |
| 2 | M2: Responsive HUD Safe-Zones & 44x44px Touch Targets | Responsive 24px/12px safe zones, 340px desktop/mobile drawer, 44x44px hit targets across controls | M1 | IN_PROGRESS |
| 3 | M3: Micro-Interactions, Theme Alignment & Build Verification | 300ms transitions, marker animations, popup/modal polish, Light/Dark mode completion, npm run build | M2 | PLANNED |

## Interface Contracts
### CSS Theme Variable Interface (`index.css` ↔ Components)
- `:root` (Dark Mode):
  - `--md-sys-color-primary`: `#89ceff`
  - `--md-sys-color-primary-container`: `#0ea5e9`
  - `--md-sys-color-surface`: `#0f1418`
  - `--md-sys-color-surface-container-high`: `#1b2024`
  - `--md-sys-color-vibrant-emerald`: `#10b981`
  - `--md-sys-color-amber-gold`: `#f59e0b`
  - `--font-heading`: `'Fira Sans', 'Vazirmatn', sans-serif`
  - `--font-tech`: `'Inter', 'Vazirmatn', sans-serif`
  - `--hud-safe-zone`: `24px` (desktop) / `12px` (mobile `@media (max-width: 768px)`)
- `[data-theme="light"]`:
  - `--md-sys-color-primary`: `#0284c7`
  - `--md-sys-color-primary-container`: `#e0f2fe`
  - `--md-sys-color-surface`: `#f8fafc`
  - `--md-sys-color-surface-container-high`: `#ffffff`
  - `--md-sys-color-vibrant-emerald`: `#059669`
  - `--md-sys-color-amber-gold`: `#d97706`

## Code Layout
- `frontend/src/index.css`
- `frontend/src/App.jsx`
- `frontend/src/components/AuthModal.jsx`
- `frontend/src/components/TrackingConfirmModal.jsx`
- `frontend/src/components/LandingPage.jsx`
- `frontend/index.html`
