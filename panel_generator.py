import json
import re
from data_preprocessing import load_antibody_data, normalize_marker_name, aggregate_antibodies_by_marker
from llm_api_client import consult_gpt_oss

def generate_panel_simple(user_markers, antibody_data_csv, channel_mapping_json):
    """
    A simplified, robust panel generator.
    1. Loads data.
    2. Filters available antibodies for user markers.
    3. Asks LLM to select a valid combination (unique system codes) in ONE go.
    """
    print(f"--- Starting Simple Panel Generation for: {user_markers} ---")

    # 1. Load Data
    antibody_df = load_antibody_data(antibody_data_csv, channel_mapping_json)
    if antibody_df is None:
        return {"status": "error", "message": "Could not load antibody data CSV."}
    
    try:
        with open('fluorochrome_brightness.json', 'r') as f:
            brightness_data = json.load(f)
    except FileNotFoundError:
        # Fallback if file missing, though not strictly critical for basic matching
        brightness_data = {} 

    # 2. Aggregate and Filter Antibodies
    # We get a dictionary: {"cd4": [list of antibodies], "cd8": [...]}
    antibodies_by_norm_marker, _ = aggregate_antibodies_by_marker(antibody_df, brightness_data)

    available_antibodies = {}
    markers_missing = []

    for user_marker in user_markers:
        norm_marker = normalize_marker_name(user_marker)
        if norm_marker in antibodies_by_norm_marker:
            # We store using the USER'S original marker name to avoid confusion in the prompt
            available_antibodies[user_marker] = antibodies_by_norm_marker[norm_marker]
        else:
            markers_missing.append(user_marker)

    if not available_antibodies:
        return {
            "status": "error", 
            "message": f"None of the requested markers were found in the library. Missing: {markers_missing}"
        }

    # 3. Construct the Prompt
    # We send the simplified antibody list to the LLM
    
    prompt_data = {}
    for m, abs_list in available_antibodies.items():
        # Simplify the list for the LLM to save tokens and reduce noise
        prompt_data[m] = []
        for ab in abs_list:
            prompt_data[m].append({
                "clone": ab['clone'],
                "fluorochrome": ab['fluorochrome'],
                "system_code": ab['system_code'], # CRITICAL for conflict checking
                "brand": ab.get('brand', 'N/A'), # Include Brand
                "catalog_number": ab.get('catalog_number', 'N/A') # Include Catalog Number
            })

    prompt = f"""
You are an expert flow cytometry panel designer.

**Goal:** Design a valid flow cytometry panel for these markers: {", ".join(available_antibodies.keys())}.

**Available Antibodies (Lab Inventory):**
{json.dumps(prompt_data, indent=2, ensure_ascii=False)}

**CRITICAL RULES:**
1.  **One Antibody per Marker:** Select exactly one antibody for each marker listed above.
2.  **UNIQUE System Codes:** The 'system_code' MUST be unique for every selected antibody. Two antibodies cannot share the same system_code (e.g. 'RED_780' and 'RED_780' is a conflict).
3.  **Maximize Compatibility:** If multiple options exist, choose the combination that ensures all markers can be detected.

**Output Format:**
Return a SINGLE JSON object with this structure:
{{
  "panel": [
    {{ "marker": "MarkerName", "fluorochrome": "FluorName", "clone": "CloneName", "system_code": "SystemCode", "brand": "BrandName", "catalog_number": "CatalogNumber" }}
  ],
  "rationale": "Brief explanation of why this combination was chosen."
}}

Respond with ONLY the valid JSON.
"""

    print("Sending simplified prompt to LLM...")
    llm_response = consult_gpt_oss(prompt)
    print("Received response from LLM.")

    # 4. Parse Response
    try:
        # Basic cleaning to find JSON object
        json_match = re.search(r"(\{[\s\S]*\})", llm_response)
        if not json_match:
            return {"status": "error", "message": f"LLM returned invalid format: {llm_response[:100]}..."}
        
        result_json = json.loads(json_match.group(1))
        
        # Basic Validation
        panel = result_json.get("panel", [])
        rationale = result_json.get("rationale", "No rationale provided.")
        
        # Check for missing markers in the LLM output
        final_panel_dict = {}
        for item in panel:
            if "marker" in item:
                final_panel_dict[item["marker"]] = item
        
        # Add notes for missing markers (both from inventory and LLM omission)
        for m in markers_missing:
            final_panel_dict[m] = {"Note": "Not found in library"}
            
        for m in user_markers:
            if m not in final_panel_dict and m not in markers_missing:
                 final_panel_dict[m] = {"Note": "LLM failed to select an antibody (possible conflict)"}

        return {
            "status": "success",
            "panel_data": {
                "Panel": final_panel_dict,
                "Design_Rationale": rationale,
                "Gating_Strategy": "N/A (Simple Mode)" 
            }
        }

    except json.JSONDecodeError:
        return {"status": "error", "message": f"Failed to parse LLM JSON. Response: {llm_response}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}