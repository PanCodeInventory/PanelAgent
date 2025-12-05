import json
import re
import random
from data_preprocessing import load_antibody_data, normalize_marker_name, aggregate_antibodies_by_marker
from llm_api_client import consult_gpt_oss

def find_valid_panels(markers, antibodies_by_marker, max_solutions=3):
    """
    Uses backtracking to find up to 'max_solutions' valid panels (no system_code conflicts).
    Returns a list of panels, where each panel is a dictionary {marker: antibody_info}.
    """
    solutions = []
    
    # Sort markers by number of available antibodies (least options first) to fail fast
    sorted_markers = sorted(markers, key=lambda m: len(antibodies_by_marker.get(m, [])))
    
    def backtrack(index, current_panel, used_system_codes):
        if len(solutions) >= max_solutions:
            return

        if index == len(sorted_markers):
            solutions.append(current_panel.copy())
            return

        marker = sorted_markers[index]
        options = antibodies_by_marker.get(marker, [])
        
        # Shuffle options to get random variety in solutions
        options_shuffled = options.copy()
        random.shuffle(options_shuffled)

        for ab in options_shuffled:
            code = ab.get('system_code')
            if code and code != 'UNKNOWN' and code not in used_system_codes:
                # Choose this antibody
                current_panel[marker] = ab
                used_system_codes.add(code)
                
                # Recurse
                backtrack(index + 1, current_panel, used_system_codes)
                
                # Backtrack (undo choice)
                if len(solutions) >= max_solutions:
                    return
                del current_panel[marker]
                used_system_codes.remove(code)

    backtrack(0, {}, set())
    return solutions

def diagnose_conflicts(markers, antibodies_by_marker):
    """
    Analyzes the markers to find potential conflict sources.
    Returns a readable string explaining the conflict.
    """
    diagnosis = []
    
    # 1. Collect available codes for each marker
    marker_codes = {}
    for m in markers:
        options = antibodies_by_marker.get(m, [])
        codes = sorted(list(set(ab['system_code'] for ab in options if ab.get('system_code') != 'UNKNOWN')))
        marker_codes[m] = codes

    # 2. Check for markers with NO available antibodies
    dead_markers = [m for m, codes in marker_codes.items() if not codes]
    if dead_markers:
        return f"以下 Marker 没有可用的有效抗体 (No valid antibodies): {', '.join(dead_markers)}。请检查库存或拼写。"

    # 3. Check for "Tight Constraints" (Pigeonhole Principle)
    # Group markers by their available channel sets
    # e.g. Key: ('APC', 'PE') -> Value: ['CD4', 'CD8', 'FoxP3']
    # If len(Value) > len(Key), it's mathematically impossible.
    
    from collections import defaultdict
    constraint_groups = defaultdict(list)
    
    for m, codes in marker_codes.items():
        # Only consider markers that are somewhat restricted (e.g. < 5 options) to avoid noise
        # (Actually, let's check all, but the conflict is only proven if count > slots)
        codes_tuple = tuple(codes)
        constraint_groups[codes_tuple].append(m)
        
    conflict_found = False
    for codes, group_markers in constraint_groups.items():
        slots = len(codes)
        claimants = len(group_markers)
        
        if claimants > slots:
            conflict_found = True
            code_str = ", ".join(codes) if codes else "None"
            marker_str = ", ".join(group_markers)
            diagnosis.append(f"❌ **冲突组 (Conflict Group)**:\n   - Markers: **{marker_str}** ({claimants} 个)\n   - 只能争夺以下 {slots} 个通道: **[{code_str}]**\n   - 坑位不足，必然冲突。建议移除其中 {claimants - slots} 个 Marker。")

    if not conflict_found:
        # Fallback: General density check
        diagnosis.append("虽然没有发现明显的'硬性'死锁，但在回溯搜索中未能找到解。这通常是因为多个 Marker 互相抢占了热门通道 (如 PE, APC, PE-Cy7)。建议减少 Marker 数量或增加抗体库存。")

    return "\n\n".join(diagnosis)

