# PanelAgent 迁移适配指南

> **目标读者：** 迁移协助 AI Agent（如 Claude/Cursor 等编码助手）  
> **迁移方：** 原始实验室 → 新实验室  
> **核心原则：** 替换实验室特有数据，保留通用计算逻辑

---

## 目录

1. [迁移概览](#1-迁移概览)
2. [迁移检查清单](#2-迁移检查清单)
3. [逐项操作说明](#3-逐项操作说明)
   - [3.1 抗体库存 CSV 替换](#31-抗体库存-csv-替换)
   - [3.2 管理员密码设置](#32-管理员密码设置)
   - [3.3 会话签名密钥设置](#33-会话签名密钥设置)
   - [3.4 AI API Key 配置](#34-ai-api-key-配置)
   - [3.5 CORS 白名单配置](#35-cors-白名单配置)
   - [3.6 前端开发白名单配置](#36-前端开发白名单配置)
   - [3.7 物种→文件名映射确认](#37-物种文件名映射确认)
   - [3.8 历史数据清理](#38-历史数据清理)
   - [3.9 仪器通道映射适配（视情况）](#39-仪器通道映射适配视情况)
   - [3.10 库存 CSV 列名映射（视情况）](#310-库存-csv-列名映射视情况)
   - [3.11 Docker 部署参数（视情况）](#311-docker-部署参数视情况)
   - [3.12 语言偏好设置（视情况）](#312-语言偏好设置视情况)
4. [可沿用的部分清单](#4-可沿用的部分清单)
5. [迁移验证清单](#5-迁移验证清单)
6. [附录：关键文件索引](#6-附录关键文件索引)

---

## 1. 迁移概览

### 架构拓扑

```
                        ┌──────────────────┐
                        │  Gateway (nginx) │
                        │   port 8080       │
                        └────────┬─────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
          /admin/*        /api/v1/*          /*
                 │               │               │
        ┌────────▼──────┐       │      ┌────────▼──────┐
        │ Admin Frontend │       │      │ User Frontend │
        │   port 3001    │       │      │   port 3000   │
        └────────┬──────┘       │      └────────┬──────┘
                 │              │               │
                 └──────────────┼───────────────┘
                                │
                       ┌────────▼─────────┐
                       │     Backend      │
                       │   port 8000      │
                       │  FastAPI + LLM   │
                       └──────────────────┘
```

### 迁移流程（三步曲）

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: 替换数据层                                              │
│  替换抗体库存 CSV → 确认通道映射 → 放置新光谱数据（如需）           │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: 修改配置层                                              │
│  管理员密码 → API Key → CORS → 物种映射 → 会话密钥                │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: 清理历史层                                              │
│  删除 SQLite 数据库 → 清空质量登记数据 → 清除投影缓存               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 迁移检查清单

| # | 项 | 优先级 | 操作类型 | 所需信息 |
|---|----|--------|----------|----------|
| 1 | 抗体库存 CSV | **P0-必须** | 替换文件 | 新实验室的抗体库文件（.csv） |
| 2 | 管理员密码 | **P0-必须** | 修改配置 | 新实验室指定的管理员密码 |
| 3 | 会话签名密钥 | **P0-必须** | 修改配置 | 随机生成的字符串 |
| 4 | AI API Key | **P0-必须** | 填写配置 | 新实验室的 API Key、Base URL、模型名 |
| 5 | CORS 白名单 | **P0-必须** | 修改配置 | 新实验室的部署 IP/域名 |
| 6 | 前端开发白名单 | **P0-必须** | 修改配置 | 开发人员本地 IP |
| 7 | 物种→文件名映射 | **P0-必须** | 修改代码配置 | 确认新实验室的 CSV 文件名 |
| 8 | 历史数据清理 | **P0-必须** | 删除文件 | 无（操作即可） |
| 9 | 仪器通道映射 | **P1-视情况** | 替换文件 | 新仪器的通道配置 |
| 10 | 光谱数据 | **P1-视情况** | 替换文件 | 新仪器的光谱数据 |
| 11 | 荧光素亮度评分 | **P2-可选** | 调整数值 | 仪器实测亮度数据 |
| 12 | CSV 列名映射 | **P1-视情况** | 修改代码 | 新实验室 CSV 的列结构 |
| 13 | Docker 端口 | **P2-视情况** | 修改配置 | 新服务器的端口占用情况 |
| 14 | Nginx 网关域名 | **P2-视情况** | 修改配置 | 新部署域名/路径 |
| 15 | LLM 语言偏好 | **P2-视情况** | 修改代码 | 新实验室语种需求 |
| 16 | 物种标记列表 | **P2-视情况** | 修改代码 | 研究非常规物种时需要 |
| 17 | 活力染料文件 | **P1-视情况** | 替换文件 | 新实验室使用的活力染料 |
| 18 | Isotype/Others 文件 | **P2-可选** | 替换文件 | 新实验室的同型对照数据 |

---

## 3. 逐项操作说明

### 3.1 抗体库存 CSV 替换

**优先级：** P0-必须

**涉及的路径与文件：**

```
inventory/
├── 流式抗体库-20250625-人.csv     ← 替换为新实验室人源抗体库
├── 流式抗体库-20250625小鼠.csv    ← 替换为新实验室鼠源抗体库
├── viability_dyes.csv            ← 替换为新实验室活力染料（可选）
├── Isotype.csv                    ← 替换为新实验室同型对照（可选）
├── Others.csv                     ← 替换为新实验室其他试剂（可选）
├── Flourence_List.csv             ← 可沿用
├── impossible_inventory.csv        ← 视情况修改/清空
└── panel_inventory.csv             ← 可清空重建
```

**CSV 文件期望格式：**

库存 CSV 必须包含以下列（列名可不一样，见第 3.10 节）：

```
Fluorescein,Target,Species,Clone,Catalog Number,Brand,Quantity
APC,CD3,Human,SK7,344822,BioLegend,5
FITC,CD4,Human,RPA-T4,300538,BioLegend,3
```

> **注意：** CSV 编码可能为 GBK/GB18030（中文 Windows 导出），系统会自动尝试 utf-8 → gbk → gb18030 → latin1 编码回退。

**AI Agent 操作步骤：**

```bash
# 1. 确认新实验室提供了哪些 CSV 文件
ls -la inventory/*.csv

# 2. 检查新 CSV 的列名
head -1 inventory/新文件名.csv

# 3. 检查列名是否与现有的 column_mapping 匹配（详见第 3.10 节）
#    如果列名不一样，需要修改 data_preprocessing.py 中的 column_mapping
```

---

### 3.2 管理员密码设置

**优先级：** P0-必须

**涉及文件：** `docker-compose.yml`

```yaml
environment:
  ADMIN_PASSWORD: "请更改为新密码"   # ← 必须更改
```

**要求：**
- 至少 8 个字符
- 包含大小写字母和数字
- 不要使用常见密码

**AI Agent 操作：**

```bash
# 1. 确认当前值（不应直接读取明文密码）
grep ADMIN_PASSWORD docker-compose.yml

# 2. 提示用户输入新密码并替换
```

---

### 3.3 会话签名密钥设置

**优先级：** P0-必须

**涉及文件：** `docker-compose.yml`

```yaml
environment:
  ADMIN_SESSION_SECRET: "panelagent-docker-session-secret-2024"  # ← 建议更改
```

**要求：**
- 至少 32 个字符的随机字符串
- 如果留空，系统会在启动时自动生成一个随机密钥

**AI Agent 操作：**

```bash
# 生成随机密钥
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 3.4 AI API Key 配置

**优先级：** P0-必须

**涉及文件：** `.env`（项目根目录）

```ini
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL_NAME=gpt-4o
```

**两种配置方式：**

| 方式 | 说明 | 优点 |
|------|------|------|
| **A) 环境变量** | 在 `.env` 中填写 | 一次配置，所有服务生效 |
| **B) 运行时设置** | 在管理后台 → 设置页面填写 | 无需重启，动态切换 |

**推荐策略：** `.env` 中填写默认值，同时允许管理员在 UI 上覆盖。

**支持的 API 端点（OpenAI 兼容）：**

| 类型 | 示例 Base URL |
|------|---------------|
| OpenAI 官方 | `https://api.openai.com/v1` |
| Azure OpenAI | `https://xxx.openai.azure.com/` |
| 本地 LLM（Ollama） | `http://localhost:11434/v1` |
| 本地 LLM（LM Studio） | `http://127.0.0.1:1234/v1` |
| 第三方代理 | `https://aihubmix.com/v1` |

---

### 3.5 CORS 白名单配置

**优先级：** P0-必须

**涉及文件：** `docker-compose.yml`

```yaml
environment:
  BACKEND_CORS_ORIGINS: "http://localhost:3000,http://localhost:3001,http://192.168.1.100:3000,http://192.168.1.105:3000"
```

**需要添加的地址：**

| 服务 | 本地地址 | 生产地址（按需） |
|------|----------|------------------|
| User Frontend | `http://localhost:3000` | `https://your-domain.com` |
| Admin Frontend | `http://localhost:3001` | `https://admin.your-domain.com` |
| Gateway | `http://localhost:8080` | `https://your-domain.com` |
| 开发机 IP | `http://192.168.x.x:3000` | — |

> **注意：** `localhost` 和实际 IP 地址是**不同的 origin**，需要都加上。

---

### 3.6 前端开发白名单配置

**优先级：** P0-必须（仅开发模式需要）

**涉及文件：** `frontend/.env.local`

```ini
ALLOWED_DEV_ORIGINS=localhost,127.0.0.1,192.168.1.100,192.168.1.101,192.168.1.105
```

添加所有开发人员的机器 IP 地址，用于 Next.js HMR WebSocket 连接验证。

---

### 3.7 物种→文件名映射确认

**优先级：** P0-必须

**涉及文件：** `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ...
    SPECIES_INVENTORY_MAP: dict[str, str] = {
        "Mouse": "流式抗体库-20250625小鼠.csv",     # ← 确认文件名与实际一致
        "Human": "流式抗体库-20250625-人.csv",      # ← 确认文件名与实际一致
    }
```

**AI Agent 操作：**

```python
# 检查逻辑：确认 inventory/ 目录中的 CSV 文件名与映射一致
import os
inventory_dir = "inventory"
actual_files = set(os.listdir(inventory_dir))
expected_files = {"流式抗体库-20250625-人.csv", "流式抗体库-20250625小鼠.csv"}
missing = expected_files - actual_files
if missing:
    print(f"缺少文件: {missing}")
    print("请在 config.py 中更新 SPECIES_INVENTORY_MAP 映射")
```

---

### 3.8 历史数据清理

**优先级：** P0-必须

**需要删除/清空的路径：**

```
# 【必须删除】SQLite 数据库（含 LLM 设置 + panel 历史）
data/admin_console.sqlite3

# 【必须清空】质量登记问题记录
data/quality_registry/issues.json        → 清空为 {"issues": []} 或 {"records": []}

# 【必须清空】质量审计日志
data/quality_registry/audit/             → 删除目录下所有 .json 文件

# 【必须清空】质量投影缓存
data/quality_registry/projections/       → 删除目录下所有 .json 文件
```

**AI Agent 操作：**

```bash
# 删除 SQLite 数据库
rm -f data/admin_console.sqlite3

# 清空质量问题记录（保留文件，重置内容）
echo '{"issues": []}' > data/quality_registry/issues.json

# 清空审计日志目录
rm -f data/quality_registry/audit/*.json

# 清空投影缓存目录
rm -f data/quality_registry/projections/*.json
```

> **注意：** 系统首次启动时会自动重新创建 `admin_console.sqlite3` 及其表结构，无需手动初始化。

---

### 3.9 仪器通道映射适配（视情况）

**优先级：** P1-视情况而定

**何时不需要修改：**
- 新实验室使用**同型号流式细胞仪**（激光/检测器配置相同）
- 或同为传统多激光配置（蓝 488nm + 黄/绿 561nm + 红 640nm + 紫 405nm）

**何时需要修改：**

| 场景 | 需要改的文件 | 说明 |
|------|-------------|------|
| 改用**光谱流式细胞仪**（如 Cytek Aurora） | `channel_mapping.json` | 通道命名完全不同（如 `B1_525nm`, `V1_450nm`） |
| 改用**不同品牌仪器** | `channel_mapping.json` | 如从 CytoFLEX 换到 LSRFortessa，通道命名不同 |
| 使用**不同激光/检测器配置** | `channel_mapping.json` | 如从 3 激光升级到 5 激光 |
| 仅换同品牌新型号 | `channel_mapping.json` | 可能只新增几个通道，现有映射可沿用 |

**涉及文件：**

| 文件 | 结构示例 |
|------|----------|
| `channel_mapping.json` | `{"FITC": "B1_FITC", "PE": "Y1_PE", ...}` |
| `spectral_data.json` | `{"FITC": {"peak": 519, "sigma": 15, "color": "#00FF00", "category": "Blue Laser"}, ...}` |
| `fluorochrome_brightness.json` | `{"PE": 5, "FITC": 3, ...}` |

**AI Agent 操作：**

```bash
# 1. 获取新仪器的通道信息，询问用户通道映射表
# 2. 根据新映射重建 channel_mapping.json
# 3. 如果使用新荧光素，补充 spectral_data.json
# 4. 如果新仪器的荧光素亮度不同，调整 fluorochrome_brightness.json
```

---

### 3.10 库存 CSV 列名映射（视情况）

**优先级：** P1-视情况

**当前代码期望的列名（`data_preprocessing.py` 中硬编码）：**

```python
COLUMN_EXPECTED = {
    "target": "Target",
    "fluorophore": "Fluorescein",
    "clone": "Clone",
    "catalog_number": "Catalog Number",
    "brand": "Brand",
    "quantity": "Quantity",
    "species": "Species",
}
```

**如果新实验室的 CSV 列名不同**（例如使用英文列名 `Fluorophore` 而非 `Fluorescein`），需要：

**方案 A：修改 `data_preprocessing.py` 中的 `column_mapping` 逻辑**

在 `load_antibody_data()` 函数中，找到或添加 `column_mapping` 参数：

```python
column_mapping = {
    'Antigen': 'Target',          # 新列名 → 标准列名
    'Fluorophore': 'Fluorescein',  # 新列名 → 标准列名
    'Clone #': 'Clone',           # 新列名 → 标准列名
}
```

**方案 B：让新实验室调整 CSV 列名以匹配现有格式（推荐）**

---

### 3.11 Docker 部署参数（视情况）

**优先级：** P2-视情况

**涉及文件：** `docker-compose.yml`

可能需修改的参数：

```yaml
services:
  backend:
    ports:
      - "8000:8000"              # 左边端口可能被占用
  frontend:
    ports:
      - "3000:3000"              # 左边端口可能被占用
  admin-frontend:
    ports:
      - "3001:3000"              # 左边端口可能被占用
  gateway:
    ports:
      - "8080:80"                # NGINX 对外端口
```

**涉及文件：** `gateway/nginx.conf`

可能需修改的参数：

```nginx
server_name _;                  # 可改为具体域名
```

---

### 3.12 语言偏好设置（视情况）

**优先级：** P2-视情况

**涉及文件：** `llm_api_client.py`

```python
system_prompt = "你是一个流式细胞术专家，请以 JSON 格式输出。所有文本内容请使用中文回答。"
```

如果新实验室需要英文：

```python
system_prompt = "You are a flow cytometry expert. Please output in JSON format. Respond in English."
```

> 同时，前端页面（`frontend/` 和 `admin-frontend/` 中所有 `tsx` 文件）的中文 UI 文字也需要翻译。

---

## 4. 可沿用的部分清单

以下组件/数据在新实验室**可以直接沿用，无需修改**：

### 物理化学数据（跨实验室通用）

| 文件 | 说明 |
|------|------|
| `spectral_data.json` | 荧光素光谱特性由分子结构决定，全球一致 |
| `fluorochrome_brightness.json` | 荧光素的相对亮度是已知物理量（PE 比 FITC 亮） |

### 算法与业务逻辑代码（跨实验室通用）

| 路径 | 说明 |
|------|------|
| `panel_generator.py` | 面板生成算法 |
| `data_preprocessing.py` | 数据预处理逻辑（除 column_mapping 外） |
| `llm_api_client.py` | LLM 客户端（除 system prompt 外） |

### 后端服务代码

| 路径 | 说明 |
|------|------|
| `backend/app/core/config.py` | 配置类（除 SPECIES_INVENTORY_MAP 外） |
| `backend/app/services/*.py` | 所有服务层代码 |
| `backend/app/schemas/*.py` | 所有 Pydantic schema |
| `backend/app/api/v1/endpoints/*.py` | 所有 API 端点 |

### 前端代码

| 路径 | 说明 |
|------|------|
| `frontend/` 全部 | UI 逻辑完全通用 |
| `admin-frontend/` 全部 | 管理界面完全通用 |

### 基础设施配置（需改参数，不改结构）

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | 架构模式可复用，只改参数值 |
| `gateway/nginx.conf` | 路由规则可复用，只改域名/端口 |
| `Dockerfile.backend` | 构建文件，无需修改 |
| `Dockerfile.frontend` | 构建文件，无需修改 |
| `Makefile` | 开发命令，无需修改 |

---

## 5. 迁移验证清单

完成所有迁移步骤后，按顺序验证以下内容：

### 5.1 启动前检查

```bash
# 验证所有必须文件存在
echo "=== 文件完整性检查 ==="
ls -la inventory/*.csv               # 应有新实验室的抗体库文件
cat .env | grep -v "KEY\|SECRET"     # 确认 .env 存在且格式正确

# 验证通道映射文件格式合法
python -c "import json; json.load(open('channel_mapping.json'))" && echo "channel_mapping OK"
python -c "import json; json.load(open('spectral_data.json'))" && echo "spectral_data OK"
python -c "import json; json.load(open('fluorochrome_brightness.json'))" && echo "brightness OK"

# 确认历史数据已清理
ls data/admin_console.sqlite3 2>/dev/null && echo "⚠ 警告：SQLite 数据库仍然存在" || echo "✓ SQLite 已清理"
ls data/quality_registry/audit/*.json 2>/dev/null && echo "⚠ 警告：审计日志未清理" || echo "✓ 审计日志已清理"
```

### 5.2 启动验证

```bash
# 方式一：Docker 部署
docker compose build     # 构建镜像
docker compose up -d     # 启动服务
docker compose ps        # 确认所有容器正常运行

# 方式二：本地开发
make dev-all
```

### 5.3 API 功能验证

```bash
# 1. 健康检查
curl http://localhost:8000/api/v1/health
# 预期: {"status": "ok"}

# 2. 检查 API Key 配置（管理后台设置页面）：
# 访问 http://localhost:3001/settings
# 确认 API Key 状态显示"已配置"

# 3. 登录管理后台
# 访问 http://localhost:3001/login
# 使用第 3.2 节设置的管理员密码登录

# 4. 测试面板生成（人源）
curl -X POST http://localhost:8000/api/v1/panels/generate \
  -H "Content-Type: application/json" \
  -d '{"species": "Human", "markers": ["CD3", "CD4", "CD8"]}'
# 预期: 返回 JSON 格式 panel 建议

# 5. 测试面板生成（鼠源）
curl -X POST http://localhost:8000/api/v1/panels/generate \
  -H "Content-Type: application/json" \
  -d '{"species": "Mouse", "markers": ["CD3", "CD4", "CD8"]}'
# 预期: 返回 JSON 格式 panel 建议
```

### 5.4 前端功能验证

| 测试项 | 路径 | 预期结果 |
|--------|------|----------|
| 用户首页 | `http://localhost:3000` | 页面正常渲染 |
| Panel 设计 | `http://localhost:3000/panel-design` | 可选择人/鼠物种 |
| 实验设计 | `http://localhost:3000/exp-design` | 可输入自然语言描述 |
| 设置页面 | `http://localhost:3001/settings` | 可修改 LLM 配置并保存 |
| 管理员登录 | `http://localhost:3001/login` | 用新密码登录成功 |

---

## 6. 附录：关键文件索引

### 项目根目录

| 文件 | 用途 | 迁移操作 |
|------|------|----------|
| `.env` | 环境变量（API Key, Base, Model） | 修改 |
| `docker-compose.yml` | Docker 编排配置 | 参数修改 |
| `channel_mapping.json` | 荧光素→仪器通道映射 | 视情况替换 |
| `spectral_data.json` | 荧光素光谱数据 | 视情况替换/增补 |
| `fluorochrome_brightness.json` | 荧光素亮度评分 | 视情况调整 |

### inventory/ 目录

| 文件 | 用途 | 迁移操作 |
|------|------|----------|
| `*.csv`（人源抗体库） | 人源库存 | 替换 |
| `*.csv`（鼠源抗体库） | 鼠源库存 | 替换 |
| `viability_dyes.csv` | 活力染料 | 替换（如使用不同染料） |
| `Isotype.csv` | 同型对照 | 替换（可选） |
| `Others.csv` | 其他试剂 | 替换（可选） |

### data/ 目录

| 路径 | 用途 | 迁移操作 |
|------|------|----------|
| `data/admin_console.sqlite3` | LLM 设置 + Panel 历史 | **删除**（系统重建） |
| `data/quality_registry/issues.json` | 质量问题记录 | **清空** |
| `data/quality_registry/audit/` | 审计日志 | **清空** |
| `data/quality_registry/projections/` | 质量投影缓存 | **清空** |
| `data/cytoflex_s_fluorochrome_mapping.csv` | 参考文档 | 可替换 |

### backend/ 目录（需修改的）

| 文件 | 用途 | 迁移操作 |
|------|------|----------|
| `backend/app/core/config.py` 中的 `SPECIES_INVENTORY_MAP` | 物种→CSV 文件映射 | 确认文件名一致 |

### 前端配置

| 文件 | 用途 | 迁移操作 |
|------|------|----------|
| `frontend/.env.local` 中的 `ALLOWED_DEV_ORIGINS` | HMR 白名单 | 添加开发人员 IP |
| `admin-frontend/.env.local` | 管理后台 API 地址 | 一般无需修改 |

---

## 附：AI Agent 快速启动命令

```bash
# 1. 检测当前项目状态
echo "=== 文件完整性 ==="
for f in channel_mapping.json spectral_data.json fluorochrome_brightness.json .env docker-compose.yml; do
  [ -f "$f" ] && echo "✓ $f" || echo "✗ $f 缺失"
done

echo ""
echo "=== 库存文件 ==="
ls -la inventory/*.csv 2>/dev/null || echo "inventory/ 中没有 CSV 文件"

echo ""
echo "=== 历史数据 ==="
[ -f data/admin_console.sqlite3 ] && echo "⚠ SQLite 数据库存在（需删除）" || echo "✓ 无遗留数据库"
find data/quality_registry -name "*.json" 2>/dev/null | wc -l | xargs -I{} echo "质量登记文件数: {}"

echo ""
echo "=== 配置检查 ==="
grep -n "SPECIES_INVENTORY_MAP" backend/app/core/config.py
grep -n "ADMIN_PASSWORD" docker-compose.yml
grep -n "BACKEND_CORS_ORIGINS" docker-compose.yml
```
