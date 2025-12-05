# GEMINI.md

## Project Overview

**FlowCyt Panel Assistant** is a hybrid AI tool designed to automate and optimize the design of multi-color flow cytometry panels. Unlike generic chatbots, it grounds its generation in the user's **actual local antibody inventory**, ensuring that every suggested panel is physically possible to construct.

The system solves the "Combinatorial Constraint Satisfaction Problem" of panel design using a two-step approach:
1.  **Constraint Solving (Python):** A backtracking algorithm finds valid combinations that satisfy hardware constraints (one fluorochrome per detector).
2.  **Expert Reasoning (LLM):** A Large Language Model evaluates valid candidates based on biological heuristics (antigen density vs. fluorochrome brightness) and experimental goals.

## Technical Architecture

### 1. Data Layer (`data_preprocessing.py`)
*   **Inventory Loading:** Parses CSV inventory files (`流式抗体库-*.csv`).
*   **Normalization:**
    *   **Markers:** Standardizes names (e.g., `CD96 (TACTILE)` -> `cd96`, `CD8a` -> `cd8`).
    *   **Aliases:** Builds an inverted index so searches for `PD-L1` can find antibodies labeled `CD274`.
    *   **Channels:** Maps commercial fluorochrome names (e.g., `Alexa Fluor 488`, `BB515`) to standardized hardware detectors (`FITC`) via `channel_mapping.json`.
*   **Aggregates:** Groups individual antibody products by their target marker.

### 2. Logic Layer (`panel_generator.py`)
*   **Backtracking Solver (`find_valid_panels`):**
    *   Implements a Depth-First Search (DFS) to assign antibodies to markers.
    *   Enforces the constraint: `No two markers can share the same System_Code`.
    *   Optimization: Sorts markers by scarcity (fewest available antibodies) first to fail fast.
*   **Conflict Diagnosis (`diagnose_conflicts`):**
    *   If no solution is found, analyzes the constraints using the Pigeonhole Principle.
    *   Returns human-readable explanations (e.g., "You have 4 markers fighting for the PE/APC channels, but only 2 slots available").
*   **LLM Evaluation (`evaluate_candidates_with_llm`):**
    *   Prepares a comparative prompt highlighting the *differences* between top candidates.
    *   Parses JSON responses to extract the "Best Option Index", "Rationale", and "Gating Strategy".

### 3. Presentation Layer (`streamlit_app.py`)
*   **Tab 1: Experimental Design:**
    *   Uses LLM (`recommend_markers_from_inventory`) to suggest markers based on a natural language research goal.
*   **Tab 2: Panel Generation:**
    *   Input: Comma-separated marker list.
    *   Output: Interactive tables of candidate panels.
    *   **Visualization:** Integrates `spectral_viewer.py` to display simulated emission spectra for every candidate panel, allowing visual spillover assessment.
    *   Action: "Evaluate with AI" button triggers the LLM analysis.

## Configuration Files

*   **`channel_mapping.json`**: Critical for the solver. Maps specific dyes to exclusive system channels.
    *   *Example:* `{"FITC": "FITC", "Alexa Fluor 488": "FITC", "BB515": "FITC"}`
*   **`fluorochrome_brightness.json`**: Used by the LLM to judge panel quality (Brightness Matching).
    *   *Scale:* 1 (Dim) to 5 (Very Bright).
*   **`spectral_data.json`**: A local database of fluorophore physical properties (Peak Emission, Sigma). Used by the spectral viewer to simulate Gaussian curves.

## LLM Integration (`llm_api_client.py`)

*   **Hybrid Configuration:** Supports both local LM Studio and Cloud LLM providers (OpenAI, DeepSeek, etc.).
*   **Configuration:** Reads from environment variables (`.env` file) or defaults to local settings.
    *   `OPENAI_API_BASE`: Custom API endpoint.
    *   `OPENAI_API_KEY`: API Key.
    *   `OPENAI_MODEL_NAME`: Model name to request.
*   **Robust Parsing:** Includes fallback logic (`json.loads` -> `ast.literal_eval`) and Markdown cleanup to handle variable LLM outputs.

## Development Status

*   **Current Focus:** Refinement of the UI and robustness of the solver.
*   **Known Limitations:** 
    *   Inventory file path is configured in code.
    *   Spectral simulation is based on Gaussian approximation.