# How to deploy cired.digital R2R on Hetzner

HDM, 2025-06-03

This document explains manual deployment.

## Check that the VPS is up

1. Open the **Hetzner Console** at [https://console.hetzner.com/projects] and login.
2. Open the cired.digital Dashboard page.
3. Open the "Servers" resource.
4. Verify it is running: blinking green light next to the name.
5. Verify its Public IP is still 157.180.70.232

## Initial VPS configuration

This is a CPX21 instance: 8.46€ per month for 3vCPU, 4GB RAM, 80GB disk, no GPU.
The docker image is pre-installed.
No load test yet.
Can be rescaled to 4, 8 or 16 vCPU as long as it remains on the AMD architecture.


### Basic security: Never log as root

- Created the `admin` user and its home directory `/home/admin`
- Transferred the `admin` user's public key, so that SSH does not ask for password.
- Added `admin` to the `docker` group

### Install extra tools:

- Installed `pipx` with `sudo apt install pipx`
- Installed `uv` with `pipx install uv`
- Added `~/.local/bin` to the path with `pipx ensurepath`

## Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

### Basic security: Enable the firewall

```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 7273
sudo ufw deny 5432
sudo ufw enable
```

### Basic security: no defaults passwords

- Generate secrets with `pwgen -s 16 1`
- Change the default passwords in `secrets/env/*.env`.
- Chmod 600 the secret files


### Clone the cired.digital Git repo.
- `git clone https://github.com/MinhHaDuong/cired.digital.git`


## Automated Remote Deployment

1. `deploy/ops/deploy.sh --remote`     # Automated deployment to production

## Manual Remote Deployment (if needed)

1. `deploy/ops/up.sh --remote`         # Start services remotely
2. `deploy/ops/down.sh --remote`       # Stop services remotely
3. `deploy/ops/validate.sh --remote`   # Validate remotely

## Legacy Manual Process (deprecated)

1. ssh -t admin@157.180.70.232 bash     # Login to the VPS
2. cd cired.digital                     # Project directory
3. git pull                             # Update to latest version
4. deploy/ops/up.sh                     # Start the stack
5. deploy/ops/validate.sh               # Verify

## Manual smoketesting

1. open http://cired.digital:7273/auth/login.
2. login: the R2R server is at http://cired.digital:7272 (same host, port 7272).
3. Go to the Documents tab, click "+ New", add a document.
4. Wait and refresh the page untill you see Ingestion success and Extraction success.
5. Go to the Chat tab, choose the mode "Question and Answer", ask questions about the document.

Warning: R2R tends to display the login popup even when one is already logged in.

## Update the distant production data from local development data

1. Create the snapshot on the local development server: `deploy/ops/snapshot.sh`.
2. Push it to the VPS: `deploy/ops/push_snapshot.sh`.
3. Push the secrets to the VPS: `deploy/ops/push_secrets.sh`

## Go to the server
1. Login `ssh -t admin@157.180.70.232 bash`
2. Verify: secrets protection, everything at `ls -l secrets/env/` should be -rw-------
3. Verify the archive is there : `cd cired.digital && ls -lh data/archive/R2/`
4. Verify the space disk left: `df -h /` and verify there will be space for the tar
5. Update the code: `git pull`
6. Assume that the VPS (production server) can be stopped, nobody is connected: `cd deploy && ops/down.sh`
7. Run `ops/restore.sh`. It will show the archive name, so run it again with the argument.
8. Run `docker compose up --build` and inspect the logs

## Smoketesting
1. [http://cired.digital:7273/documents] should show the same as [http://localhost:7273/documents]
2. [http://cired.digital/] should show the same page as [http://localhost/]
3. Open Firefox's console (F12, Console tab) and verify for errors.
4. Complete the Onboarding procedure.

## Remote Execution Configuration

The deployment scripts now support remote execution via the `--remote` flag. Server configuration is managed in `deploy/ops/common_config.sh`:

- `REMOTE_USER`: SSH username (default: admin)
- `REMOTE_HOST`: Server IP address (default: 157.180.70.232)  
- `REMOTE_PROJECT_PATH`: Project path on server (default: /home/admin/cired.digital)

These can be overridden via environment variables if needed.

## Notes:

The scripts pair `snapshot.sh` / `restore.sh` are for both deployment and recovery.

All deployment scripts (`up.sh`, `down.sh`, `deploy.sh`) now support the `--remote` flag for automated remote execution via SSH.
