# CIRED.digital Maintenance Procedures

## Monthly Core Tasks

### Security
- [X] *ssh admin@157.180.70.232*, *apt upgrade*, *reboot*, restart the docker stack
- [ ] Update Python/JS dependencies
- [ ] Review API keys & secrets rotation (TODO: Rotate and retransfer keys in secrets/env, it is 90 days since end of June)
- [ ] Run quick dependency vulnerability check
- [ ] Apply Docker updates

### System Health
- [X] Check VPS CPU, memory, disk usage through the Konsole at *https://console.hetzner.com/projects/10518741/servers/63277649/graphs*
- [X] Check VPS CPU, memory with  *htop*
- [X] Check VPS free disk   *df -h*
- [X] Verify Docker containers & service health  with *docker ps*
- [X] Scan logs for errors/warnings
```for container in $(docker ps --format "{{.Names}}"); do     echo "=== $container ===";     docker logs --since 1h "$container" 2>&1 | grep -i -E "(error|fail|exception|fatal)"; done
```

### Application Health
- [X] Run sample chatbot queries at *http://cired.digital*
- [ ] Check R2R search and LLM API connections

### Data Management
- [ ] Verify HAL API connectivity & response times
- [ ] Sync new HAL publications, update `data/prepared/`
- [ ] Validate sample metadata entries
- [ ] Archive previous data snapshot
- [ ] Verify indexing and check for duplicates

### Performance & Resources
- [ ] Review search/query performance briefly
- [ ] Clean temp files and prune old logs
- [ ] Prune unused Docker images

### Backups
- [ ] Snapshot `data/` and R2R database
- [ ] Archive system configs (without secrets)
- [ ] Test a quick restore from last snapshot

### Documentation & Communication
- [ ] Update maintenance log
- [ ] Note issues/actions/follow-up
- [ ] Share a short status with CIRED team

### Code Repository
- [ ] Clean up merged branches (`git branch --merged main`)
- [ ] Review stale feature branches (>30 days)
- [ ] Verify main branch is synced with origin
- [ ] Check for large files or repo bloat
