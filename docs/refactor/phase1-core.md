# v0.1 — panelagent 核心内核（SQLite + seed 随包 + 纯计算 CLI + MCP 薄皮）

你负责 v0.1。只新增代码，**禁止修改** `backend/`、`frontend/`、`panel_generator.py`、`tests/`（现有文件）。不要 git commit。代码与注释用英文，与仓库现有风格一致。

## 设计原则（已与用户拍板，不可偏离）

1. **SQLite 是唯一事实源**。静态 JSON/CSV 降级为导入源；包内 seed 是物理常数。
2. **写死 vs 导入的分界**：
   - 写死（随包 seed）：染料光谱、亮度分级、基础别名表 —— 物理常数与命名约定，全球不变。
   - 导入（用户数据）：仪器通道映射（换仪器才变）、抗体库存 CSV（每实验室不同）。
   - **没有** panels 表、没有独立质量注册表、没有 audit_events、没有 settings 表。
3. **质量信息直接挂在库存行上**（quality_flag/quality_notes 列），不单独建表。
4. **CLI 完全不碰 LLM**。panel 生成/诊断是纯计算（从 panel_generator.py 移植算法）。
5. **所有子命令支持 `--json`**，输出机器可读 JSON 到 stdout——MCP/skill/脚本全部复用 CLI 语义，不搞第二套接口。

## 动工前先读

- `panel_generator.py` 全文（重点：`find_valid_panels`、`generate_candidate_panels`、`diagnose_conflicts`、`_is_usable_system_code`）
- `config/channel_mapping.json`（57 条 短名→通道，CytoFLEX 命名）、`config/fluorochrome_brightness.json`（34 条）、`config/spectral_data.json`（49 条，`_comment` 等下划线键要跳过；key 是全名如 `Alexa Fluor® 488`）
- `inventory/*.csv`（列：`Target,Fluorescein,Clone,Brand,Catalog Number`——注意列名是 **Fluorescein**；`impossible_inventory.csv` 是死锁样本：全部 APC）
- `backend/app/core/config.py`（了解现状即可，不改动）

## 交付物

```
panelagent/
  __init__.py        # 导出主要符号 + __version__
  db.py              # connect(path); ensure_schema(conn) 幂等; schema_version; WAL; row_factory
  models.py          # dataclass: Fluorochrome, ChannelInfo, Antibody, ImportReport, PanelCandidate...
  repo.py            # Repo 类以 connection 为构造参数，无全局状态
  seed.py            # 加载包内 seed 数据并写入 DB
  importers.py       # import_instrument_config(conn, config_dir); import_antibody_csv(conn, csv_path, species)
  engine.py          # 移植的纯算法: find_valid_panels / generate_candidates / diagnose_conflicts（数据源换 SQL JOIN）
  resolve.py         # resolve_fluorochrome(conn, name) —— 精确 + alias，不做模糊猜测
  cli.py             # argparse 子命令; main()
  mcp.py             # FastMCP stdio server（可选依赖）
  __main__.py
  data/seed/
    spectra.json         # 从 config/spectral_data.json 复制（去掉 _comment 等下划线键）
    brightness.json      # 从 config/fluorochrome_brightness.json 复制
    aliases.json         # 精心整理的别名表（见下）
    instruments.json     # 默认仪器: {"vendor":"Beckman","model":"CytoFLEX"} + channel_mapping.json 内容
panelagent/data/seed/aliases.json 生成规则：
    对 channel_mapping.json 的每个 key：若它精确存在于 spectra → 不需要别名；
    否则映射到全名。**已比对的结论（直接用）**：
    - ®-less → ®-full（7 个）: "Alexa Fluor 488/594/647/700" → 对应 ® 版本, "Pacific Blue"→"Pacific Blue™", "BV786"→"Brilliant Violet 786™", "PE-Cy5.5"→ 已有通道但无独立光谱（可归 "PE-Cy5"）, "AmCyan"→ 无对应（保留无光谱）
    - 确实无光谱可对应（保留 resolve 返回通道+亮度但无谱）: "V450", "V500", "Fixable Viability Stain 780", brightness 中的 BUV395/496/563/661/737/805
    目标：channel_mapping 的 57 个 key 全部能 resolve（有谱最好，无谱的明确记录在 aliases.json 旁的 seed README 或 docs 里）。
pyproject.toml         # 仓库根；name=panelagent；console_scripts: pa=panelagent.cli:main；extras: mcp=["mcp>=1.2"]
tests/core/            # 新测试（不动现有 tests/ 文件）
docs/panelagent-core.md
```

