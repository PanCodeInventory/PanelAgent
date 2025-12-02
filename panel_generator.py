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

def generate_candidate_panels(user_markers, antibody_data_csv, channel_mapping_json, max_solutions=10):
    """
    Step 1: Pure Python Generation (The "Manual Mode").
    Generates valid panels but does NOT call LLM.
    """
    print(f"--- Generating Candidate Panels for: {user_markers} ---")

    # 1. Load Data
    antibody_df = load_antibody_data(antibody_data_csv, channel_mapping_json)
    if antibody_df is None:
        return {"status": "error", "message": "Could not load antibody data CSV."}
    
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
    
    # Format candidates for Prompt
    candidates_str = ""
    for i, cand in enumerate(candidates):
        candidates_str += f"\n--- OPTION {i+1} ---\n"
        candidates_str += json.dumps(cand, indent=2, ensure_ascii=False)

    prompt = f"""
You are an expert flow cytometry panel designer.

**Goal:** Evaluate the following {len(candidates)} valid antibody panels.
Select the BEST one based on **fluorochrome brightness matching** (bright fluorochromes for low-expression markers, dim for high).

**Candidate Panels:**
{candidates_str}

**Instructions:**
1.  **Analyze** each option carefully.
2.  **Select** the single best option (1-based index).
3.  **Explain** your choice (Design Rationale), highlighting specific marker-fluorochrome matches.
4.  **Provide** a comprehensive Gating Strategy.

**Output Format:**
Return a SINGLE JSON object: 
{{
  "selected_option_index": 1, 
  "rationale": "...",
  "gating_strategy": "..."
}}
Respond with ONLY the valid JSON.
"""

    llm_response = consult_gpt_oss(prompt)
    
    # Parse Response
    try:
        json_match = re.search(r"(\{[\s\S]*\})", llm_response)
        if not json_match:
            print("LLM format invalid. Defaulting to Option 1.")
            selected_idx = 0
            rationale = "LLM output invalid. Shown Option 1."
            gating = "N/A"
        else:
            result_json = json.loads(json_match.group(1))
            idx = result_json.get("selected_option_index", 1) - 1
            if 0 <= idx < len(candidates):
                selected_idx = idx
            else:
                selected_idx = 0
            
            rationale = result_json.get("rationale", "No rationale provided.")
            gating = result_json.get("gating_strategy", "N/A")
            
        selected_panel = candidates[selected_idx].copy()
        
        # Add missing marker notes
        for m in missing_markers:
            selected_panel[m] = {"Note": "Not found in library"}

        return {
            "status": "success",
            "selected_panel": selected_panel,
            "rationale": rationale,
            "gating_strategy": gating
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}