# PanelAgent Docker Deployment Runbook

This document provides procedures for managing the Docker deployment of PanelAgent, including backup, validation, rollback, and cutover from tmux to Docker.

---

## 1. Quick Reference

| Service | Live (tmux) | Staging (Docker) | Status |
|---------|-------------|------------------|--------|
| Backend | `:8000` | `:18000` | Validating |
| Frontend | `:3000` | `:13000` | Validating |

**Compose file**: `docker-compose.yml`

**tmux session**: `panelagent` (left pane: backend, right pane: frontend)

---

## 2. Prerequisites

Before running any Docker operations, ensure:

1. **Docker and Docker Compose installed**:
   ```bash
   docker --version
   docker compose version
   ```

2. **Environment file exists at project root**:
   ```bash
   ls -la .env
   ```
   Must contain:
   - `OPENAI_API_BASE`
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL_NAME`

3. **Quality registry directory exists**:
   ```bash
   ls -la data/quality_registry/
   ```

4. **tmux session is running** (for rollback safety):
   ```bash
   tmux ls | grep panelagent
   ```

---

## 3. Starting the Docker Stack (Staging)

### 3.1 Build Images

```bash
# Build both frontend and backend images
docker compose build

# Or build with no cache (clean build)
docker compose build --no-cache
```

### 3.2 Start Services

```bash
# Start in detached mode
docker compose up -d

# View status
docker compose ps

# Stream logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
```

### 3.3 Verify Startup

```bash
# Check containers are running
docker compose ps

# Expected output:
# NAME                    IMAGE                           COMMAND                  SERVICE    CREATED         STATUS                   PORTS
# panelagent-backend      panelagent-backend              "uvicorn backend.app…"   backend    2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:18000->8000/tcp
# panelagent-frontend     panelagent-frontend             "npx next start -H 0…"   frontend   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:13000->3000/tcp
```

---

## 4. Validation Checklist

Before considering cutover, verify Docker matches tmux behavior.

### 4.1 Backend Health Check

```bash
# Docker backend (staging port)
curl -s http://127.0.0.1:18000/api/v1/health | jq

# Expected response:
# {
#   "status": "ok",
#   "version": "1.0.0"
# }

# Compare with tmux backend (live port)
curl -s http://127.0.0.1:8000/api/v1/health | jq
```

### 4.2 Frontend Health Check

```bash
# Docker frontend (staging port)
curl -sI http://127.0.0.1:13000

# Expected: HTTP/1.1 200 OK

# Compare with tmux frontend (live port)
curl -sI http://127.0.0.1:3000
```

### 4.3 API Proxy Through Frontend

```bash
# Test API proxy through Docker frontend
curl -s http://127.0.0.1:13000/api/v1/health | jq

# Should return same as direct backend access
```

### 4.4 Quality Registry Persistence

```bash
# Verify data directory is mounted
docker exec panelagent-backend ls -la /app/data/quality_registry/

# Check host data is visible in container
docker exec panelagent-backend cat /app/data/quality_registry/issues.json | head -20
```

### 4.5 tmux Coexistence Check

```bash
# Both should work simultaneously
echo "=== tmux backend ==="
curl -s http://127.0.0.1:8000/api/v1/health | jq -c
echo ""
echo "=== Docker backend ==="
curl -s http://127.0.0.1:18000/api/v1/health | jq -c
```

### 4.6 Full Validation Script

```bash
#!/bin/bash
echo "=== PanelAgent Docker Validation ==="
echo ""

