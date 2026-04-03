# Docker LAN Compose Migration Issues

## T4: Frontend Dockerfile Issues
- Docker Hub registry unreachable (DNS timeout) — resolved via mirror docker.1ms.run
- Alpine apk repos unreachable (TLS error) — resolved by switching healthcheck to Node.js fetch
- No sudo password available — couldn't modify /etc/docker/daemon.json
- Image is 417MB without standalone output; could be ~100MB with standalone (requires next.config.ts change)

## T6: End-to-End Parity Issues
- Test quality record (id=b48d3627-c9a2-48a6-95ac-3ce7f2847cb9, marker="test_docker_persistence") could not be deleted — API lacks DELETE endpoint for quality-registry issues
- README documents incorrect API routes (e.g., `/api/v1/quality-registry` vs actual `/api/v1/quality-registry/issues`)
