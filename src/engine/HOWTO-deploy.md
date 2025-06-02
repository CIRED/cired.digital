# How to deploy cired.digital R2R on Hetzner

HDM, 2025-05-14

The purpose of this document is to explain manual deployment, before scripting it.

## Check that the VPS is up

1. Go to https://www.hetzner.com/cloud/.
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

Transfer secrets:

- Created the directory `/home/admin/credentials`
- Transfered the secrets file to `credentials/API_KEYS`
- Chmod 600 the secrets file

## Start R2R on the remote

1. ssh -t admin@157.180.70.232 bash
2. cd cired.digital
3. git pull
4. cd src/orchestration/R2R
5. ./start.sh
6. ./validate.sh to perform automatic tests with

## Manual smoketesting

1. open http://157.180.70.232:7273/auth/login
2. login using the prod backend http://157.180.70.232:7273 and default identifiers admin@example.com / change_me_immediately
3. Go to the Documents tab, click "+ New", add a document.
4. Wait and refresh the page untill you see Ingestion success and Extraction success
5. Go to the Chat tab, choose the mode "Question and Answer", ask questions about the document

Warning: R2R tends to display the login popup even when one is already logged in.

## Update the distant production data from local development data

1. Run snapshot.sh on the local development server.
2. Transfer the snapshot to VPS. It is timestapped in cired.digital/data/archived/R2R/ .
3. Ensure that the VPS (production server) can be stopped, nobody is connected.
4. Run restore.sh on the VPS.

The scripts pair snapshot.sh / restore.sh can also be used for recovery.

Note:
The restore.sh script does not inject the secret API_KEYS to the environment before calling docker compose.
Warnings about these are normal.
