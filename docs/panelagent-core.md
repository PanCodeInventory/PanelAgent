# PanelAgent core v0.1.3

`panelagent` is an LLM-free computation core backed by SQLite. SQLite is the
only runtime source of truth. Package seeds contain physical dye data and naming
aliases; instrument configuration and antibody inventories can be imported.
One database represents one laboratory and can hold any number of freely named
antibody libraries, such as Mouse, Human, Isotype, or Controls. Panel generation
and diagnosis always operate within exactly one selected library.

## Public Python API

The package exports `connect`, `ensure_schema`, `schema_version`, `Repo`,
`resolve_fluorochrome`, `find_valid_panels`, `generate_candidates`, and
`diagnose_conflicts`. Repository instances receive an explicit SQLite
connection and keep no global state.

## Database

The schema contains `instruments`, `channels`, `channel_mapping`,
`fluorochrome_spectra`, `fluorochrome_aliases`,
`fluorochrome_brightness`, and `antibodies`. Quality state lives directly on an
antibody row in `quality_flag`, `quality_notes`, and `quality_updated_at`.
Writes are transactional, foreign keys are enabled, and databases use WAL.
The `antibodies.library` column identifies the owning library and participates
in the inventory uniqueness constraint.

Database path precedence is:

1. CLI `--db PATH` (accepted anywhere in the command line)
2. `PANELAGENT_DB`
3. `~/.local/share/panelagent/panelagent.db`

Parent directories are created automatically.

## CLI

Install and initialize:

```console
pip install -e ".[mcp]"
pa init
pa init --config-dir config --csv Mouse=inventory/panel_inventory.csv
pa init --config-dir config --inventory-dir inventory
```

Inspection and annotation:

```console
pa db path
pa db stats --json
pa dye list --laser Violet
pa dye show AF488 --json
pa dye alias-add AF-488 "Alexa Fluor® 488"
pa channel list --laser Blue
pa antibody list --library Mouse --flag bad
pa antibody search BioLegend --json
pa antibody annotate 1 --library Mouse --flag warn --note "Low signal"
```

Pure panel computation:

```console
pa panel generate --library Mouse --markers CD3,CD4,CD8 --max 10 --json
pa panel diagnose --library Mouse --markers pd1,ctla4,lag3 --json
```

Every subcommand accepts `--json`, including when it appears after nested
subcommands. Panel generation excludes `quality_flag=bad` by default; use
`--include-bad` to override it. Warnings and dyes with brightness level 1 or 2
are summarized in each candidate.

Inventory-directory library inference recognizes filenames containing `小鼠`,
`人`, or case-insensitive `isotype`. Unidentified filenames are skipped with a
warning. Use `--csv Library=PATH` for an explicit, freely named library.

CSV imports accept Excel-style UTF-8 BOM and CRLF files, silently discard fully
empty trailing rows, and ignore unnamed trailing columns. Rows are skipped with
a warning only when both target and fluorochrome are absent. A missing `Target`
falls back to `Name`; either target or fluorochrome may otherwise remain NULL.
Additional named columns such as `Quantity` are preserved in `extra`. Hidden
files and macOS `._*` AppleDouble files are ignored. Re-imports use a NULL-safe
identity based on library, catalog number, clone, target, and fluorochrome, so
they update existing rows instead of accumulating duplicates.

Literal `-` placeholders in target, fluorochrome, and clone cells are imported
as NULL. Brightness seed names are normalized to spectrum canonical names at
seed time: exact spectrum names take precedence, followed by explicit aliases.
Unresolved brightness keys produce seed warnings. Full vendor spellings such as
`PE/Cyanine7`, `PerCP/Cyanine5.5`, and `Brilliant Violet 421™` resolve through
the same aliases as their short forms. Known dyes without source data remain
unresolved rather than receiving guessed brightness values.

## MCP

Run `pa mcp` to start the optional FastMCP stdio server. Install the `mcp` extra
first. The server exposes read-only tools:

- `list_fluorochromes`, `get_fluorochrome`, `list_channels`
- `search_antibodies`
- `generate_panel`, `diagnose_panel`
- `db_stats`

All tools call the same repository and computation functions used by the CLI.

## Seed synchronization

The editable authority remains `config/`. Files under
`panelagent/data/seed/` are package snapshots and must be recopied or regenerated
after edits to `config/spectral_data.json`,
`config/fluorochrome_brightness.json`, or `config/channel_mapping.json`.
Underscore-prefixed metadata keys are omitted from `spectra.json`.

The 57 CytoFLEX dye mappings collapse to 14 unique physical channel rows under
the required `(instrument_id, channel)` primary key. `AmCyan`, `V450`, `V500`,
and `Fixable Viability Stain 780` intentionally resolve without spectra.
