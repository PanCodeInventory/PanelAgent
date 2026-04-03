# Learnings: JSON Path Hardening

## Task 2: Config Resolver

### Pattern: Centralized Path Resolution with parent[N]

**Problem:**
- Multiple endpoint files had duplicate `_project_root()` implementations
- Each endpoint calculated project root using different parent[N] values based on their file location
- Example: `backend/app/api/v1/endpoints/*.py` used `parents[5]`, while config.py needs `parents[3]`

**Solution:**
- Added centralized `project_root()` function in `backend/app/core/config.py`
- Use `parents[3]` because config.py is at `backend/app/core/config.py`:
  ```
  Path(__file__)           → .../backend/app/core/config.py
  parents[0]              → .../backend/app/core/
  parents[1]              → .../backend/app/
  parents[2]              → .../backend/
  parents[3]              → .../ (project root)
  ```

**Key Insight:**
- The correct parent[N] value depends on file depth from project root
- Always verify: `Path(__file__).parents[N] / "backend"` and `Path(__file__).parents[N] / "tests"` should exist
- Write tests that verify the path contains expected subdirectories

### Pattern: Name-to-Attribute Mapping for Static Data Paths

**Problem:**
- Direct access to Settings attributes (e.g., `settings.CHANNEL_MAPPING_FILE`) couples code to implementation details
- Changing Settings field names would break all consumers

**Solution:**
- Created `_NAME_MAP` dictionary mapping logical names to Settings attributes:
  ```python
  _NAME_MAP = {
      "channel_mapping": "CHANNEL_MAPPING_FILE",
      "brightness_mapping": "BRIGHTNESS_MAPPING_FILE",
      "spectral_data": "SPECTRAL_DATA_FILE",
  }
  ```
- `resolve_static_data_path(name)` function uses this map to get the Settings attribute

**Benefits:**
- Abstraction layer between logical names and implementation
- Can change Settings field names without breaking API
- Clear semantic names vs. implementation details

### Pattern: Absolute Path Verification in Tests

**Testing Strategy:**
- Verify `project_root()` returns absolute path using `Path.is_absolute()`
- Verify path contains expected directories using `path.exists()` and `path.is_dir()`
- Verify resolved paths point to existing files using `path.exists()` and `path.is_file()`
- Test that all paths are absolute to ensure no relative path issues

**Test Coverage:**
1. `project_root()` returns absolute path
2. `project_root()` contains `backend/` directory
3. `project_root()` contains `tests/` directory
4. `resolve_static_data_path("channel_mapping")` → channel_mapping.json
5. `resolve_static_data_path("brightness_mapping")` → fluorochrome_brightness.json
6. `resolve_static_data_path("spectral_data")` → spectral_data.json
7. All resolved paths are absolute
8. `resolve_static_data_path()` raises KeyError for unknown names

### Backward Compatibility

**Principle:**
- Never modify existing Settings class fields or defaults
- Never change behavior of existing functions like `get_settings()`
- New additions should be additive only

**Implementation:**
- Added new functions to config.py without touching Settings class
- Existing endpoint files continue to work unchanged
- Task 5 will update endpoints to use the new helpers

## Task 1: CWD Dependency Regression Test

### Pattern: Testing CWD Dependencies

**Problem:**
- `panel_generator.py` line 272 uses `open('fluorochrome_brightness.json', 'r')` - a bare relative path
- When CWD is not the project root, the file cannot be found
- The code catches `FileNotFoundError` and falls back to empty dict `{}` - a silent failure

**Solution (Test Implementation):**
- Created `tests/test_json_path_resolution.py` with `test_generate_candidate_panels_is_cwd_independent`
- Use `monkeypatch.chdir(tmp_path)` to change CWD to a temp directory
- Mock LLM calls to prevent network calls
- Mock `aggregate_antibodies_by_marker` to capture what brightness_data is passed
- Assert that brightness_data SHOULD be loaded even from non-root CWD

**Test Results:**
- RED state: Test FAILS when CWD is temp directory
  - `brightness_data = {}` because FileNotFoundError was caught
  - Assertion fails: "Brightness data should be loaded even from non-root CWD. FAILURE proves the bug: panel_generator.py line 272 uses open('fluorochrome_brightness.json', 'r') which is CWD-dependent. Got brightness: {}"

**Key Insight:**
- The code catches FileNotFoundError internally, so no exception propagates
- Need to verify that brightness_data is NOT empty to prove the bug
- Mocking `aggregate_antibodies_by_marker` lets us inspect what brightness_data was used
- This proves the CWD dependency exists: file loads from project root but not from temp CWD

## Task 3: Fix panel_generator.py - GREEN Phase

### Pattern: Config-Backed Path Replacement

