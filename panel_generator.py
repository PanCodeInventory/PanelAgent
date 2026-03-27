import json
import re
import random
import ast
from data_preprocessing import load_antibody_data, normalize_marker_name, aggregate_antibodies_by_marker
from llm_api_client import consult_gpt_oss


def _infer_marker_type(marker_name, experimental_goal):
    marker_lower = marker_name.lower()
    goal_lower = experimental_goal.lower()

    lineage_markers = {
        'cd3', 'cd4', 'cd8', 'cd8a', 'cd19', 'cd20', 'cd45', 'cd45ra', 'cd45ro',
        'cd11b', 'cd11c', 'cd14', 'cd16', 'cd56', 'nk1.1', 'ter119', 'b220',
        'tcr', 'tcrb', 'tcrgd', 'cd90', 'cd127'
    }
    activation_markers = {
        'cd25', 'cd44', 'cd69', 'cd62l', 'cd71', 'cd107a', 'cd134', 'cd137',
        'cd154', 'cd178', 'ki-67', 'hla-dr'
    }
    exhaustion_markers = {
        'pd-1', 'pd1', 'tigit', 'tim-3', 'tim3', 'lag-3', 'lag3', 'ctla-4',
        'ctla4', 'cd160', '2b4', 'btla'
    }
    functional_markers = {
        'ifn', 'tnf', 'il-', 'il17', 'il-17', 'il2', 'il-2', 'granzyme', 'perforin',
        'gm-csf', 'foxp3', 't-bet', 'eomes', 'gata3', 'ror', 'bcl-6', 'annexin'
    }

    if marker_lower in lineage_markers or marker_lower.startswith('cd') and marker_lower[:3] in {'cd3', 'cd4', 'cd8'}:
        return 'Lineage'
    if any(token in marker_lower for token in exhaustion_markers):
        return 'Exhaustion'
    if any(token in marker_lower for token in functional_markers):
        return 'Functional'
    if any(token in marker_lower for token in activation_markers):
        return 'Activation'
    if any(word in goal_lower for word in ['cytokine', 'function', 'functional']) and marker_lower.startswith('il'):
        return 'Functional'
    return 'Phenotyping'


def _build_marker_reason(marker_name, marker_type, experimental_goal):
    goal_lower = experimental_goal.lower()

    if marker_type == 'Lineage':
        return f"Anchors the core cell population needed for {experimental_goal.strip() or 'this experiment'}."
    if marker_type == 'Activation':
        return f"Captures activation state changes relevant to {experimental_goal.strip() or 'the stated goal'}."
    if marker_type == 'Exhaustion':
        return f"Profiles exhaustion or checkpoint biology highlighted by {experimental_goal.strip() or 'the experimental question'}."
    if marker_type == 'Functional':
        return f"Measures functional output associated with {experimental_goal.strip() or 'the experiment'}."
    if 'tumor' in goal_lower:
        return 'Useful for distinguishing phenotype within the tumor-associated immune compartment.'
    return 'Included because it is a relevant inventory marker for the requested study objective.'


