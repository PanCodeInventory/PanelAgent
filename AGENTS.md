# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-19
**Commit:** 1e5a5c3
**Branch:** main

## OVERVIEW

FlowCyt Panel Assistant — hybrid AI tool for multi-color flow cytometry panel design. Combines deterministic backtracking solver (Python) with LLM expert evaluation (OpenAI-compatible API) to generate physically valid panels grounded in the user's real antibody inventory.

## STRUCTURE

```
FlowCyt-Assitant/
├── streamlit_app.py          # UI entry point (2 tabs: Exp Design, Panel Gen)
├── panel_generator.py        # Core logic: backtracking solver + LLM evaluation
├── data_preprocessing.py     # CSV loading, marker normalization, alias index
├── spectral_viewer.py        # Gaussian spectral simulation (Plotly)
├── llm_api_client.py         # OpenAI-compatible API wrapper (LM Studio / cloud)
├── channel_mapping.json      # Fluorochrome → detector channel mapping
├── fluorochrome_brightness.json  # Brightness scale 1-5 per fluorochrome
├── spectral_data.json        # Peak/Sigma/Color per fluorochrome
├── Dockerfile                # python:3.9-slim-buster, port 8501
├── requirements.txt          # 7 deps: streamlit, pandas, openai, python-dotenv, plotly, scipy, numpy
├── AGENT.md                  # Gemini-focused agent guidance (legacy)
├── guidedoc.md               # Chinese design doc with architecture decisions
├── inventory/                # User-provided CSV antibody inventory (not in repo)
├── icons/                    # Static SVG assets
└── .github/workflows/        # Gemini CLI workflows (AI-assisted review/triage, NOT build/test CI)
```

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `streamlit_app.py` | module | root | UI entry point. Run via `streamlit run`. 2 tabs. |
| `generate_candidate_panels()` | function | panel_generator.py:102 | Main orchestrator: normalize markers → aggregate → solve → return candidates |
| `find_valid_panels()` | function | panel_generator.py:8 | DFS backtracking solver. Constraint: no duplicate System_Code per panel. |
| `diagnose_conflicts()` | function | panel_generator.py:52 | Pigeonhole principle analysis when no valid panel exists |
| `evaluate_candidates_with_llm()` | function | panel_generator.py:165 | Diff analysis across candidates → prompt LLM → parse JSON response |
| `recommend_markers_from_inventory()` | function | panel_generator.py:308 | Tab 1: LLM selects markers from inventory based on research goal |
| `load_antibody_data()` | function | data_preprocessing.py:49 | CSV loader with encoding detection (utf-8/gbk/gb18030/latin1) and column mapping |
| `normalize_marker_name()` | function | data_preprocessing.py:5 | Strips parentheticals, lowercases, removes spaces/dashes, strips a/b suffixes |
| `parse_target_aliases()` | function | data_preprocessing.py:24 | Extracts alias list from "CD274 (B7-H1, PD-L1)" format |
| `aggregate_antibodies_by_marker()` | function | data_preprocessing.py:133 | Builds inverted index: alias → [antibody_info_list] |
| `plot_panel_spectra()` | function | spectral_viewer.py:25 | Plotly figure of Gaussian emission spectra for all fluorochromes in a panel |
| `consult_gpt_oss()` | function | llm_api_client.py:14 | Single function: sends prompt, returns raw LLM response string |

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add/change fluorochrome-channel mapping | `channel_mapping.json` | Keys are commercial dye names, values are detector IDs |
| Add/change fluorochrome brightness | `fluorochrome_brightness.json` | Scale 1 (dim) to 5 (very bright) |
| Add/change spectral simulation data | `spectral_data.json` | Peak (nm), Sigma, Color (hex) |
| Change inventory file path | `streamlit_app.py:15-18` | `INVENTORY_CONFIG` dict maps species → CSV path |
| Change CSV column names | `streamlit_app.py:26-33` | `CUSTOM_COLUMN_MAPPING` maps user cols → standard names |
| Change LLM endpoint/model | `.env` or `llm_api_client.py:10-12` | Env vars: `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_MODEL_NAME` |
| Modify backtracking solver logic | `panel_generator.py:8-50` | DFS with scarcity-first ordering and random shuffle |
| Modify LLM evaluation prompt | `panel_generator.py:209-253` | JSON output prompt with brightness/spillover criteria |
| Modify marker recommendation prompt | `panel_generator.py:319-342` | Tab 1 experimental design prompt |

