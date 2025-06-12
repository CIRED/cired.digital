# How to deploy cired.digital R2R on Hetzner

HDM, 2025-06-03

This document explains manual deployment.

## Check that the VPS is up

1. Go to [https://www.hetzner.com/cloud/].
2. Login in the `cloud` management portal.
3. Open (=click) the cired.digital Dashboard page.
4. Open (=click) the "Servers" resource.
5. See that it is running (blinking green light).
6. Note its Public IP is 157.180.70.232

## VPS configuration

This is a CPX21 instance: 3vCPU, 4GB RAM, 80GB disk
with the docker image pre-installed.
It costs 8.46€ per month.
No load test yet.

Never log as root:

- Created the `admin` user and its home directory `/home/admin`
- Transferred the `admin` user's public key, so that SSH does not ask for password.
- Added `admin` to the `docker` group

Install extra tools:

- Installed `pipx` with `sudo apt install pipx`
- Installed `uv` with `pipx install uv`
- Added `~/.local/bin` to the path with `pipx ensurepath`

Clone the cired.digital Git repo.
- `git clone https://github.com/MinhHaDuong/cired.digital.git`

Transfer secrets:

- Transfer the secrets file to `cired.digital/credentials/API_KEYS`
- Chmod 600 the secrets file

## Start R2R on the remote

1. ssh -t admin@157.180.70.232 bash         # Login to the VPS
2. cd cired.digital                         # Project directory
3. git pull                                 # Update to latest version
4. src/engine/ops/up.sh                     # Start the stack
5. src/engine/ops/validate.sh               # Verify

## Manual smoketesting

1. open http://cired.digital:7273/auth/login.
2. login: the R2R server is at http://cired.digital:7272 (same host, port 7272).
3. Go to the Documents tab, click "+ New", add a document.
4. Wait and refresh the page untill you see Ingestion success and Extraction success.
5. Go to the Chat tab, choose the mode "Question and Answer", ask questions about the document.

Warning: R2R tends to display the login popup even when one is already logged in.

## Update the distant production data from local development data

1. Run `snapshot.sh` on the local development server.
2. Transfer the snapshot to VPS. It is timestapped in cired.digital/data/archived/R2R/ .
3. Ensure that the VPS (production server) can be stopped, nobody is connected.
4. Run `restore.sh` on the VPS.

The scripts pair `snapshot.sh` / `restore.sh` can also be used for recovery.

Note: The `restore.sh` script does not inject the secret API_KEYS to the environment before calling docker compose. Warnings about these are normal.
