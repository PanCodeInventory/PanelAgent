# Frontend Theme Redesign Design

- Date: 2026-03-30
- Project: FlowCyt Panel Assistant
- Scope: Frontend visual redesign only
- Status: Approved for planning

## Goal

Replace the current frontend visual language with a more credible, publication-grade scientific interface. The new design should feel closer to a high-quality academic platform than to a neon AI SaaS dashboard.

The redesign targets visual quality, hierarchy, and consistency only. Existing frontend and backend behavior must remain unchanged.

## Design Decision

Use a **Paper Platform** direction as the foundation, with a small amount of **Editorial Science** polish.

In practice, that means:

- the product is primarily light-themed
- the interface feels like a research platform or publication workspace
- typography and spacing do more of the design work than saturated color or glow
- charts and dense analysis modules can be slightly darker or more framed, but the product should not return to an all-dark identity

## Visual Intent

### Primary Mood

The UI should communicate:

- scientific credibility
- calm precision
- readability over spectacle
- analysis and interpretation over marketing energy

### What It Should Feel Like

- a paper-adjacent scientific platform
- a trustworthy analysis tool used repeatedly in research workflows
- an interface designed for reading tables, recommendations, gating logic, and spectra without fatigue

### What It Should Not Feel Like

- a glowing AI product landing page
- a generic dark SaaS dashboard
- a rainbow status-heavy admin panel
- a glassmorphism-heavy consumer UI

## Core Aesthetic System

### Color System

The palette should be restrained and hierarchical.

- **Base background:** warm paper white, not pure white
- **Surface background:** slightly lifted paper or neutral panel tone
- **Primary text:** deep ink gray
- **Secondary text:** cool gray with strong readability
- **Primary action color:** academic blue
- **Secondary accent:** restrained copper or muted editorial warmth
- **Status colors:** semantic and muted, never fluorescent

Color should be used in this order of importance:

1. structure and contrast
2. interaction states
3. semantic meaning
4. brand personality

The interface must avoid decorative color noise. If a color does not communicate structure, meaning, or interaction, it should be removed.

### Typography

Typography should move the interface toward publication quality.

- headings should feel like section titles in a scientific publication
- body text should stay highly readable in dense analytical contexts
- mono text should remain available for codes, markers, compact labels, and technical values
- title contrast should come from scale, weight, and spacing more than from bright color

### Surfaces and Containers

Cards should feel like modular paper panels, not floating product tiles.

- reduce overt glow, neon framing, and aggressive glass effects
- use lighter borders, subtle surface lifts, and controlled shadows
- emphasize layout rhythm and content grouping over component theatrics

### Motion

Motion should be minimal and scholarly.

- preserve responsiveness and hover clarity
- remove motion that exists only to look flashy
- keep transitions soft, short, and functional

## Page-Level Direction

### Home Page

The home page should look like a scientific platform overview, not a startup homepage.

It should:

- reduce decorative colored particles and neon accents
- use more editorial spacing and stronger section typography
- present capabilities as research modules
- make the search/evaluate/visualize workflow feel methodical and trustworthy

The homepage should answer: what this platform does, how it works, and why a researcher would trust it.

### Experimental Design Page

This page should resemble a structured research input and recommendation workspace.

It should:

- make the experiment description area feel like a deliberate authoring surface
- present recommendation results like an annotated table rather than a flashy app result block
- keep type/category badges semantic but subdued
- favor readability of rationale text over visual decoration

The result should feel closer to a manuscript preparation or analysis notebook step than a chatbot output panel.

### Panel Design Page

This is the densest screen and should become the clearest expression of the redesign.

It should:

- read as an analysis workbench
- clearly separate marker input, candidate panels, AI rationale, diagnosis, and spectra
- reduce visual clutter from competing highlight styles
- make candidate comparison easier than in the current design
- present the recommended panel with authority, but not with excessive saturation

### Spectra Chart

The spectra chart should move toward publication-figure aesthetics.

It should:

- use cleaner plot backgrounds
- soften axes, labels, and grids
- keep fluorochrome distinction clear without making the chart feel candy-colored
- feel like an interpretable scientific figure embedded inside a platform

## Component Rules

### Buttons

- default buttons use academic blue
- secondary buttons should recede visually but remain crisp
- shadows and glows should be reduced significantly

### Cards

- use restrained surfaces and lighter framing
- avoid looking like component-library defaults or glossy product boxes

### Badges

- keep semantic differentiation
- reduce saturation and visual noise
- use them to support scanning, not dominate the page

### Empty, Error, and Loading States

- make these states feel editorial and calm
- avoid loud warning blocks unless the issue is truly important
- loading placeholders should be clean and publication-like

## Information Hierarchy

The redesign should improve hierarchy in the following order:

1. page purpose
2. primary task area
3. important output/result
4. supporting explanation
5. secondary metadata

This hierarchy must be readable without relying on strong color fills.

## Accessibility and Readability

The redesign must preserve or improve:

- text contrast
- form control clarity
- scanability of tables and charts
- legibility on both desktop and mobile

Because this tool contains dense domain information, readability is more important than novelty.

## Scope

### In Scope

- global color and surface tokens
- global background/surface treatment
- header and footer polish if needed for consistency
- homepage visual redesign
- experimental design page visual redesign
- panel design page visual redesign
- spectra chart visual refinement
- status and badge normalization where needed for consistency

### Out of Scope

- backend logic changes
- API or hook behavior changes
- new product features
- workflow restructuring unrelated to visual clarity
- large-scale frontend architecture refactors

## Files Expected To Change

Primary implementation target:

- `frontend/src/app/globals.css`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/exp-design/page.tsx`
- `frontend/src/app/panel-design/page.tsx`
- `frontend/src/components/spectra-chart.tsx`

Other files should only change if required to support the approved visual system.

## Implementation Principles

- preserve all existing functionality
- preserve all current user flows
- change presentation first, not logic
- prefer consistency over isolated one-off flourishes
- remove visual noise before adding new styling
- ensure the final result looks intentionally designed as one system

## Verification Requirements

Before implementation is considered complete:

- frontend build must pass
- TypeScript checks must pass through the existing Next.js build pipeline
- major flows must still render correctly:
  - homepage
  - experimental design page
  - panel design page
  - spectra chart area
- no regressions to API integration or page navigation

## Recommended Planning Sequence

1. redefine global visual tokens and surface language
2. update shared chrome and global atmosphere
3. redesign homepage to establish the new voice
4. redesign exp-design and panel-design around the new hierarchy
5. refine spectra chart styling last so it aligns with the finalized palette

## Spec Review Notes

This spec has been checked for:

- no placeholders
- no contradictory theme direction
- clear scope boundaries
- explicit in-scope file targets
- no implementation work starting before approval and planning