def _fallback_recommend_markers(experimental_goal, num_colors, available_targets_list):
    goal_lower = experimental_goal.lower()
    normalized_to_original = {
        normalize_marker_name(target): target for target in available_targets_list if target
    }

    priority_groups = [
        ['cd45', 'cd3', 'cd4', 'cd8', 'cd8a', 'cd19', 'cd11b', 'cd11c', 'nk1.1', 'cd56'],
        ['cd44', 'cd62l', 'cd69', 'cd25', 'ki67', 'ki-67', 'cd107a'],
        ['pd1', 'pd-1', 'tigit', 'tim3', 'tim-3', 'lag3', 'lag-3', 'ctla4', 'ctla-4'],
        ['ifng', 'ifn-g', 'ifnγ', 'tnfa', 'tnf-a', 'il2', 'il-2', 'il17', 'il-17', 'perforin', 'granzymeb', 'foxp3'],
    ]

    if 'exhaust' in goal_lower or 'checkpoint' in goal_lower:
        priority_groups = [priority_groups[0], priority_groups[2], priority_groups[1], priority_groups[3]]
    elif any(word in goal_lower for word in ['cytokine', 'functional', 'activation']):
        priority_groups = [priority_groups[0], priority_groups[3], priority_groups[1], priority_groups[2]]

    selected = []
    seen = set()
    for group in priority_groups:
        for candidate in group:
            normalized = normalize_marker_name(candidate)
            original = normalized_to_original.get(normalized)
            if original and original not in seen:
                selected.append(original)
                seen.add(original)
            if len(selected) >= num_colors:
                break
        if len(selected) >= num_colors:
            break

    if len(selected) < num_colors:
        for target in available_targets_list:
            if target not in seen:
                selected.append(target)
                seen.add(target)
            if len(selected) >= num_colors:
                break

    details = []
    for marker in selected[:num_colors]:
        marker_type = _infer_marker_type(marker, experimental_goal)
        details.append(
            {
                'marker': marker,
                'type': marker_type,
                'reason': _build_marker_reason(marker, marker_type, experimental_goal),
            }
        )

    return {
        'status': 'success',
        'markers_detail': details,
        'selected_markers': [item['marker'] for item in details],
        'message': 'LLM unavailable; generated heuristic recommendations from inventory.',
    }

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

**Output Format (Strict JSON):**
Return ONLY a valid JSON object. Do NOT use Markdown code blocks. Use DOUBLE QUOTES for ALL keys and string values.
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

    llm_response = consult_gpt_oss(prompt) or ""
    
    # Parse Response
    try:
        # Clean potential markdown
        cleaned_response = llm_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        json_match = re.search(r"(\{[\s\S]*\})", cleaned_response)
        if not json_match:
            print("LLM format invalid. Defaulting to Option 1.")
            selected_idx = 0
            rationale = "LLM output invalid. Shown Option 1."
            gating_detail = []
        else:
            json_str = json_match.group(1)
            try:
                result_json = json.loads(json_str)
            except json.JSONDecodeError:
                # Fallback: Try parsing as Python literal (handles single quotes)
                result_json = ast.literal_eval(json_str)

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
        raw_preview = llm_response[:100]
        return {"status": "error", "message": f"Parsing Error: {str(e)}. Raw: {raw_preview}..."}

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

**Output Format (Strict JSON):**
Return a SINGLE JSON object containing a list called "markers_detail". 
Do NOT use Markdown code blocks. Use DOUBLE QUOTES for ALL keys and string values.
{{
  "markers_detail": [
    {{ "marker": "MarkerName", "type": "Category", "reason": "Short explanation..." }},
    {{ "marker": "MarkerName", "type": "Category", "reason": "Short explanation..." }}
  ]
}}
"""

    try:
        llm_response = consult_gpt_oss(prompt) or ""
    except Exception:
        return _fallback_recommend_markers(experimental_goal, num_colors, available_targets_list)

    if not llm_response or llm_response.startswith('连接错误:'):
        return _fallback_recommend_markers(experimental_goal, num_colors, available_targets_list)
    
    try:
        # Clean potential markdown
        cleaned_response = llm_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        json_match = re.search(r"(\{[\s\S]*\})", cleaned_response)
        if not json_match:
            return _fallback_recommend_markers(experimental_goal, num_colors, available_targets_list)
        
        json_str = json_match.group(1)
        try:
            result_json = json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: Try parsing as Python literal (handles single quotes)
            result_json = ast.literal_eval(json_str)

        details = result_json.get("markers_detail", [])
        if not details:
            return _fallback_recommend_markers(experimental_goal, num_colors, available_targets_list)
        
        # Extract simple list of names for the input box
        selected_markers = [item["marker"] for item in details]
        
        return {
            "status": "success",
            "markers_detail": details,
            "selected_markers": selected_markers,
            "raw_response": llm_response
        }
    except Exception as e:
        return _fallback_recommend_markers(experimental_goal, num_colors, available_targets_list)
