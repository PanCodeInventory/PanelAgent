# Frontend Theme Redesign Execution Plan

## TL;DR
> **Summary**: Re-theme the frontend to a publication-grade light-first scientific interface (Paper Platform + slight Editorial Science), while preserving all existing behavior and data flows.
> **Deliverables**:
> - Tokenized light-first visual system and restrained semantic states
> - Updated shell + 3 pages + spectra chart visual language
> - Hardcoded-color hotspot elimination in target files
> - Build/QA evidence for desktop and mobile critical paths
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: T1 baseline evidence -> T2 global token system -> T5/T6/T7 page/chart retheme -> T8 final regression hardening

## Context

### Original Request
- User requested replacing the current theme because visual quality was unsatisfactory and asked for deep style exploration before execution.

### Interview Summary
- Visual brainstorming completed with browser companion.
- User selected academic publication feel, mostly light theme.
- Final approved direction: Paper Platform base with slight Editorial Science polish.

### Metis Review (gaps addressed)
- Close hotspot drift: explicitly eliminate all hardcoded color outliers in home/exp/panel/spectra files.
- Add guardrails against logic changes and scope creep.
- Add acceptance criteria for chart readability, badge semantics, and responsive shell behavior.
- Add edge-case checks for nav wrapping, dense badge overflow, and warning contrast on light surfaces.

## Work Objectives

### Core Objective
- Deliver a cohesive, publication-grade frontend visual system that is light-first, scientifically credible, and calmer than the current neon/dark-heavy presentation.

### Deliverables
- Updated theme tokens and utilities in `frontend/src/app/globals.css`.
- Updated shared shell styling in `frontend/src/app/layout.tsx`.
- Updated presentation in:
  - `frontend/src/app/page.tsx`
  - `frontend/src/app/exp-design/page.tsx`
  - `frontend/src/app/panel-design/page.tsx`
  - `frontend/src/components/spectra-chart.tsx`
- QA evidence for visual and behavioral parity.

### Definition of Done (verifiable conditions with commands)
- Frontend production build succeeds:
  - `cd /home/user/PanChongshi/Repo/PanelAgent/frontend && /home/user/miniforge3/envs/flowcyt/bin/node node_modules/next/dist/bin/next build`
- API-proxy critical flows still respond through frontend:
  - `curl -s -X POST http://localhost:3000/api/v1/panels/generate -H "Content-Type: application/json" -d '{"species":"Mouse","markers":["CD45","CD3e","CD8a"],"num_colors":3}' | python3 -m json.tool`
  - `curl -s -X POST http://localhost:3000/api/v1/recommendations/markers -H "Content-Type: application/json" -d '{"species":"Mouse","experimental_goal":"T cell exhaustion","num_colors":8}' | python3 -m json.tool`
- No new logic-affecting diffs in hooks/backend files outside theme target set.
- Evidence files exist for all task QA scenarios in `.sisyphus/evidence/`.

### Must Have
- Light-first publication-style hierarchy and calmer semantic colors.
- Consistent visual system across shell, pages, and chart.
- Retained existing interactions and response handling.
- Explicit treatment for hardcoded color hotspots.

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- No backend/API/hook behavior changes.
- No new product features or workflow redesign.
- No indiscriminate neon accents, rainbow status overuse, or heavy glow styling.
- No arbitrary one-off inline colors added outside approved token strategy.

## Verification Strategy
> ZERO HUMAN INTERVENTION — all verification is agent-executed.
- Test decision: tests-after + existing Next.js build and API smoke checks.
- QA policy: Every task includes happy and failure/edge scenario with evidence output.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy

### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.

Wave 1 (foundation): T1, T2, T3, T4
- T1 baseline evidence and hotspot inventory lock
- T2 global token + utility normalization
- T3 shell retheme (layout chrome)
- T4 home page publication-style retheme

Wave 2 (feature surfaces): T5, T6, T7, T8
- T5 exp-design visual normalization
- T6 panel-design visual normalization
- T7 spectra chart publication-figure retheme
- T8 cross-page responsive/accessibility hardening + regression closure

### Dependency Matrix (full, all tasks)
- T1: Blocks T2-T8
- T2: Blocks T3-T8
- T3: Blocked by T2; can run in parallel with T4
- T4: Blocked by T2; can run in parallel with T3
- T5: Blocked by T2
- T6: Blocked by T2
- T7: Blocked by T2
- T8: Blocked by T3, T4, T5, T6, T7

