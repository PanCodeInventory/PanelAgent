import pandas as pd
import json
import re

def normalize_marker_name(name):
    """
    Normalizes a marker name by:
    1. Removing content in parentheses (e.g. "CD96 (TACTILE)" -> "CD96")
    2. Converting to lowercase
    3. Removing delimiters (spaces, dashes)
    4. Handling common suffixes
    """
    if not isinstance(name, str):
        return ""
    
    # Remove parentheses and content inside them
    name = re.sub(r'\s*\(.*?\)', '', name)
    
    name = name.lower().replace("-", "").replace(" ", "")
    if name.endswith('a') or name.endswith('b'): # Handle CD8a, CD8b
        name = name[:-1]
    return name

def parse_target_aliases(target_string):
    """
    Parses a target string like "CD274 (B7-H1, PD-L1)" and returns a list of all normalized aliases.
    Handles comma and slash separators, e.g., CD45 (LCA/T200).
    """
    if not isinstance(target_string, str):
        return []

    # Extract the main name (text before parentheses) and normalize it
    main_name = re.sub(r'\s*\(.*\)', '', target_string).strip()
    all_names = {normalize_marker_name(main_name)}

    # Extract content from within parentheses
    aliases_in_parens = re.findall(r'\((.*?)\)', target_string)
    
    # Process each group of aliases found
    for group in aliases_in_parens:
        # Split by comma or slash, and strip whitespace from each part
        aliases = [name.strip() for name in re.split(r'[,/]', group)]
        for alias in aliases:
            if alias:  # Ensure not an empty string
                all_names.add(normalize_marker_name(alias))

    return list(all_names)

def load_antibody_data(file_path, mapping_file=None):
    """
    Loads antibody inventory from a CSV file, parses target aliases, 
    and optionally adds a System_Code based on a mapping file.
    """
    try:
        df = pd.read_csv(file_path)

        # --- NEW: Parse Aliases into a new column ---
        df['Target_Aliases'] = df['Target'].apply(parse_target_aliases)

        if mapping_file:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                channel_map = json.load(f)
            
            # Normalize map keys to lowercase for robust matching
            channel_map = {k.lower(): v for k, v in channel_map.items()}

            # Use lower() for case-insensitive mapping
            df['System_Code'] = df['Fluorescein'].str.lower().map(channel_map)
            df['System_Code'].fillna('UNKNOWN', inplace=True)

        return df
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"Error loading data or mapping: {e}")
        return None

def format_antibodies_for_llm(df):
    """
    Formats the antibody DataFrame into a list of dictionaries suitable for LLM input.
    Each dictionary will contain 'Fluorescein', 'Target', 'System_Code', 
    'Brand', 'Catalog Number', 'Clone', and the new 'Target_Aliases'.
    """
    if df is None:
        return []
    
    # Ensure 'Target_Aliases' column exists; create it if it doesn't
    if 'Target_Aliases' not in df.columns:
        df['Target_Aliases'] = df['Target'].apply(parse_target_aliases)
    
    # Select and rename columns for clarity for the LLM
    llm_data = df[['Fluorescein', 'Target', 'System_Code', 'Brand', 'Catalog Number', 'Clone', 'Target_Aliases']].copy()
    
    # Convert DataFrame to a list of dictionaries
    return llm_data.to_dict(orient='records')

def aggregate_antibodies_by_marker(antibody_df, brightness_data):
    """
    Aggregates antibody data by marker, simplifying the information and adding brightness.
    This is the new "information hub" for antigens.
    """
    antibodies_by_marker = {}
    marker_expression = {}

    # Ensure brightness keys are lowercase for case-insensitive matching
    brightness_data_lower = {k.lower(): v for k, v in brightness_data.items()}

    for _, row in antibody_df.iterrows():
        # The primary, un-normalized marker name from the 'Target' column
        main_marker = row['Target'].split('(')[0].strip()
        
        if not row['Target_Aliases']:
            continue

        # Store the simplified antibody info
        fluorochrome = row['Fluorescein']
        brightness = brightness_data_lower.get(fluorochrome.lower(), 3) # Default to 3 (Medium)

        antibody_info = {
            "clone": row['Clone'],
            "fluorochrome": fluorochrome,
            "brightness": brightness,
            "system_code": row.get('System_Code', 'UNKNOWN'),
            "brand": row.get('Brand', 'N/A'), # Added Brand
            "catalog_number": row.get('Catalog Number', 'N/A') # Added Catalog Number
        }

        # --- FIX: Index antibody under ALL aliases ---
        # Instead of just picking the first alias, we add this antibody to the list 
        # for EVERY alias found. This creates a comprehensive inverted index.
        for alias in row['Target_Aliases']:
            if alias not in antibodies_by_marker:
                antibodies_by_marker[alias] = []
            antibodies_by_marker[alias].append(antibody_info)

        # Store expression level (logic remains similar, mapping to all aliases might be overkill 
        # but mapping to the main one is usually enough for the prompt context)
        if 'Expression Level' in row and pd.notna(row['Expression Level']):
            # We map expression level to ALL aliases too, to be safe
            for alias in row['Target_Aliases']:
                current_level = marker_expression.get(alias)
                new_level = row['Expression Level']
                
                level_priority = {"High": 3, "Medium": 2, "Low": 1}
                
                if not current_level or level_priority.get(new_level, 0) > level_priority.get(current_level, 0):
                    marker_expression[alias] = new_level

    return antibodies_by_marker, marker_expression


if __name__ == "__main__":
    csv_file = "流式抗体库-20250625小鼠.csv"
    mapping_file = "channel_mapping.json"
    brightness_file = "fluorochrome_brightness.json"
    
    antibody_df = load_antibody_data(csv_file, mapping_file)

    if antibody_df is not None:
        print("Antibody data loaded successfully.")
        
        # llm_formatted_data = format_antibodies_for_llm(antibody_df)
        # print("\nFormatted data for LLM (first 2 entries):")
        # print(json.dumps(llm_formatted_data[:2], indent=2, ensure_ascii=False))

        with open(brightness_file, 'r') as f:
            brightness_data = json.load(f)

        # --- Test the new aggregation function ---
        print("\n--- Testing New Aggregation Function ---")
        antibodies_by_marker, marker_expression = aggregate_antibodies_by_marker(antibody_df, brightness_data)
        
        print("\nMarker Expression Levels Found:")
        print(json.dumps(marker_expression, indent=2))

        print("\nAntibodies for 'cd3':")
        if 'cd3' in antibodies_by_marker:
            print(json.dumps(antibodies_by_marker['cd3'], indent=2, ensure_ascii=False))
        else:
            print("No data found for 'cd3'. Check marker normalization.")

        print("\nAntibodies for 'nk1.1':")
        if 'nk1.1' in antibodies_by_marker:
            print(json.dumps(antibodies_by_marker['nk1.1'], indent=2, ensure_ascii=False))
        else:
            print("No data found for 'nk1.1'. Check marker normalization.")

