# CytoFLEX S Fluorochrome Mapping Maintenance

## Purpose

This document governs the fluorochrome-to-detector mapping system for the Beckman Coulter CytoFLEX S flow cytometer. It provides canonical naming conventions, maintenance procedures, and synchronization checks to ensure consistent channel assignment across the PanelAgent system.

## Runtime Authority

**`channel_mapping.json` is the runtime source of truth.**

This markdown file provides maintenance guidance only. Production code does not parse this file. Runtime channel assignment happens via `data_preprocessing.py:load_antibody_data()`, which loads `channel_mapping.json` and maps fluorochrome names to System_Code values.

## Scope

**Covered:**
- Fluorochrome to detector (System_Code) mapping
- Canonical name aliases and variants

**Not Covered:**
- Brightness values (stored in `fluorochrome_brightness.json`)
- Spectral peak data (stored in `spectral_data.json`)
- Antibody inventory metadata

## Data Model

| File | Purpose | Runtime-Loaded |
|------|---------|----------------|
| `channel_mapping.json` | Fluorochrome → System_Code mapping | Yes |
| `fluorochrome_brightness.json` | Brightness ratings (1-5) | Yes |
| `spectral_data.json` | Spectral metadata | No (visualization) |
| `data/cytoflex_s_fluorochrome_mapping.csv` | Human reference catalog | No |

Runtime flow:
1. `load_antibody_data()` loads `channel_mapping.json`
2. Maps `Fluorescein` column via case-insensitive lookup
3. Missing mappings default to `UNKNOWN` (excluded from panels)
4. Brightness defaults to 3 (medium) when not found

## Canonical Naming

Accepted alias forms:

| Variant Type | Example | Resolution |
|--------------|---------|------------|
| Unicode marks | `Alexa Fluor® 488` | → `Alexa Fluor 488` |
| Slash forms | `PE/Cyanine7` | → `PE-Cy7` |
| Abbreviations | `AF647`, `BV421`, `PB` | Full names |

All matching is case-insensitive at runtime.

## System Code Catalog

| Laser | Code | Detector | Representative Fluorochromes |
|-------|------|----------|------------------------------|
| Violet | V1_PB450 | 450/45 | Pacific Blue, BV421, DAPI |
| Violet | V2_KO525 | 525/40 | BV510, AmCyan, KIRAVIA Blue 520 |
| Violet | V3_V610 | 610/20 | BV605 |
| Violet | V4_V660 | 660/20 | BV650 |
| Violet | V5_V780 | 780/60 | BV785, BV786 |
| Blue | B1_FITC | 525/40 | FITC, Alexa Fluor 488, BB515 |
| Blue | B2_PerCP | 690/50 | PerCP, PerCP-Cy5.5 |
| Yellow-Green | Y1_PE | 585/42 | PE |
| Yellow-Green | Y2_ECD | 610/20 | Alexa Fluor 594, PE-CF594 |
| Yellow-Green | Y3_PC5 | 690/30 | PE-Cy5, 7-AAD |
| Yellow-Green | Y4_PC7 | 780/60 | PE-Cy7 |
| Red | R1_APC | 660/20 | APC, Alexa Fluor 647 |
| Red | R2_A700 | 712/25 | Alexa Fluor 700, APC-R700 |
| Red | R3_A750 | 780/60 | APC-Cy7, APC/Fire 750, Zombie NIR |

## Status Semantics

| Status | Meaning |
|--------|---------|
| `mapped` | Fluorochrome name exists as a key in `channel_mapping.json` |
| `alias` | Known abbreviation or shorthand — documented for reference but may not be a direct key in `channel_mapping.json` |
| `unsupported` | No compatible detector on this instrument configuration |

## Update Workflow

**Pre-change verification (confirm baseline is clean):**

