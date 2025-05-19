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

1. Prendre un snapshot.
2. Transférer le snapshot sur le VPS
3. Restaurer à partir du snapshot transféré.

On va écrire une paire de scripts snapshot,sh et restore.sh, qui tournent dans les deux environnements dev et prod.

On va ajouter une option --quick au script de validation.

### Script pour prendre un snapshot

Codes de sortie:

. 0 succès
. 1 aborted because the state of a running R2R seems invalid
. 2 error: R2R fails validity test after relaunch

Séquence:

1. Vérifier l'état du moteur `validate.sh --quick`, si up et invalide: exit 1
2. Arrêter `down.sh`
3. Archiver `tar -czvf $(VOLUMES_DIR)/archived/R2R/snapshot_$(date +%F).tar.gz $(VOLUMES_DIR)/active/R2R`
4. Relancer `up.sh`
5. Vérifier l'état du moteur `validate.sh  --quick`, si invalide: exit 2
6. exit 0

### Script pour restaurer

C'est avec un rollback intégré.
 
Codes de sortie:

. 0 Succès
. 1 Tarball pas trouvée
. 2 Tarball pas décompressée
. 3 Tarball contenu suspect invalide
. 4 Échec de mise à jour, rollback valide
. 5 Échec de mise à jour et du rollback

Séquence:
 
1. Faire une copie sauvegade de `$(VOLUMES_DIR)/active/R2R/` par sécurité.
2. Décompresser la tarball dans un répertoire temporaire. Exit 1. si pas trouvée, 2. si pas décompressée, 3. si contenu suspect.
3. Arrêter `down.sh`
4. Remplacer `$(VOLUMES_DIR)/active/R2R/` 
5. Relancer `up.sh`
6. Vérifier l'état du moteur `validate.sh  --quick`, si OK, exit 0 et nettoyage du répertoire temporaire
7. Sinon `down.sh` ,  restaurer à partir de la copie de sauvegarde, `up.sh`, 
8. Vérifier l'état du moteur `validate.sh  --quick`, si OK, exit 4 et nettoyage du répertoire temporaire, sinon exit 5.
