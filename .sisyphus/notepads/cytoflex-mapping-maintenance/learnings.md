# CytoFLEX S Mapping Maintenance Learnings

## Canonical Naming Conventions

- Unicode variants (®™) are accepted as aliases in channel_mapping.json
- Slash variants (PE/Cyanine7 vs PE-Cy7) are resolved to hyphenated forms
- Abbreviated forms (AF647, BV421, PB) map to full names

## Data Model Architecture

The system uses 4 files with clear separation:
1. `channel_mapping.json` - Runtime source of truth, consumed by data_preprocessing.py
2. `fluorochrome_brightness.json` - Brightness ratings 1-5
3. `spectral_data.json` - Spectral visualization data (peak, sigma, color, category)
4. `data/cytoflex_s_fluorochrome_mapping.csv` - Human reference catalog, not runtime-loaded

## Runtime Behavior

- `load_antibody_data()` performs case-insensitive matching via lowercase normalization
- Missing channel mappings result in System_Code='UNKNOWN' (excluded from panels)
- Missing brightness defaults to 3 (medium)
- CSV file is NOT loaded at runtime - confirmed by code inspection

## System Code Catalog

14 detectors organized by laser:
- Violet (405nm): V1_PB450, V2_KO525, V3_V610, V4_V660, V5_V780
- Blue (488nm): B1_FITC, B2_PerCP
- Yellow-Green (561nm): Y1_PE, Y2_ECD, Y3_PC5, Y4_PC7
- Red (638nm): R1_APC, R2_A700, R3_A750

## Synchronization Drift

Current drift check reveals 2 entries in JSON not in CSV (Alexa Fluor 594, KIRAVIA Blue 520) because CSV uses Unicode variants (®™) as canonical names. This is acceptable since CSV is reference-only.