def generate_candidate_panels(user_markers, antibody_df, max_solutions=10):
    """
    Step 1: Pure Python Generation (The "Manual Mode").
    Generates valid panels but does NOT call LLM.
    
    Args:
        user_markers: List of target markers.
        antibody_df: Pre-loaded and processed pandas DataFrame.
        max_solutions: Max number of candidates to find.
    """
    print(f"--- Generating Candidate Panels for: {user_markers} ---")

    # 1. Validation
    if antibody_df is None or antibody_df.empty:
        return {"status": "error", "message": "Antibody data is empty or invalid."}
    
    try:
        with open('fluorochrome_brightness.json', 'r') as f:
            brightness_data = json.load(f)
    except FileNotFoundError:
        brightness_data = {} 

    # 2. Aggregate and Prepare Data
    antibodies_by_norm_marker, _ = aggregate_antibodies_by_marker(antibody_df, brightness_data)

    available_antibodies_subset = {}
    markers_missing = []
    markers_found = []

    for user_marker in user_markers:
        norm_marker = normalize_marker_name(user_marker)
        if norm_marker in antibodies_by_norm_marker:
            available_antibodies_subset[user_marker] = antibodies_by_norm_marker[norm_marker]
            markers_found.append(user_marker)
        else:
            markers_missing.append(user_marker)

    if not markers_found:
        return {
            "status": "error", 
            "message": f"None of the requested markers were found. Missing: {markers_missing}"
        }

    # 3. Python Solver
    print(f"Generating up to {max_solutions} candidates...")
    candidates = find_valid_panels(markers_found, available_antibodies_subset, max_solutions=max_solutions)
    
    if not candidates:
        # --- NEW: Run Diagnosis ---
        diagnosis = diagnose_conflicts(markers_found, available_antibodies_subset)
        return {
            "status": "error",
            "message": f"无法找到无冲突的 Panel 组合。\n\n{diagnosis}"
        }

    print(f"Found {len(candidates)} valid candidates.")
    
    return {
        "status": "success",
        "candidates": candidates,
        "missing_markers": markers_missing
    }