```bash
python3 << 'EOF'
import json, csv
with open('channel_mapping.json') as f:
    json_keys = set(json.load(f).keys())
with open('data/cytoflex_s_fluorochrome_mapping.csv') as f:
    csv_keys = set(row['fluorochrome'] for row in csv.DictReader(f))
missing = json_keys - csv_keys
if missing:
    print(f"FAIL: {len(missing)} JSON keys not in CSV: {missing}")
else:
    print("PASS: All JSON keys documented in CSV")
EOF

python3 << 'EOF'
import json
with open('channel_mapping.json') as f:
    codes = set(v for v in json.load(f).values() if v != 'UNSUPPORTED')
valid = {'V1_PB450', 'V2_KO525', 'V3_V610', 'V4_V660', 'V5_V780',
         'B1_FITC', 'B2_PerCP', 'Y1_PE', 'Y2_ECD', 'Y3_PC5', 'Y4_PC7',
         'R1_APC', 'R2_A700', 'R3_A750'}
unknown = codes - valid
if unknown:
    print(f"FAIL: Unknown codes: {unknown}")
else:
    print(f"PASS: All {len(codes)} codes are valid")
EOF
```

**Step 1:** Update `channel_mapping.json` (add key → code pair)

**Step 2:** Update `fluorochrome_brightness.json` if new fluorochrome (add rating 1-5)

**Step 3:** Update `spectral_data.json` if new fluorochrome (add peak/sigma/color/category)

**Step 4:** Update `data/cytoflex_s_fluorochrome_mapping.csv` if new fluorochrome

**Step 5:** Add test in `tests/characterization/test_multi_encoding.py`

**Step 6:** Run test suite:

```bash
PYTHONPATH=. python -m pytest tests/ -q
```

**Post-change verification (confirm changes are correct):**

```bash
# Run both sync checks
python3 << 'EOF'
import json, csv
with open('channel_mapping.json') as f:
    json_keys = set(json.load(f).keys())
with open('data/cytoflex_s_fluorochrome_mapping.csv') as f:
    csv_keys = set(row['fluorochrome'] for row in csv.DictReader(f))
missing = json_keys - csv_keys
if missing:
    print(f"FAIL: {len(missing)} JSON keys not in CSV: {missing}")
else:
    print("PASS: All JSON keys documented in CSV")
EOF

python3 << 'EOF'
import json
with open('channel_mapping.json') as f:
    codes = set(v for v in json.load(f).values() if v != 'UNSUPPORTED')
valid = {'V1_PB450', 'V2_KO525', 'V3_V610', 'V4_V660', 'V5_V780',
         'B1_FITC', 'B2_PerCP', 'Y1_PE', 'Y2_ECD', 'Y3_PC5', 'Y4_PC7',
         'R1_APC', 'R2_A700', 'R3_A750'}
unknown = codes - valid
if unknown:
    print(f"FAIL: Unknown codes: {unknown}")
else:
    print(f"PASS: All {len(codes)} codes are valid")
EOF

# Run test suite
PYTHONPATH=. python -m pytest tests/ -q

# Verify keywords in maintenance doc
grep -q "## Change Log Template" data/cytoflex_s_mapping_maintenance.md && echo "PASS: Change Log Template section exists"
grep -q "Status.*Meaning" data/cytoflex_s_mapping_maintenance.md && echo "PASS: Status Semantics section exists"
```

## Synchronization Checks

### Check 1: JSON Keys vs CSV

```bash
python3 << 'EOF'
import json, csv
with open('channel_mapping.json') as f:
    json_keys = set(json.load(f).keys())
with open('data/cytoflex_s_fluorochrome_mapping.csv') as f:
    csv_keys = set(row['fluorochrome'] for row in csv.DictReader(f))
missing = json_keys - csv_keys
if missing:
    print(f"FAIL: {len(missing)} JSON keys not in CSV: {missing}")
else:
    print("PASS: All JSON keys documented in CSV")
EOF
```

**Expected:** `PASS: All JSON keys documented in CSV`

### Check 2: System_Code Coverage

```bash
python3 << 'EOF'
import json
with open('channel_mapping.json') as f:
    codes = set(v for v in json.load(f).values() if v != 'UNSUPPORTED')
valid = {'V1_PB450', 'V2_KO525', 'V3_V610', 'V4_V660', 'V5_V780',
         'B1_FITC', 'B2_PerCP', 'Y1_PE', 'Y2_ECD', 'Y3_PC5', 'Y4_PC7',
         'R1_APC', 'R2_A700', 'R3_A750'}
unknown = codes - valid
if unknown:
    print(f"FAIL: Unknown codes: {unknown}")
else:
    print(f"PASS: All {len(codes)} codes are valid")
EOF
```

**Expected:** `PASS: All 14 codes are valid`

## Change Log Template

| Date | Change | Author | Commit |
|------|--------|--------|--------|
| | | | |

