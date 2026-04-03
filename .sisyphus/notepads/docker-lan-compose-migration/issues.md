# Docker LAN Compose Migration Issues

## T4: Frontend Dockerfile Issues
- Docker Hub registry unreachable (DNS timeout) — resolved via mirror docker.1ms.run
- Alpine apk repos unreachable (TLS error) — resolved by switching healthcheck to Node.js fetch
- No sudo password available — couldn't modify /etc/docker/daemon.json
- Image is 417MB without standalone output; could be ~100MB with standalone (requires next.config.ts change)