**Problem:**
- `panel_generator.py` line 272 used `open('fluorochrome_brightness.json', 'r')` - a bare relative path
- This is CWD-dependent: works only when CWD is project root

**Solution:**
- Added import: `from backend.app.core.config import resolve_static_data_path`
- Replaced hardcoded path with config-backed resolver:
  ```python
  # BEFORE (CWD-dependent):
  with open('fluorochrome_brightness.json', 'r') as f:
  
  # AFTER (CWD-independent):
  brightness_path = resolve_static_data_path("brightness_mapping")
  with open(brightness_path, 'r') as f:
  ```

**Key Points:**
- FileNotFoundError fallback preserved for robustness
- Only the JSON loading path changed, no other logic
- Import added at line 12 (after existing backend imports)
- Tests verify: T1 test passes, all 213 tests pass

**Verification:**
- T1 regression test: PASSED
- Full test suite: 213 passed in 1.57s
- No LSP diagnostics in modified file

## Task 6: Test Fixture Alignment

### Pattern: Centralized Path Resolution for Test Fixtures

**Problem:**
- Test fixtures in `tests/conftest.py` used hardcoded JSON file paths:
  - `project_root / "channel_mapping.json"`
  - `project_root / "fluorochrome_brightness.json"`
- This couples tests to specific file names and creates redundant path logic
- Inconsistent with production code that uses `resolve_static_data_path()`

**Solution:**
- Updated fixtures to use `resolve_static_data_path()` from config:
  ```python
  # BEFORE:
  with open(project_root / "channel_mapping.json", "r", encoding="utf-8") as f:
  
  # AFTER:
  with open(resolve_static_data_path("channel_mapping"), "r", encoding="utf-8") as f:
  ```

**Fixtures Updated:**
1. `channel_map`: Uses `resolve_static_data_path("channel_mapping")`
2. `brightness_data`: Uses `resolve_static_data_path("brightness_mapping")`
3. `antibody_df`: Uses `mapping_file=str(resolve_static_data_path("channel_mapping"))`
4. `alias_antibody_df`: Uses `mapping_file=str(resolve_static_data_path("channel_mapping"))`

**Characterization Test Updated:**
- `tests/characterization/test_multi_encoding.py`: Uses same pattern

**Verification:**
- All 16 characterization tests pass
- 210 of 215 total tests pass
- 5 pre-existing failures in production code (unrelated to fixtures)

### Key Insight

Test fixtures should use the same centralized path resolution as production code to ensure consistency and maintainability. Using `resolve_static_data_path()` ensures:
1. Single source of truth for file paths
2. Consistent naming conventions across code
3. Easier to update file names in one place (config)
4. Better test maintainability

## Task 5: Endpoint Unification

### Pattern: Eliminating Duplicate _project_root() Functions

**Problem:**
- 4 endpoint files (`panels.py`, `recommendations.py`, `spectra.py`, `quality_registry.py`) each had identical `_project_root()` implementations
- Each used `Path(__file__).resolve().parents[5]` to find project root
- This duplicated logic and made maintenance harder

**Solution:**
- Added `project_root, resolve_static_data_path` to existing config import in all 4 files
- Removed local `_project_root()` functions
- Replaced `_project_root()` calls with `project_root()` for inventory path resolution
- Replaced `root / settings.CHANNEL_MAPPING_FILE` with `resolve_static_data_path("channel_mapping")`
- Replaced `root / settings.BRIGHTNESS_MAPPING_FILE` with `resolve_static_data_path("brightness_mapping")`
- Replaced `root / settings.SPECTRAL_DATA_FILE` with `resolve_static_data_path("spectral_data")`

### Specific Changes per File

**panels.py:**
- Import: Added `project_root, resolve_static_data_path`
- Removed: `_project_root()` function
- `_resolve_inventory_path()`: `root = _project_root()` → `root = project_root()`
- `_load_inventory_df()`: `mapping_file = root / settings.CHANNEL_MAPPING_FILE` → `mapping_file = resolve_static_data_path("channel_mapping")`
- `diagnose_panels()`: `brightness_file = root / settings.BRIGHTNESS_MAPPING_FILE` → `brightness_file = resolve_static_data_path("brightness_mapping")`

**recommendations.py:**
- Import: Added `project_root, resolve_static_data_path`
- Removed: `_project_root()` function
- `_resolve_inventory_path()`: `root = _project_root()` → `root = project_root()`
- `_load_inventory_df()`: `mapping_file = root / settings.CHANNEL_MAPPING_FILE` → `mapping_file = resolve_static_data_path("channel_mapping")`

**spectra.py:**
- Import: Added `resolve_static_data_path`
- Removed: `_project_root()` function
- `_load_spectral_db()`: `filepath = root / settings.SPECTRAL_DATA_FILE` → `filepath = resolve_static_data_path("spectral_data")`
- Removed `settings = get_settings()` from `_load_spectral_db()` (no longer needed)