### Agent Dispatch Summary (wave -> task count -> categories)
- Wave 1 -> 4 tasks -> visual-engineering (3), unspecified-low (1 QA setup)
- Wave 2 -> 4 tasks -> visual-engineering (4)

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. Baseline Evidence + Hotspot Lock

  **What to do**: Capture baseline screenshots and behavior checks for `/`, `/exp-design`, `/panel-design`; produce a hardcoded-color hotspot inventory limited to target files and save evidence artifacts.
  **Must NOT do**: Do not modify application code in this task.

  **Recommended Agent Profile**:
  - Category: `unspecified-low` — Reason: inventory and evidence capture only.
  - Skills: [`playwright`] — browser evidence capture.
  - Omitted: [`frontend-design`] — no redesign work yet.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T2-T8 | Blocked By: none

  **References** (executor has NO interview context — be exhaustive):
  - Pattern: `frontend/src/app/page.tsx:15` — decorative gradient/orb region currently color-heavy.
  - Pattern: `frontend/src/app/exp-design/page.tsx:40` — marker type badge color mapping hotspot.
  - Pattern: `frontend/src/app/panel-design/page.tsx:41` — brightness and warning styling hotspot.
  - Pattern: `frontend/src/components/spectra-chart.tsx:141` — warning + tooltip/grid hardcoded color hotspot.
  - API/Type: `frontend/src/lib/hooks/use-panel-generation.ts` — generation flow must remain unchanged.
  - API/Type: `frontend/src/lib/hooks/use-marker-recommendation.ts` — recommendation flow must remain unchanged.

  **Acceptance Criteria** (agent-executable only):
  - [ ] Baseline screenshots saved for three pages and at least one spectra-render state.
  - [ ] Hotspot inventory saved listing all hardcoded color classes/inline values in target files.
  - [ ] No source files outside evidence/inventory artifacts changed.

  **QA Scenarios** (MANDATORY — task incomplete without these):
  ```
  Scenario: Baseline route capture
    Tool: Playwright
    Steps: Open /, /exp-design, /panel-design at 1280x800; wait network idle; capture full-page screenshots.
    Expected: 3 screenshots exist with visible header, main content, and footer.
    Evidence: .sisyphus/evidence/task-1-baseline-pages.png

  Scenario: Baseline API-backed visual state
    Tool: Bash + Playwright
    Steps: Trigger panel generation via API, open /panel-design, verify candidate table and spectra section render, capture screenshot.
    Expected: Candidate tabs and spectra card are visible with non-empty content.
    Evidence: .sisyphus/evidence/task-1-baseline-spectra.png
  ```

  **Commit**: YES | Message: `test(theme): lock baseline screenshots and color hotspots` | Files: `.sisyphus/evidence/*`, `.sisyphus/notepads/*`

- [x] 2. Global Token System Rebuild (Light-First)

  **What to do**: Rebuild visual tokens and utilities in `globals.css` for paper-platform light-first design; reduce neon/glow intensity; define consistent semantic warning/type/brightness tokens.
  **Must NOT do**: Do not change app logic, routes, or API behavior.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` — Reason: design-token heavy CSS work.
  - Skills: [`frontend-design`] — coherent palette + hierarchy system.
  - Omitted: [`nextjs-app-router-fundamentals`] — not routing-related.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: T3-T8 | Blocked By: T1

  **References**:
  - Pattern: `frontend/src/app/globals.css:51` — existing root/dark token blocks.
  - Pattern: `frontend/src/app/globals.css:175` — utility classes (`glow-primary`, `glass`, `glass-border`).
  - Pattern: `docs/superpowers/specs/2026-03-30-frontend-theme-redesign-design.md:51` — approved color system constraints.

  **Acceptance Criteria**:
  - [ ] Light-first token set implemented with restrained academic palette.
  - [ ] Dark fallback remains readable but not primary visual identity.
  - [ ] Semantic token families exist for warning/type/brightness and are reusable.
  - [ ] No arbitrary one-off palette values introduced in non-token files by this task.

  **QA Scenarios**:
  ```
  Scenario: Token application smoke
    Tool: Playwright
    Steps: Open / and inspect hero, card, and button colors against tokenized CSS vars via computed styles.
    Expected: Primary action color and neutral surfaces align with new token values.
    Evidence: .sisyphus/evidence/task-2-token-smoke.png

  Scenario: Contrast edge check
    Tool: Playwright
    Steps: Capture text-heavy regions (exp-design table + panel-design rationale block); run accessibility snapshot for contrast warnings.
    Expected: No severe contrast failures in primary text and interactive controls.
    Evidence: .sisyphus/evidence/task-2-contrast-check.json
  ```

  **Commit**: YES | Message: `feat(theme): rebuild light-first publication token system` | Files: `frontend/src/app/globals.css`

- [x] 3. Shared Shell Retheme (Layout Chrome)

  **What to do**: Retheme header/footer and shared shell spacing to publication-grade style while keeping nav structure and links intact.
  **Must NOT do**: Do not add new navigation features or alter route structure.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` — Reason: shell-level visual hierarchy and responsive polish.
  - Skills: [`frontend-design`, `nextjs-app-router-fundamentals`] — visual plus App Router layout constraints.
  - Omitted: [`shadcn`] — no new component generation needed.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T8 | Blocked By: T2

  **References**:
  - Pattern: `frontend/src/app/layout.tsx:32` — current sticky header/nav styling.
  - Pattern: `frontend/src/app/layout.tsx:81` — footer typography and spacing.
  - Pattern: `docs/superpowers/specs/2026-03-30-frontend-theme-redesign-design.md:173` — hierarchy targets.

  **Acceptance Criteria**:
  - [ ] Header/footer visually align with paper-platform theme.
  - [ ] Nav remains functional and readable at desktop/mobile breakpoints.
  - [ ] No link destination or layout children behavior changed.

  **QA Scenarios**:
  ```
  Scenario: Responsive nav integrity
    Tool: Playwright
    Steps: Open / at widths 1280, 768, 390; verify nav items Home/Experimental Design/Panel Generation visible and clickable.
    Expected: No overlap/cutoff; each link navigates correctly.
    Evidence: .sisyphus/evidence/task-3-nav-responsive.png

  Scenario: Shell contrast/readability
    Tool: Playwright
    Steps: Capture header and footer regions with typography zoom at 125%.
    Expected: Brand text and nav labels remain legible with clear visual hierarchy.
    Evidence: .sisyphus/evidence/task-3-shell-readability.png
  ```

  **Commit**: YES | Message: `refactor(layout): retheme shell for publication-grade hierarchy` | Files: `frontend/src/app/layout.tsx`

