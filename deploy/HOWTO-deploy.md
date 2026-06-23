# How to deploy cired.digital R2R on Hetzner

HDM, 2025-07-01


## Initial VPS Setup

1. SSH into the server using the provided credentials, setup the admin user.
2. Transfer and run the `bootstrap.sh` script.
3. Follow post-execution instructions:
   - Log out and back in to apply Docker group membership.
   - Populate the secrets directory (`$HOME/secrets/env/`) with environment files.
   - Verify the `.env` file in the deploy directory pointing to the secrets.
   - Verify there is no compose override file in the deploy directory pointing.

### Write logs to a separate volume (optional)

The monitoring service writes logs to `/app/data/logs` in the container,
and compose.yaml maps this to the `../reports/monitor-logs` directory in the host filesystem. It is a good idea to store this directory on a separate volume because logs grow overtime untill they fill the root filesystem and break things.

1. Provision a 10GB ext4 formatted volume
2. Edit fstab to mount it at `/home/admin/cired.digital/reports/monitor-logs`
3. If already mounted somewhere else: detach it `sudo umount ...` and remount it with `sudo mount -a`.
4. Update the systemctl fstab cache with `sudo systemctl daemon-reexec`

## Automated Deployment

- Management scripts are in `deploy/ops/`
- They run locally by default in the dev environment.
- Use the `--remote` flag for automated remote execution.
- e.g. to deploy the application remotely:
   ```bash
   ./deploy.sh --remote
   ```
this will do a remote git pull, restart and validate.

## Manual Deployment (if needed)

1. Start services remotely:
   ```bash
   ./up.sh --remote
   ```
2. Stop services remotely:
   ```bash
   ./down.sh --remote
   ```
3. Validate remotely:
   ```bash
   ./validate.sh --remote
   ```

## Rotating secrets and API keys

Edit the relevant file in `secrets/env/` (e.g. `r2r-full.env`), push it, then
**recreate** the affected container:

```bash
./push_secrets.sh
./up.sh --remote          # recreates containers, re-reading env_file
```

- Write each secret as a real assignment: `OPENAI_API_KEY=sk-proj-...`. A bare
  value with no `VAR=` prefix leaves the variable undefined.
- **`docker restart` does NOT pick up a changed key.** It bounces the process
  with the environment baked in at container *creation*. Only `up.sh --remote`
  (i.e. `docker compose up -d --force-recreate <service>`) re-reads `env_file`.
- Verify the swap with a **novel** query, not a repeated one: R2R caches query
  embeddings, so a repeated query can return 200 from cache and hide a bad key.
  Confirm the loaded key without printing it:
  ```bash
  docker exec cidir2r-r2r-1 sh -c 'printf %s "$OPENAI_API_KEY" | tail -c 4'
  ```

## Backuping and updating the corpus Data

1. Create a snapshot locally:
   ```bash
   ./snapshot.sh
   ```
2. Push the snapshot to the VPS:
   ```bash
   ./push_snapshot.sh
   ```
3. Push secrets to the VPS:
   ```bash
   ./push_secrets.sh
   ```
## Backuping the monitoring data

1. The monitoring service writes application usage logs in a bind mount.
2. TODO: a FastAPI endpoint to zip and download it.
