<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Admin Frontend

独立的管理后台 Next.js 应用，对应外部 URL `/admin` 前缀。

## 架构说明

- **无 basePath**: 外部 `/admin` 前缀由部署层的反向代理处理（path-based routing + prefix stripping）
- **独立应用**: 拥有独立的 package.json、依赖和构建流程
- **复用组件**: 使用与 frontend 相同的 shadcn/ui 组件库

## 开发

```bash
# 安装依赖
cd admin-frontend
npm install

# 开发服务器（端口 3001）
npm run dev -- --port 3001

# 构建
npm run build
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `BACKEND_INTERNAL_URL` | 后端 API 内部地址 |

## 路由

- `/` - 重定向到 /settings
- `/login` - 管理员登录
- `/settings` - 系统设置
- `/history` - 方案历史
- `/quality-registry` - 质量管理
