# config/ — 宿主机统一配置目录

本目录是部署时唯一可调整的配置入口。所有配置**运行时不可写**，
修改后需重启 backend 容器生效：

```bash
docker compose restart backend
```

## 三个可调项

| 可调项 | 位置 | 说明 |
| --- | --- | --- |
| ① LLM 设置 | `config/.env` | 从 `.env.example` 复制并填写真实密钥 |
| ② 流式表 | `config/channel_mapping.json`<br>`config/fluorochrome_brightness.json`<br>`config/spectral_data.json` | 静态 JSON，容器内以只读挂载 |
| ③ 抗体问题表 | `config/quality_registry/` | `issues.json` 由运行时首次生成 |

## 使用方式

- 首次部署：`cp config/.env.example config/.env`，填写 `OPENAI_API_KEY`、
  `ADMIN_PASSWORD`、`ADMIN_SESSION_SECRET` 等。
- 确认 `config/` 下存在 3 个 JSON 文件（初始值已从仓库根目录复制）。
- 修改任意配置后重启 backend 容器生效。

> 注意：`config/.env` 包含密钥，已被 `.gitignore` 忽略，禁止提交。