**quality_registry.py:**
- Import: Added `project_root, resolve_static_data_path`
- Removed: `_project_root()` function
- `_resolve_inventory_path()`: `root = _project_root()` → `root = project_root()`
- `_load_inventory_df()`: `mapping_file = root / settings.CHANNEL_MAPPING_FILE` → `mapping_file = resolve_static_data_path("channel_mapping")`

### Preserved Behavior

The following settings remain unchanged and are still used directly:
- `settings.INVENTORY_DIR` - for inventory path resolution (not a static JSON file)
- `settings.SPECIES_INVENTORY_MAP` - for species-to-file mapping
- `settings.OPENAI_*` - for LLM config (in llm_api_client.py, not endpoints)

### Verification

- API tests: 44 passed in 0.99s
- Full suite: 215 passed in 1.46s
- No LSP diagnostics errors in modified files
- All endpoints preserve original behavior
- No changes to test files, schemas, or status codes

### Key Insight

**Distinguish between static JSON files and dynamic directory paths:**
- Static JSON files (channel_mapping, brightness_mapping, spectral_data) → Use `resolve_static_data_path()`
- Dynamic directory paths (inventory directory with CSV files) → Use `project_root() + settings.INVENTORY_DIR`

The centralized helpers eliminate code duplication while ensuring all modules use consistent path resolution logic.

## Task 7: Cross-Flow CWD-Independence Regression Test

### Pattern: End-to-End API CWD Independence Testing

**Problem:**
- While unit tests verified individual functions are CWD-independent
- No test verified the complete API flow works from non-root CWD
- Risk that endpoint-level changes could reintroduce CWD dependencies

**Solution:**
- Created `tests/test_cwd_independence.py` with 3 cross-flow regression tests
- Each test covers a major API endpoint:
  1. `test_api_panels_generate_from_nonroot_cwd`: `/api/v1/panels/generate`
  2. `test_api_recommendations_from_nonroot_cwd`: `/api/v1/recommendations/markers`
  3. `test_api_evaluation_from_nonroot_cwd`: `/api/v1/panels/evaluate`

**Test Structure:**
```python
@pytest.mark.asyncio
async def test_api_panels_generate_from_nonroot_cwd(client, monkeypatch, tmp_path):
    # Change CWD to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Verify CWD is actually changed
    assert os.getcwd() == str(tmp_path)
    
    # Mock LLM calls to prevent network dependencies
    with patch("llm_api_client.consult_gpt_oss", return_value=llm_response), \
         patch("panel_generator.consult_gpt_oss", return_value=llm_response):
        resp = await client.post("/api/v1/panels/generate", json=payload)
    
    # Verify successful response
    assert resp.status_code == 200
    assert body["status"] == "success"
```

**Key Technical Details:**
- Uses ASGITransport for FastAPI app testing (from httpx.AsyncClient)
- Follows existing test patterns from `tests/api/conftest.py`
- Patches both `llm_api_client.consult_gpt_oss` and `panel_generator.consult_gpt_oss`
- Mock responses are valid JSON strings matching expected response format
- Each test includes payload with valid data for its endpoint

**Verification:**
- All 3 new tests pass
- Full test suite: 218 passed in 1.46s
- No regressions introduced

### Key Insight

**Cross-flow tests provide end-to-end validation:**
- Unit tests verify individual functions use absolute paths
- Cross-flow tests verify the complete API flow works when CWD changes
- This ensures that even if unit tests pass, the integration works correctly

**CWD independence is now verified across the full stack:**
1. `panel_generator.py` → uses `resolve_static_data_path()` (Task 3)
2. Test fixtures → use `resolve_static_data_path()` (Task 6)
3. Endpoints → use `project_root()` and `resolve_static_data_path()` (Task 5)
4. API flow → works from non-root CWD (Task 7 - cross-flow test)

This comprehensive testing ensures future changes won't break CWD independence at any level.

### Test Coverage Matrix

| Level | Test File | Coverage | Status |
|-------|-----------|----------|--------|
| Unit | `tests/test_json_path_resolution.py` | `panel_generator.py` path resolution | ✅ Passed |
| Unit | `tests/test_config_path_resolution.py` | `config.py` helper functions | ✅ Passed |
| Integration | `tests/test_cwd_independence.py` | Full API flow from non-root CWD | ✅ Passed |

The regression test suite now covers:
- Unit level: individual function path resolution
- Integration level: complete API flow CWD independence

- Scope audit on 2026-04-03: backend path-resolution changes stayed within `backend/app/core/config.py`, endpoint modules, `panel_generator.py`, and tests; no `backend/app/domain/` or `backend/app/data/` moves detected.