- [x] 4. Homepage Visual Language Conversion

  **What to do**: Convert homepage from decorative neon style to publication-platform module layout; remove color-noisy decorative orbs; keep existing sections and CTA behavior.
  **Must NOT do**: Do not change routing targets or CTA semantics.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` — Reason: page composition and hierarchy redesign.
  - Skills: [`frontend-design`] — visual rhythm, typography, and restrained accents.
  - Omitted: [`playwright`] — this task produces UI changes, QA is still required but implementation-first.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: T8 | Blocked By: T2

  **References**:
  - Pattern: `frontend/src/app/page.tsx:15` — current gradient/decorative background area.
  - Pattern: `frontend/src/app/page.tsx:40` — feature card and CTA section.
  - Pattern: `frontend/src/app/page.tsx:100` — workflow section hierarchy.
  - External: `docs/superpowers/specs/2026-03-30-frontend-theme-redesign-design.md:99` — homepage direction.

  **Acceptance Criteria**:
  - [ ] Decorative color-noise reduced or removed.
  - [ ] Hero, feature cards, and workflow section retain existing content and links.
  - [ ] Visual hierarchy is clearly publication-oriented (typography + spacing-led).

  **QA Scenarios**:
  ```
  Scenario: Homepage structure parity
    Tool: Playwright
    Steps: Open /; verify presence of heading "FlowCyt Panel Assistant", two CTA cards, and "How It Works" section.
    Expected: All sections render with updated styling and unchanged links.
    Evidence: .sisyphus/evidence/task-4-home-parity.png

  Scenario: CTA behavior check
    Tool: Playwright
    Steps: Click "Start Experimental Design" and "Generate Panel" from homepage cards.
    Expected: Navigation lands on /exp-design and /panel-design respectively.
    Evidence: .sisyphus/evidence/task-4-home-cta.png
  ```

  **Commit**: YES | Message: `refactor(home): convert landing visuals to paper-platform style` | Files: `frontend/src/app/page.tsx`

- [x] 5. Experimental Design Page Retheme + Type Badge normalization

  **What to do**: Normalize exp-design visuals to publication style and replace hardcoded type badge colors with semantic token-aligned mapping.
  **Must NOT do**: Do not alter recommendation request payloads or state transitions.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` — Reason: dense form + results table styling.
  - Skills: [`frontend-design`, `shadcn`] — preserve existing UI component usage while restyling.
  - Omitted: [`nextjs-app-router-fundamentals`] — page route behavior unchanged.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T8 | Blocked By: T2

  **References**:
  - Pattern: `frontend/src/app/exp-design/page.tsx:40` — `getTypeBadgeColor` mapping hotspot.
  - Pattern: `frontend/src/app/exp-design/page.tsx:103` — primary form card styling.
  - Pattern: `frontend/src/app/exp-design/page.tsx:257` — marker detail table row rendering.
  - API/Type: `frontend/src/lib/hooks/use-marker-recommendation.ts` — behavior must remain untouched.

  **Acceptance Criteria**:
  - [ ] Type badges remain semantically distinguishable with subdued palette.
  - [ ] Form and results areas match publication-grade spacing/readability.
  - [ ] Existing button actions (`Recommend`, `Clear`, `Use This Panel`) remain unchanged.

  **QA Scenarios**:
  ```
  Scenario: Recommendation happy path styling + behavior
    Tool: Playwright
    Steps: Open /exp-design; input goal text; set colors to 8; click Recommend Markers; wait for table rows.
    Expected: Results table renders with readable badge colors and action buttons still work.
    Evidence: .sisyphus/evidence/task-5-exp-happy.png

  Scenario: Empty/error state readability
    Tool: Playwright
    Steps: Trigger empty state via Clear; then simulate recommendation failure by intercepting API 500.
    Expected: Empty and error blocks remain calm/readable and not overly saturated.
    Evidence: .sisyphus/evidence/task-5-exp-states.png
  ```

  **Commit**: YES | Message: `refactor(exp-design): normalize type badges and publication styling` | Files: `frontend/src/app/exp-design/page.tsx`