## DB schema

路径解析：`--db` > 环境变量 `PANELAGENT_DB` > 默认 `~/.local/share/panelagent/panelagent.db`（目录自动建）。

```sql
PRAGMA journal_mode=WAL;

CREATE TABLE instruments(
  id INTEGER PRIMARY KEY,
  vendor TEXT NOT NULL, model TEXT NOT NULL,
  UNIQUE(vendor, model)
);
CREATE TABLE channels(
  instrument_id INTEGER NOT NULL REFERENCES instruments(id),
  channel TEXT NOT NULL,          -- 'B1_FITC'
  laser TEXT,                     -- 从通道名前缀推断: B→Blue, Y→Yellow, R→Red, V→Violet, UV→UV; 推断不出为 NULL
  PRIMARY KEY(instrument_id, channel)
);
CREATE TABLE channel_mapping(
  instrument_id INTEGER NOT NULL REFERENCES instruments(id),
  fluorochrome TEXT NOT NULL,     -- 短名原样（AF488）
  channel TEXT NOT NULL,
  PRIMARY KEY(instrument_id, fluorochrome)
);
CREATE TABLE fluorochrome_spectra(
  name TEXT PRIMARY KEY,          -- 全名原样（含 ® ™ 符号，勿改写）
  peak_nm REAL, sigma REAL, color TEXT, category TEXT
);
CREATE TABLE fluorochrome_aliases(
  alias TEXT PRIMARY KEY,
  canonical TEXT NOT NULL REFERENCES fluorochrome_spectra(name)
);
CREATE TABLE fluorochrome_brightness(
  name TEXT PRIMARY KEY,
  brightness INTEGER NOT NULL     -- 1..5
);
CREATE TABLE antibodies(
  id INTEGER PRIMARY KEY,
  species TEXT NOT NULL,
  target TEXT NOT NULL,           -- 原样保留大小写（CD3）
  fluorochrome TEXT NOT NULL,     -- 原样（APC / PE-Cy7）
  clone_name TEXT, brand TEXT, catalog_number TEXT,
  extra JSON,                     -- CSV 其余列原始 dict
  quality_flag TEXT,              -- NULL / 'good' / 'warn' / 'bad'
  quality_notes TEXT,
  quality_updated_at TEXT,
  source_file TEXT, imported_at TEXT,
  UNIQUE(species, target, fluorochrome, clone_name, catalog_number)
);
CREATE INDEX idx_antibodies_target ON antibodies(species, target);
```

约束：核心包只依赖 stdlib + pydantic。**禁止** import FastAPI / pandas / openai。CSV 用标准库 csv 模块。所有写操作在事务内，时间戳 UTC ISO-8601。

## CLI（argparse）

```
pa init [--db DB] [--config-dir DIR] [--csv SPEC ...] [--inventory-dir DIR]
pa db path | stats
pa dye list [--laser Violet] | show NAME | alias-add ALIAS CANONICAL
pa channel list [--laser Blue]
pa antibody list [--species S] [--target T] [--flag bad] | search KEYWORD | annotate <id> --flag F --note "..."
pa panel generate --species Mouse --markers CD3,CD4,CD8 [--max N] [--include-bad]
pa panel diagnose --species Mouse --markers CD4,CD8,FoxP3,PD1,CTLA4
pa mcp
```

