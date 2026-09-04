# 配置与数据持久化

本页面说明 PanelAgent 的**配置来源**与**数据持久化**。改造后所有可调整项
统一放在宿主机 `config/` 目录，运行时不可写；数据（panel 历史、抗体问题表、
上传抗体库）通过 Docker 卷持久化，容器重建不丢失。

## 配置只有一个来源

宿主机 `config/` 目录是唯一配置入口。`config/.env` 中的密钥在 `.gitignore`
中排除，禁止提交。

### config/ 目录结构

```
config/
├── .env                     # 实际生效配置（从 .env.example 复制，含密钥，不入库）
├── .env.example             # LLM 设置模板
├── README.md                # 三个可调项说明
├── channel_mapping.json     # 流式表（只读挂载）
├── fluorochrome_brightness.json  # 流式表（只读挂载）
├── spectral_data.json       # 流式表（只读挂载）
└── quality_registry/        # 抗体问题表（issues.json 运行时首次生成）
```

三个可调项：

1. **LLM 设置**：`config/.env`（见下节完整变量表）。
2. **流式表**：`config/` 下 3 个 JSON，以只读（`:ro`）挂载进容器，容器内不可改。
3. **抗体问题表**：`config/quality_registry/`，挂载为可写目录，`issues.json` 由运行时首次生成。

## 完整 env 变量表（config/.env）

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `OPENAI_API_BASE` | OpenAI 兼容 API 端点 | `https://api.deepseek.com/v1` |
| `OPENAI_API_KEY` | LLM API 密钥 | `sk-xxxxxxxx` |
| `OPENAI_MODEL_NAME` | 模型名 | `deepseek-chat` |
| `ADMIN_PASSWORD` | 管理后台登录密码 | `change-me` |
| `ADMIN_SESSION_SECRET` | 会话签名密钥 | `change-me-session-secret` |
| `BACKEND_CORS_ORIGINS` | 允许的 CORS 来源（逗号分隔） | `http://localhost:3000,http://localhost:8088` |
| `HTTP_PROXY` | LLM 出口 HTTP 代理 | `http://172.18.0.1:7890` |
| `HTTPS_PROXY` | LLM 出口 HTTPS 代理 | `http://172.18.0.1:7890` |
| `NO_PROXY` | 绕过代理的地址 | `localhost,127.0.0.1,backend,frontend` |

## 首次部署初始化

1. 拷贝模板并填写密钥：
   ```bash
   cp config/.env.example config/.env
   # 编辑 config/.env，填写 OPENAI_API_KEY / ADMIN_PASSWORD / ADMIN_SESSION_SECRET 等
   ```
2. 确认 `config/` 下存在 3 个 JSON：
   `channel_mapping.json`、`fluorochrome_brightness.json`、`spectral_data.json`
   （初始值已从仓库根目录复制）。
3. `config/quality_registry/` 为空目录即可，`issues.json` 由运行时首次生成。

## 数据文件位置与备份

| 路径 | 内容 | 持久化方式 |
| --- | --- | --- |
| `data/admin_console.sqlite3` | panel 历史（panel_history） | 挂载卷 `./data` → `/app/data` |
| `data/quality_registry/` | 抗体问题表 | 挂载卷 `./config/quality_registry` → `/app/data/quality_registry` |
| `inventory/` | 上传的抗体库 | 挂载卷 `./inventory` → `/app/inventory` |

备份时复制宿主机上的 `data/` 与 `inventory/` 目录即可。panel 历史仍存储在
sqlite 中，仅通过挂载卷实现持久化，功能未改动。

## 修改配置后的生效方式

```bash
docker compose restart backend
```

LLM 设置已改为纯环境变量读取，后端不再写入数据库；重启后 UI 显示与
`config/.env` 完全一致，不再出现"信息打架"。