- [x] 6. Panel Design Page Retheme + Warning/Brightness Normalization

  **What to do**: Restyle panel-design workbench to publication-grade hierarchy and replace hardcoded warning/brightness color blocks with semantic subdued equivalents.
  **Must NOT do**: Do not change generation/evaluation logic, tab semantics, or diagnosis content.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` — Reason: highest-density page requiring careful hierarchy.
  - Skills: [`frontend-design`, `shadcn`] — compose existing UI primitives with cohesive style.
  - Omitted: [`playwright`] — execution task, QA handled in scenarios.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T8 | Blocked By: T2

  **References**:
  - Pattern: `frontend/src/app/panel-design/page.tsx:41` — `getBrightnessColor` hotspot.
  - Pattern: `frontend/src/app/panel-design/page.tsx:54` — candidate table row styling.
  - Pattern: `frontend/src/app/panel-design/page.tsx:242` — warning/missing marker card tone.
  - Pattern: `frontend/src/app/panel-design/page.tsx:339` — gating strategy list presentation.
  - API/Type: `frontend/src/lib/hooks/use-panel-generation.ts` and `frontend/src/lib/hooks/use-panel-evaluation.ts` — preserve behavior.

  **Acceptance Criteria**:
  - [ ] Brightness encoding remains visually distinct while less saturated.
  - [ ] Warning and diagnosis surfaces are readable and consistent with light-first system.
  - [ ] Candidate tabs, evaluation flow, and diagnosis block behaviors are unchanged.

  **QA Scenarios**:
  ```
  Scenario: Panel generation + evaluation visual parity
    Tool: Playwright
    Steps: Open /panel-design; enter markers "CD45,CD3e,CD8a"; click Search Panels; then click Evaluate with AI.
    Expected: Candidate table, recommended panel, rationale, and gating strategy appear with updated styling.
    Evidence: .sisyphus/evidence/task-6-panel-happy.png

  Scenario: Missing marker warning edge case
    Tool: Playwright
    Steps: Search markers including nonexistent one (e.g., "CD45,NON_EXISTENT_MARKER").
    Expected: Missing marker warning appears with subdued readable warning colors and no layout break.
    Evidence: .sisyphus/evidence/task-6-panel-warning.png
  ```

  **Commit**: YES | Message: `refactor(panel-design): retheme workbench and normalize warning states` | Files: `frontend/src/app/panel-design/page.tsx`

- [x] 7. Spectra Chart Publication-Figure Retheme

  **What to do**: Re-theme chart warning surfaces, grid/axis/tooltip/legend visuals for publication readability on light-first surfaces without changing chart data logic.
  **Must NOT do**: Do not change request/response handling or series transformation semantics.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` — Reason: chart readability and scientific figure polish.
  - Skills: [`frontend-design`] — visual balance for chart-heavy UI.
  - Omitted: [`shadcn`] — chart is Recharts-driven, not component registry work.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: T8 | Blocked By: T2

  **References**:
  - Pattern: `frontend/src/components/spectra-chart.tsx:141` — warning block hardcoded colors.
  - Pattern: `frontend/src/components/spectra-chart.tsx:158` — grid/tick/label color usage.
  - Pattern: `frontend/src/components/spectra-chart.tsx:187` — tooltip and legend styling.
  - API/Type: `frontend/src/components/spectra-chart.tsx:53` — API call semantics must remain intact.

  **Acceptance Criteria**:
  - [ ] Chart remains legible on light-first palette with clear axes and line distinction.
  - [ ] Warning badges/surfaces align with subdued semantic warning color.
  - [ ] Tooltip/legend remain readable and non-intrusive.

  **QA Scenarios**:
  ```
  Scenario: Spectra render readability
    Tool: Playwright
    Steps: Open /panel-design with generated candidates; switch tabs to update spectra; inspect chart axis/legend/tooltip.
    Expected: Plot lines remain distinguishable; axis labels and tooltip text readable.
    Evidence: .sisyphus/evidence/task-7-spectra-happy.png

  Scenario: Unknown fluorochrome warning styling
    Tool: Bash + Playwright
    Steps: Mock spectra API response with warnings array; open chart view.
    Expected: Warning block appears with subdued warning palette and clear text contrast.
    Evidence: .sisyphus/evidence/task-7-spectra-warning.png
  ```

  **Commit**: YES | Message: `refactor(spectra): apply publication-figure visual treatment` | Files: `frontend/src/components/spectra-chart.tsx`