def evaluate_candidates_with_llm(candidates, missing_markers=[]):
    """
    Step 2: AI Expert Evaluation (The "Auto Mode").
    Takes a list of candidates (usually top 3) and asks LLM to pick the best.
    """
    print(f"--- Asking LLM to evaluate {len(candidates)} candidates ---")
    
    if not candidates:
        return {"status": "error", "message": "No candidates to evaluate."}

    # --- 1. Diff Analysis ---
    # We assume all candidates have the same set of markers (keys).
    # We want to find which markers have different assignments across candidates.
    first_panel = candidates[0]
    markers = list(first_panel.keys())
    
    common_assignments = {}
    diff_markers = []

    for m in markers:
        # Check if this marker has the exact same antibody (same system_code/fluor) in all candidates
        # We use system_code + fluorochrome as identity signature
        signatures = set()
        for cand in candidates:
            ab = cand.get(m, {})
            sig = f"{ab.get('fluorochrome', '?')} ({ab.get('system_code', '?')})"
            signatures.add(sig)
        
        if len(signatures) == 1:
            # It's common across all
            common_assignments[m] = list(signatures)[0]
        else:
            diff_markers.append(m)

    # --- 2. Construct Prompt ---
    common_str = ", ".join([f"{m}: {fluor}" for m, fluor in common_assignments.items()])
    
    diff_str = ""
    for i, cand in enumerate(candidates):
        diff_str += f"\n**OPTION {i+1} Differences:**\n"
        for m in diff_markers:
            ab = cand.get(m, {})
            diff_str += f"- {m}: {ab.get('fluorochrome', '?')} (Brightness: {ab.get('brightness', '?')})\n"

    prompt = f"""
You are a flow cytometry panel design expert.

**Goal:** Compare {len(candidates)} candidate panels and select the BEST one.

**Context:**
- **Common Assignments (Identical in all options):** 
  {common_assignments if common_assignments else "None"}
  *(These are fixed due to inventory constraints. Do not critique them unless fatal.)*

- **KEY DIFFERENCES (Focus your decision here):**
{diff_str}

**Evaluation Criteria:**
1. **Brightness Matching:** High expression markers -> Dim fluorochromes. Low expression -> Bright fluorochromes.
2. **Spillover:** Minimize spectral overlap in critical co-expressed markers.

**Task:**
1. **Select** the best option index.
2. **Rationale:** Focus ONLY on why the specific assignments in the chosen option are better than the others.
3. **Gating Strategy:** Provide a **structured hierarchical list** (e.g., "1. CD45+ -> 2. CD3+ ...").

**Output Format (JSON):**
{{
  "selected_option_index": 1, 
  "rationale": "Option X is better because...",
  "gating_detail": [
    {{ 
      "step": 1, 
      "parent": "All Events", 
      "axis": "FSC-A / SSC-A", 
      "gate": "Polygon around lymphocytes", 
      "population": "Lymphocytes" 
    }},
    {{
       "step": 2,
       "parent": "Lymphocytes",
       "axis": "CD3 / CD19",
       "gate": "CD3+",
       "population": "T Cells"
    }}
  ]
}}
"""

    llm_response = consult_gpt_oss(prompt)
    
    # Parse Response
    try:
        json_match = re.search(r"(\{[\s\S]*\})", llm_response)
        if not json_match:
            print("LLM format invalid. Defaulting to Option 1.")
            selected_idx = 0
            rationale = "LLM output invalid. Shown Option 1."
            gating_detail = []
        else:
            result_json = json.loads(json_match.group(1))
            idx = result_json.get("selected_option_index", 1) - 1
            if 0 <= idx < len(candidates):
                selected_idx = idx
            else:
                selected_idx = 0
            
            rationale = result_json.get("rationale", "No rationale provided.")
            gating_detail = result_json.get("gating_detail", [])
            
        selected_panel = candidates[selected_idx].copy()
        
        # Add missing marker notes
        for m in missing_markers:
            selected_panel[m] = {"Note": "Not found in library"}

        return {
            "status": "success",
            "selected_panel": selected_panel,
            "rationale": rationale,
            "gating_detail": gating_detail
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def recommend_markers_from_inventory(experimental_goal, num_colors, available_targets_list):
    """
    New Feature: AI Experimental Design.
    Asks LLM to select markers from the INVENTORY list based on a research goal.
    Returns structured data for table display.
    """
    print(f"--- Asking LLM to recommend {num_colors} markers for: {experimental_goal} ---")
    
    # Convert list to string for prompt
    targets_str = ", ".join(sorted(available_targets_list))
    
    prompt = f"""
You are a senior flow cytometry expert.

**User's Research Goal:** {experimental_goal}
**Target Panel Size:** {num_colors} colors (approximately)

**Constraint:** You can ONLY select markers from the following **Available Inventory**:
[{targets_str}]

**Task:**
1. Select the most critical markers from the inventory to achieve the research goal.
2. Categorize each marker (e.g., Lineage, Activation, Exhaustion, Functional).
3. Provide a brief reason for selecting it.

**Output Format:**
Return a SINGLE JSON object containing a list called "markers_detail":
{{
  "markers_detail": [
    {{ "marker": "MarkerName", "type": "Category", "reason": "Short explanation..." }},
    {{ "marker": "MarkerName", "type": "Category", "reason": "Short explanation..." }}
  ]
}}
Respond with ONLY the valid JSON.
"""

    llm_response = consult_gpt_oss(prompt)
    
    try:
        json_match = re.search(r"(\{[\s\S]*\})", llm_response)
        if not json_match:
            return {"status": "error", "message": "LLM returned invalid format."}
        
        result_json = json.loads(json_match.group(1))
        details = result_json.get("markers_detail", [])
        
        # Extract simple list of names for the input box
        selected_markers = [item["marker"] for item in details]
        
        return {
            "status": "success",
            "markers_detail": details,
            "selected_markers": selected_markers
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}