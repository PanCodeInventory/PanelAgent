# Learnings — Frontend Theme Redesign

## 2026-03-30 Initialization
- Previous dark theme ("SpectroLab Dark") was rejected by user as "太丑了"
- Second attempt ("Electric Blue + Copper") was also rejected — uncommitted changes reverted
- User approved "Paper Platform + slight Editorial Science" direction
- Light-first, academic publication feel is the target
- Must preserve all existing functionality — pure visual redesign only

## 2026-03-30 T1: Hardcoded Color Hotspot Inventory

### frontend/src/app/page.tsx (6 hotspots — decorative HSL orbs)
- Line 17: `bg-[hsl(217,91%,60%)]/20` — blue orb
- Line 18: `bg-[hsl(330,81%,60%)]/20` — pink orb
- Line 19: `bg-[hsl(160,84%,39%)]/15` — green orb
- Line 20: `bg-[hsl(45,93%,47%)]/15` — amber orb
- Line 21: `bg-[hsl(270,91%,65%)]/20` — purple orb
- Line 22: `bg-[hsl(12,76%,61%)]/15` — red/orange orb
- ACTION: Remove all decorative orbs entirely (Paper Platform = no decorative particles)

### frontend/src/app/exp-design/page.tsx (4 hotspots — type badge colors)
- Lines 40-55: `getTypeBadgeColor()` function:
  - `bg-blue-500/10 text-blue-400 border-blue-500/30` — lineage
  - `bg-emerald-500/10 text-emerald-400 border-emerald-500/30` — activation
  - `bg-amber-500/10 text-amber-400 border-amber-500/30` — exhaustion
  - `bg-purple-500/10 text-purple-400 border-purple-500/30` — functional
- ACTION: Replace with semantic token-aligned subdued colors

### frontend/src/app/panel-design/page.tsx (2 hotspot groups)
- Lines 41-45: `getBrightnessColor()` function:
  - `bg-emerald-400` (brightness >= 4)
  - `bg-yellow-400` (brightness >= 3)
  - `bg-red-400` (brightness < 3)
- Lines 242-261: Missing markers warning card:
  - `border-yellow-500/20 bg-yellow-500/5`
  - `text-yellow-400`, `text-yellow-200/70`
  - `border-yellow-500/50 text-yellow-400`
- Line 469: `text-yellow-400` in diagnosis header
- ACTION: Replace brightness dots with token-based semantic colors; replace yellow-500 warning with subdued token warning

### frontend/src/components/spectra-chart.tsx (2 hotspot groups)
- Lines 141-153: Warning block (same yellow-500 pattern as panel-design)
- Lines 158-201: Chart rendering hardcoded oklch values:
  - Grid: `stroke="oklch(0.3 0.02 250 / 20%)"`
  - Ticks: `fill: "oklch(0.6 0.05 250)"`
  - Labels: `fill: "oklch(0.6 0.05 250)"`
  - Tooltip bg: `oklch(0.18 0.025 255)` (dark navy!)
  - Tooltip border: `oklch(0.4 0.02 250 / 15%)`
  - Tooltip text: `oklch(0.96 0.005 250)` (near-white)
  - Legend: `oklch(0.96 0.005 250)`
- ACTION: Replace yellow-500 warnings with token warnings; replace dark oklch with light-first chart colors

### globals.css (glow/glass utilities to reduce)
- Lines 86-88: `--glow-primary`, `--glow-accent` CSS variables
- Lines 147-167: `.glow-primary`, `.glow-accent`, `.glass`, `.glass-border` utility classes
- ACTION: Reduce glow effects; glass → paper-panel surfaces

- 2026-03-30 plan audit learning: the T8 hotspot grep allows token definitions in `globals.css` and runtime `series.color`, but not chart-level inline `oklch(...)` styling constants in `spectra-chart.tsx`.
