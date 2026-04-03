# Issues — Frontend Theme Redesign

(none yet)

- 2026-03-30 plan compliance audit: `.sisyphus/evidence/` is empty, so T1 baseline artifacts and T8 final evidence bundle are missing despite being required deliverables.
- 2026-03-30 plan compliance audit: `frontend/src/components/spectra-chart.tsx` still contains hardcoded `oklch(...)` values at lines 160, 167, 172, 178, 183, 189-196, and 202, which violates T8 hotspot-closure acceptance criteria.
- 2026-03-30 plan compliance audit: `frontend/src/app/layout.tsx` keeps the full brand plus three full nav labels in one non-responsive row (`layout.tsx:33`, `layout.tsx:44`), so the mobile nav-readability requirement from T3/T8 is not convincingly met.