## CONVENTIONS

- **Flat module structure**: No packages, no `__init__.py`. Direct imports between 5 `.py` files.
- **Bilingual comments**: Code comments mix English and Chinese. Docstrings are English.
- **LLM JSON parsing**: Triple fallback chain — `json.loads` → `ast.literal_eval` → default to Option 1.
- **Session state**: Streamlit `st.session_state` manages all UI state (candidates, LLM results, species selection).
- **Data flow**: `streamlit_app.py` → `panel_generator.py` → `data_preprocessing.py` → `llm_api_client.py`. No circular imports.
- **Standard CSV columns expected**: `Target`, `Fluorescein`. Optional: `Clone`, `Brand`, `Catalog Number`.

## ANTI-PATTERNS (THIS PROJECT)

- **NEVER** allow duplicate `System_Code` in a single panel — this is a hard physics constraint (one fluorochrome per detector).
- **NEVER** use Markdown code blocks in LLM JSON responses — the parser expects raw JSON with double quotes. Prompts explicitly forbid ````json` wrappers.
- **NEVER** send full inventory to LLM unfiltered — filter by user-requested markers first (context window limit).
- **DO NOT** select antibodies with Quantity < 2 when possible (avoid dead stock).
- **DO NOT** critique common assignments across candidates in LLM evaluation — they are fixed by inventory constraints.
- **DO NOT** hardcode inventory paths outside `INVENTORY_CONFIG` — all paths should go through the config dict.

## UNIQUE STYLES

- **Search-then-Evaluate architecture**: Deterministic solver guarantees physical validity; LLM only ranks pre-validated candidates. LLM never generates panels directly.
- **Scarcity-first backtracking**: Markers with fewest antibody options are assigned first (fail-fast optimization).
- **Conflict diagnosis via Pigeonhole Principle**: When no solution exists, identifies which marker groups are mathematically impossible to satisfy.
- **Diff-focused LLM evaluation**: Instead of sending full panels, only highlights marker assignments that differ between candidates to reduce prompt size.
- **Inverted alias index**: `parse_target_aliases` + `aggregate_antibodies_by_marker` builds a many-to-many mapping so searching "PD-L1" finds antibodies labeled "CD274 (B7-H1, PD-L1)".

## COMMANDS

```bash
# Run locally
streamlit run streamlit_app.py

# Install dependencies
pip install -r requirements.txt

# Docker build and run
docker build -t flowcyt . && docker run -p 8501:8501 flowcyt

# Test data preprocessing standalone
python data_preprocessing.py
```

**No test suite exists.** No pytest, no linting, no type checking configured.

## NOTES

- **inventory/ folder is user-managed** — not in repo. Users place CSV files (e.g., `Mouse_20250625_ZhengLab.csv`) there.
- **LLM required for AI features** — Tab 1 (marker recommendation) and "Evaluate with AI" button need a running LLM endpoint. Default: local LM Studio at `http://127.0.0.1:1234/v1`.
- **Spectral simulation is Gaussian approximation** — not real spectral overlap data. Useful for visual assessment only.
- **Existing AGENT.md is Gemini-focused** — contains detailed architecture docs but formatted for Gemini CLI. This AGENTS.md is the canonical reference.
- **guidedoc.md** — Chinese design document with roadmap and technical challenges. Historical reference.