- `pa init` 无参数时：只灌包内 seed（任何机器开箱即用）。`--config-dir` 导入仪器三件套（channel_mapping 顺带生成 channels 行；spectra/brightness 覆盖 seed 中同名条目）。`--csv Species=path.csv` 可多次；`--inventory-dir` 批量导入目录下 `*.csv`，文件名含"小鼠"→Mouse、含"人"→Human，否则跳过并 warning（可用 `--csv` 显式指定）。幂等：按 UNIQUE 键 upsert，重复 init 不产生重复行。结束打印 ImportReport（各表插入/更新计数）。
- `pa antibody annotate`：更新 quality_flag/quality_notes/quality_updated_at，打印更新后的行。
- `pa panel generate`：移植 `generate_candidate_panels` + `find_valid_panels` 的回溯算法。数据源 = `antibodies JOIN channel_mapping`（fluorochrome 短名精确匹配；匹配不到通道的抗体视同无该选项）。quality_flag='bad' 默认跳过，`--include-bad` 强制包含；结果中 'warn' 的条目标注出来。每个候选 panel 附亮度摘要（用了哪些 ≤2 级暗染料）。无解时自动调 diagnose 逻辑给出原因（含中文文案，照抄 panel_generator.py 现有文案风格）。
- `pa panel diagnose`：移植 `diagnose_conflicts`——死 marker 检查 + 抽屉原理死锁分组。`impossible_inventory.csv` 那种全 APC 输入必须能报出冲突组。
- 表格输出纯文本对齐即可（不引 rich）。`--json` 为全局参数，输出结构化结果（PanelCandidate 包含 markers→clone/fluorochrome/channel/brightness 完整指派）。

## MCP server

`pa mcp`：官方 `mcp` 包 FastMCP，stdio。工具全部只读/纯计算，无写操作：

- `list_fluorochromes(laser=None)` / `get_fluorochrome(name)`
- `list_channels(laser=None)`
- `search_antibodies(species=None, target=None, keyword=None)`
- `generate_panel(species, markers: list[str], max_solutions=10, include_bad=False)`
- `diagnose_panel(species, markers: list[str])`
- `db_stats()`

mcp.py 顶部 import 失败时清晰报错提示 `pip install panelagent[mcp]`。

## 测试（tests/core/，pytest，conftest 用 tmp_path 临时 DB）

至少覆盖：
1. ensure_schema 幂等、WAL 生效
2. 裸 init（仅 seed）：49 spectra / 34 brightness / 默认仪器 + 57 channels + 57 mapping / aliases 全部可 resolve
3. `--config-dir config --inventory-dir inventory` init：antibodies 行数 = CSV 数据行数；重复 init 不涨行
4. resolve_fluorochrome：精确（PE）、别名（AF488→Alexa Fluor® 488）、未知名返回 None
5. annotate 后 list --flag bad 能查出；generate 默认跳过 bad、--include-bad 包含
6. generate：用 inventory/panel_inventory.csv 的 marker 集合产出候选，指派无重复通道，亮度摘要正确
7. diagnose：impossible_inventory.csv 场景报出抽屉死锁；未知 marker 报 dead marker
8. CLI 冒烟：直接调 main()（argv 注入）跑 init→dye show PE→antibody list--species Mouse→panel generate，断言 --json 输出可 json.loads
9. MCP：用 mcp 包 stdio client 连 `pa mcp`，调 db_stats + search_antibodies 断言返回

## 验收（自己全部跑通再收工）

1. `pip install -e ".[mcp]"` 成功，且仓库根现有 pytest 仍可运行：`PYTHONPATH=. python -m pytest tests/ -q` 结果不差于动工前
2. `PYTHONPATH=. python -m pytest tests/core -q` 全绿
3. `ruff check panelagent/ tests/core/` 干净
4. `pa init --config-dir config --inventory-dir inventory && pa db stats` 在干净 DB 上条数符合（贴输出）
5. `pa panel generate --species Mouse --markers CD3,CD4,CD8 --json` 有候选（贴输出）
6. `docs/panelagent-core.md`：公开 API、schema、CLI/MCP 用法、DB 路径规则、seed 与 config/ 的同步约定（config/ 仍是权威编辑处，seed 变更需重新复制）

完成后输出：改动文件清单 + 各验收命令实际输出摘要。