# Backend health
echo "[1/4] Backend health (Docker :18000)..."
BACKEND_HEALTH=$(curl -s http://127.0.0.1:18000/api/v1/health)
if echo "$BACKEND_HEALTH" | grep -q '"status":"ok"'; then
    echo "  PASS: $BACKEND_HEALTH"
else
    echo "  FAIL: Backend not healthy"
    exit 1
fi

# Frontend health
echo "[2/4] Frontend health (Docker :13000)..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:13000)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "  PASS: Frontend returns 200"
else
    echo "  FAIL: Frontend returns $FRONTEND_STATUS"
    exit 1
fi

# API proxy
echo "[3/4] API proxy through frontend..."
PROXY_HEALTH=$(curl -s http://127.0.0.1:13000/api/v1/health)
if echo "$PROXY_HEALTH" | grep -q '"status":"ok"'; then
    echo "  PASS: API proxy working"
else
    echo "  FAIL: API proxy not working"
    exit 1
fi

# Quality registry
echo "[4/4] Quality registry persistence..."
if docker exec panelagent-backend test -f /app/data/quality_registry/issues.json; then
    echo "  PASS: Registry file accessible in container"
else
    echo "  FAIL: Registry file not found"
    exit 1
fi

echo ""
echo "=== All validation checks passed ==="
```

---

## 5. Backup Procedure

Always backup before cutover or major changes.

### 5.1 Backup Quality Registry

```bash
# Create timestamped backup
cp -r data/quality_registry data/quality_registry.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup exists
ls -la data/quality_registry.backup.*
```

### 5.2 Compressed Archive Backup

```bash
# Create compressed archive
tar czf /tmp/quality_registry_backup.$(date +%Y%m%d_%H%M%S).tar.gz data/quality_registry/

# Verify archive
tar tzf /tmp/quality_registry_backup.*.tar.gz | head -10
```

### 5.3 Docker Volume Backup (if using named volumes)

```bash
# Backup using temporary container
docker run --rm \
  -v panelagent_quality_registry:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/quality_registry_volume.$(date +%Y%m%d_%H%M%S).tar.gz -C /source .
```

### 5.4 Pre-Cutover Backup Checklist

```bash
# Run before ANY cutover attempt
echo "Creating pre-cutover backup..."
BACKUP_DIR="data/quality_registry.backup.$(date +%Y%m%d_%H%M%S)"
cp -r data/quality_registry "$BACKUP_DIR"
echo "Backup created at: $BACKUP_DIR"
echo ""
echo "Backup contents:"
ls -la "$BACKUP_DIR"
```

---

## 6. Rollback Procedure

If the Docker stack has issues, follow these steps to safely return to tmux-only operation.

### 6.1 Immediate Rollback Steps

```bash
# Step 1: Stop Docker stack
docker compose down

# Step 2: Verify Docker is stopped
docker compose ps

# Step 3: Check tmux backend is still responding
curl -s http://127.0.0.1:8000/api/v1/health | jq

# Step 4: Check tmux frontend is still responding
curl -sI http://127.0.0.1:3000 | head -1

# Step 5: Verify tmux session exists
tmux ls | grep panelagent
```

### 6.2 If tmux Backend Is Not Responding

```bash
# Attach to tmux session
tmux attach -t panelagent

# In the left pane (backend), restart:
# Ctrl+C to stop, then:
cd /home/user/PanChongshi/Repo/PanelAgent/backend
uvicorn app.main:app --reload --port 8000
```

### 6.3 If tmux Frontend Is Not Responding

```bash
# Attach to tmux session
tmux attach -t panelagent

# In the right pane (frontend), restart:
# Ctrl+C to stop, then:
cd /home/user/PanChongshi/Repo/PanelAgent/frontend
npm run dev
```

### 6.4 Rollback Verification

```bash
#!/bin/bash
echo "=== Rollback Verification ==="

# Verify Docker is down
if docker compose ps | grep -q "panelagent"; then
    echo "WARNING: Docker containers still running"
    echo "Run: docker compose down"
    exit 1
else
    echo "[OK] Docker stack is down"
fi

# Verify tmux backend
TMUX_BACKEND=$(curl -s http://127.0.0.1:8000/api/v1/health)
if echo "$TMUX_BACKEND" | grep -q '"status":"ok"'; then
    echo "[OK] tmux backend responding: $TMUX_BACKEND"
else
    echo "[FAIL] tmux backend not responding"
    exit 1
fi

# Verify tmux frontend
TMUX_FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000)
if [ "$TMUX_FRONTEND" = "200" ]; then
    echo "[OK] tmux frontend responding: HTTP $TMUX_FRONTEND"
else
    echo "[FAIL] tmux frontend not responding: HTTP $TMUX_FRONTEND"
    exit 1
fi

echo ""
echo "=== Rollback successful. System running on tmux. ==="
```

### 6.5 Emergency Full Rollback

If both Docker and tmux are broken:

```bash
# Step 1: Stop everything
docker compose down
tmux kill-session -t panelagent 2>/dev/null || true

# Step 2: Start fresh tmux session
tmux new-session -d -s panelagent -n "PanelAgent"

# Step 3: Start backend in left pane
tmux send-keys -t panelagent:0.0 "cd /home/user/PanChongshi/Repo/PanelAgent/backend && uvicorn app.main:app --reload --port 8000" Enter

# Step 4: Split window and start frontend in right pane
tmux split-window -h -t panelagent:0
tmux send-keys -t panelagent:0.1 "cd /home/user/PanChongshi/Repo/PanelAgent/frontend && npm run dev" Enter

# Step 5: Verify
echo "Waiting for services to start..."
sleep 5
curl -s http://127.0.0.1:8000/api/v1/health
curl -sI http://127.0.0.1:3000 | head -1
```

---

## 7. Cutover Procedure (Production Ports)

**WARNING**: Only execute this when Docker validation is complete and you are ready to switch production traffic from tmux to Docker.

### 7.1 Pre-Cutover Checklist

```bash
# [ ] Backup created
cp -r data/quality_registry data/quality_registry.backup.$(date +%Y%m%d_%H%M%S)

# [ ] Docker validation passed (all checks in section 4)
curl -s http://127.0.0.1:18000/api/v1/health | jq
curl -s http://127.0.0.1:13000/api/v1/health | jq

# [ ] No active users (coordinate downtime)
echo "Check who is using the system..."

# [ ] Team notified
echo "Notify team of cutover window"
```

### 7.2 Port Switching Steps

```bash
# Step 1: Stop Docker stack on staging ports
docker compose down

# Step 2: Edit docker-compose.yml to use production ports
# Change:
#   backend ports: "18000:8000" -> "8000:8000"
#   frontend ports: "13000:3000" -> "3000:3000"
sed -i 's/"18000:8000"/"8000:8000"/' docker-compose.yml
sed -i 's/"13000:3000"/"3000:3000"/' docker-compose.yml

# Step 3: Stop tmux (port conflict prevention)
tmux kill-session -t panelagent

# Step 4: Start Docker on production ports
docker compose up -d

# Step 5: Verify on production ports
curl -s http://127.0.0.1:8000/api/v1/health | jq
curl -sI http://127.0.0.1:3000 | head -1
```

### 7.3 docker-compose.yml Port Mapping Reference

**Before cutover** (staging):
```yaml
services:
  backend:
    ports:
      - "18000:8000"  # staging
  frontend:
    ports:
      - "13000:3000"  # staging
```

**After cutover** (production):
```yaml
services:
  backend:
    ports:
      - "8000:8000"   # production
  frontend:
    ports:
      - "3000:3000"   # production
```

### 7.4 Post-Cutover Verification

```bash
#!/bin/bash
echo "=== Post-Cutover Verification ==="

# Verify Docker on production ports
echo "[1/3] Checking Docker backend on :8000..."
if curl -s http://127.0.0.1:8000/api/v1/health | grep -q '"status":"ok"'; then
    echo "  PASS: Backend responding"
else
    echo "  FAIL: Backend not responding"
    exit 1
fi

echo "[2/3] Checking Docker frontend on :3000..."
if [ "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000)" = "200" ]; then
    echo "  PASS: Frontend responding"
else
    echo "  FAIL: Frontend not responding"
    exit 1
fi

echo "[3/3] Checking API proxy..."
if curl -s http://127.0.0.1:3000/api/v1/health | grep -q '"status":"ok"'; then
    echo "  PASS: API proxy working"
else
    echo "  FAIL: API proxy not working"
    exit 1
fi

echo ""
echo "=== Cutover complete. System running on Docker. ==="
```

### 7.5 Rollback After Cutover

If issues arise after cutover, immediately revert:

```bash
# Step 1: Stop Docker
docker compose down

# Step 2: Revert port changes
sed -i 's/"8000:8000"/"18000:8000"/' docker-compose.yml
sed -i 's/"3000:3000"/"13000:3000"/' docker-compose.yml

# Step 3: Start tmux
tmux new-session -d -s panelagent
tmux send-keys -t panelagent:0.0 "cd /home/user/PanChongshi/Repo/PanelAgent/backend && uvicorn app.main:app --reload --port 8000" Enter
tmux split-window -h -t panelagent:0
tmux send-keys -t panelagent:0.1 "cd /home/user/PanChongshi/Repo/PanelAgent/frontend && npm run dev" Enter

# Step 4: Verify tmux
curl -s http://127.0.0.1:8000/api/v1/health
curl -sI http://127.0.0.1:3000

echo "Rolled back to tmux. Docker ports restored to staging."
```

---

## 8. Common Issues and Troubleshooting

### 8.1 Backend Cannot Read .env File

**Symptom**: Backend fails to start, complaining about missing OpenAI API config.

**Diagnosis**:
```bash
# Check env_file is mounted
docker exec panelagent-backend env | grep OPENAI

# Check .env exists on host
ls -la .env
```

**Fix**:
```bash
# Verify docker-compose.yml env_file path
cat docker-compose.yml | grep -A2 "env_file"

# Should show:
# env_file:
#   - .env

# If .env is in different location, update the path
```

### 8.2 Frontend Cannot Reach Backend

**Symptom**: Frontend shows API errors, backend unreachable.

**Diagnosis**:
```bash
# Check BACKEND_INTERNAL_URL in container
docker exec panelagent-backend env | grep BACKEND
docker exec panelagent-frontend env | grep BACKEND

# Check backend health directly
curl http://127.0.0.1:18000/api/v1/health
```

**Fix**:
```bash
# In docker-compose.yml, ensure:
# frontend:
#   environment:
#     BACKEND_INTERNAL_URL: "http://backend:8000"

# Restart frontend after fixing
docker compose restart frontend
```

### 8.3 Quality Registry Data Lost

**Symptom**: Quality registry appears empty after container restart.

**Diagnosis**:
```bash
# Check volume mount
docker inspect panelagent-backend | jq '.[0].Mounts'

# Verify data exists on host
ls -la data/quality_registry/

# Check container sees the data
docker exec panelagent-backend ls -la /app/data/quality_registry/
```

**Fix**:
```bash
# Ensure docker-compose.yml has correct volume mount:
# volumes:
#   - ./data/quality_registry:/app/data/quality_registry

# If data was lost, restore from backup
cp -r data/quality_registry.backup.YYYYMMDD/* data/quality_registry/
```

### 8.4 Port Already in Use

**Symptom**: Docker fails to start with "port already in use" error.

**Diagnosis**:
```bash
# Check what is using the port
sudo lsof -i :18000
sudo lsof -i :13000

# Or use ss
ss -tlnp | grep -E '13000|18000'
```

**Cause**: tmux is still running on conflicting ports (3000/8000), or another Docker instance.

**Fix**:
```bash
# If Docker staging ports conflict, check for orphaned containers
docker ps -a | grep panelagent

# Remove orphaned containers
docker rm -f panelagent-backend panelagent-frontend

# Restart
docker compose up -d
```

**For production port conflicts (3000/8000)**:
```bash
# Check tmux is using ports
sudo lsof -i :8000
sudo lsof -i :3000

# Stop tmux before Docker cutover
tmux kill-session -t panelagent
```

### 8.5 Container Health Check Failing

**Symptom**: Container shows "unhealthy" in docker compose ps.

**Diagnosis**:
```bash
# View health check logs
docker inspect panelagent-backend | jq '.[0].State.Health'
docker inspect panelagent-frontend | jq '.[0].State.Health'

# Check if service is actually responding
curl -v http://127.0.0.1:18000/api/v1/health
```

**Fix**:
```bash
# Restart the service
docker compose restart backend

# Or rebuild if needed
docker compose down
docker compose up -d --build
```

### 8.6 Build Failures

**Symptom**: docker compose build fails.

**Diagnosis**:
```bash
# Build with verbose output
docker compose build --no-cache --progress=plain 2>&1 | tee build.log
```

**Common fixes**:
```bash
# Network issues - retry
docker compose build

# Cache issues - clean build
docker compose down
docker system prune -f
docker compose build --no-cache

# Check Docker daemon
docker info
```

### 8.7 CORS Errors After Cutover

**Symptom**: Browser blocks API requests after switching to production ports.

**Diagnosis**: Check browser console for CORS errors.

**Fix**: Update CORS origins in docker-compose.yml:
```yaml
backend:
  environment:
    BACKEND_CORS_ORIGINS: "http://localhost:3000,http://localhost:13000,http://192.168.1.100:3000"
```

---

## 9. Reference Commands

### Docker Compose

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# Rebuild and restart
docker compose up -d --build

# View logs
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend

# View status
docker compose ps

# Execute command in container
docker exec panelagent-backend python -c "import sys; print(sys.path)"
docker exec panelagent-frontend sh -c "env | grep BACKEND"

# Shell access
docker exec -it panelagent-backend bash
docker exec -it panelagent-frontend sh
```

### tmux Management

```bash
# List sessions
tmux ls

# Attach to panelagent
tmux attach -t panelagent

# Kill session
tmux kill-session -t panelagent

# Create new session
tmux new-session -d -s panelagent -n "PanelAgent"
tmux send-keys -t panelagent:0.0 "cd /home/user/PanChongshi/Repo/PanelAgent/backend && uvicorn app.main:app --reload --port 8000" Enter
tmux split-window -h -t panelagent:0
tmux send-keys -t panelagent:0.1 "cd /home/user/PanChongshi/Repo/PanelAgent/frontend && npm run dev" Enter
```

### Validation Shortcuts

```bash
# Quick health check
curl -s http://127.0.0.1:18000/api/v1/health | jq
curl -s http://127.0.0.1:8000/api/v1/health | jq

# Port availability
ss -tlnp | grep -E '3000|8000|13000|18000'

# Process check
ps aux | grep -E 'uvicorn|next'
```

---

## 10. Contact and Escalation

**Document Owner**: Infrastructure Team

**Last Updated**: 2026-04-03

**Review Schedule**: Before any deployment or cutover

---

*This runbook is a living document. Update it as procedures change or new issues are discovered.*