- [x] 8. Cross-Page Regression Hardening (Responsive + Accessibility + Hotspot Closure)

  **What to do**: Execute final pass to close all remaining hardcoded-color hotspots in target files, verify responsive layout and readability, and produce final evidence bundle.
  **Must NOT do**: Do not introduce new design directions or scope expansion; no backend/hook changes.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: cross-cutting verification and final closure.
  - Skills: [`playwright`] — multi-viewport evidence capture.
  - Omitted: [`frontend-design`] — this is hardening/verification, not new concept work.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: Final Verification Wave | Blocked By: T3, T4, T5, T6, T7

  **References**:
  - Pattern: `frontend/src/app/page.tsx:17` — home decorative hardcoded HSL hotspot to eliminate or normalize.
  - Pattern: `frontend/src/app/exp-design/page.tsx:40` — badge color mapping closure.
  - Pattern: `frontend/src/app/panel-design/page.tsx:41` — brightness + warning closure.
  - Pattern: `frontend/src/components/spectra-chart.tsx:141` — warning/tooltip/grid closure.

  **Acceptance Criteria**:
  - [ ] Grep hotspot query returns no unapproved hardcoded color usages in target files.
  - [ ] Approved exceptions are explicitly documented: token definitions in `frontend/src/app/globals.css` and runtime `series.color` values from spectra API lines.
  - [ ] Desktop/mobile screenshots captured for `/`, `/exp-design`, `/panel-design`.
  - [ ] Frontend build passes and API smoke checks pass via frontend proxy.
  - [ ] All evidence artifacts assembled in `.sisyphus/evidence/`.

  **QA Scenarios**:
  ```
  Scenario: Multi-viewport regression sweep
    Tool: Playwright
    Steps: Capture /, /exp-design, /panel-design at 1280x800 and 390x844.
    Expected: No clipping/overlap; typography and controls remain readable.
    Evidence: .sisyphus/evidence/task-8-responsive-sweep.png

  Scenario: Hardcoded-color closure
    Tool: Grep
    Steps: Run color hotspot grep on frontend/src for red/yellow/emerald/blue/purple/orange/pink/cyan/sky/amber classes and inline oklch/hsl values.
    Expected: Only approved token definitions in globals.css and spectra runtime series colors remain.
    Evidence: .sisyphus/evidence/task-8-hotspot-closure.txt
  ```

  **Commit**: YES | Message: `test(theme): close hotspot regressions and finalize visual QA` | Files: `.sisyphus/evidence/*`, affected target files as needed


## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [x] F1. Plan Compliance Audit — oracle (APPROVED with minor notes)
- [x] F2. Code Quality Review — unspecified-high (APPROVED)
- [x] F3. Real Manual QA — unspecified-high (+ playwright if UI) (APPROVED)
- [x] F4. Scope Fidelity Check — deep (APPROVED)

## Commit Strategy
- Use one commit per task unless two small adjacent tasks are tightly coupled and review-safe.
- Commit message pattern: `type(scope): description`.
- Expected commit scopes: `theme`, `layout`, `home`, `exp-design`, `panel-design`, `spectra`, `qa`.

## Success Criteria
- Visual system is coherent, light-first, publication-grade.
- No behavior regression in panel generation/recommendation entry points.
- All target files updated consistently with token strategy.
- Final verification wave approved and user explicitly confirms completion.
