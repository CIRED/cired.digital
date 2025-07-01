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
