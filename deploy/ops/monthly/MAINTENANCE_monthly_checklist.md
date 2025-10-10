# CIRED.digital Maintenance Procedures

## Monthly Core Tasks

### System Health
- [ ] Check VPS CPU, memory, disk usage
- [ ] Verify Docker containers & service health
- [ ] Scan logs for errors/warnings

### Application Health
- [ ] Verify HAL API connectivity & response times
- [ ] Check R2R search and LLM API connections
- [ ] Run sample chatbot queries

### Data Management
- [ ] Sync new HAL publications, update `data/prepared/`
- [ ] Validate sample metadata entries
- [ ] Archive previous data snapshot
- [ ] Verify indexing and check for duplicates

### Security
- [ ] Apply OS & Docker updates
- [ ] Update Python/JS dependencies
- [ ] Review API keys & secrets rotation (>90 days)
- [ ] Run quick dependency vulnerability check

### Performance & Resources
- [ ] Review search/query performance briefly
- [ ] Pull monitor logs to update the local copy
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
