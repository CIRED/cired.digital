# SECURING.md for R2R

HDM, 2025-06-26


## Keeping the .env directory secret

- We create a `.env` file next to `compose.yaml` to set the `ENV_DIR` variable pointing to the `env/` directory. This will be automatically picked up by docker compose.

- The path to `env/` directory is `../../secrets/env` . That is in an dir named `secrets/`, sibling of the `cired.digital/` repository. Since `cired.digital/` is the GitHub project root, the `secrets/` dir is not shared. It must be snapshotted / backuped separately.

## Removing cleartext password from configuration file

- The personalized configuration file `user_configs/cidir2r.toml` contains "${R2R_ADMIN_PASSWORD}" instead of the clear text.
- The secret is defined in R2R's `env_file` along with all others
- We patch `scripts/start-r2r.sh` to do the interpolation (inject the secrets) at up time.

## Removing default passwords from environment files

Create strong passwords as necessary with: `openssl rand -hex 32`

### Set a R2R_SECRET_KEY in r2r-full.env

It is empty by default.
It is used to sign JWTs (JSON Web Token) and CSRF (Cross-Site Request Forgery) tokens.

### Remove the  NEXT_PUBLIC_R2R_DEFAULT_EMAIL and NEXT_PUBLIC_R2R_DEFAULT_PASSWORD from r2r-dashboard.env

In the Next.js web application framework, environment variables prefixed with `NEXT_PUBLIC_` are exposed to the client's browser.
The default credentials are *admin@example.com* and *change_me_immediately*.
They are used to bootstrap the admin user in R2R's dashboard.
If an admin has not been created, change them to something secret.
On first admin login, the system asks for a new password, and the value is not used again.
The two variables should be removed then.

### Replace MINIO_ROOT_PASSWORD in minio.env

Default value is *minioadmin* .
This is probably not used at the moment.

### Replace the weak default password: *hatchet_password*

It appears 3 times in env/hatchet.env: twice as an environment variables, once in the base URL.
It appears 2 times in scripts/create-hatchet-db.sh, both as fallbacks for missing env variables.

**But there is a smell**:
The environment variables used in create-hatchet-db.sh are not defined in hatchet.env:
- The env file defines DATABASE_POSTGRES_USERNAME and POSTGRES_USER, but the script uses HATCHET_POSTGRES_USER with fallback to hatchet_user
- The env file defines DATABASE_POSTGRES_PASSWORD and POSTGRES_PASSWORD, but the script uses HATCHET_POSTGRES_PASSWORD with fallback to hatchet_password
- The env file defines HATCHET_DATABASE_POSTGRES_DB_NAME and POSTGRES_DB=hatchet, but the script uses HATCHET_POSTGRES_DBNAME with fallback to hatchet

It does not looks okay to define POSTGRES_PASSWORD with different meanings both in hatchet.env and postgres.env.

We do not want password in a script.

**Fix**

Align the definitions in hatchet.env on the script:
- Change POSTGRES_DB to HATCHET_POSTGRES_DBNAME
- Change POSTGRES_USER to HATCHET_POSTGRES_USER
- Change POSTGRES_PASSWORD to HATCHET_POSTGRES_PASSWORD

Drop defaults from the script:
- Change ${HATCHET_POSTGRES_DBNAME:-hatchet} to a simple  ${HATCHET_POSTGRES_DBNAME}
- Same for ${HATCHET_POSTGRES_USER:-hatchet_user}
- Same for ${HATCHET_POSTGRES_PASSWORD:-hatchet_password}

### Replace weak default password *password* assigned to RABBITMQ_DEFAULT_PASS in hatchet.env

It appears twice: as an environemnt variable, and in the base URL.
This is Hatchet's task queue.

### Replace the weak default password *postgres*

It is assigned to POSTGRES_PASSWORD in postgres.env and to R2R_POSTGRES_PASSWORD in r2r-full.env.

### Replace the weak default Hatchet admin passwords.

When going to Hatchet's dashboard from R2R's dashboard, the defaults credentials are *admin@example.com* and *Admin123!!*.
Set something strong in hatchet.env:
```
HATCHET_ADMIN_EMAIL=<an_email>
HATCHET_ADMIN_PASSWORD=<a_strong_password>
```

### Verify

To surface any remaining literal secrets in env files or scripts, run these from the project's root:

```bash
grep -R --line-number -E '(_PASS(W?ORD)?|_SECRET|://[^:]+:[^@]+@)' ../secrets
grep -R --line-number -E '(_PASS(W?ORD)?|_SECRET|://[^:]+:[^@]+@)' deploy/
```

### Alternative with docker secret files.

Create a file secrets/postgres_password containing only the random string.
Reference it in compose.yaml:
```
    services:
      postgres:
        secrets:
          - source: postgres_password
            target: POSTGRES_PASSWORD
    secrets:
      postgres_password:
        file: ./secrets/postgres_password
```

## Re-build, re-run, verify
```
docker compose down          # stop old containers
docker compose pull          # grab any upstream fixes
docker compose up            # start with new secrets in place, watching the logs
```

**Postgres auth:**

docker compose exec postgres psql -U postgres -c '\conninfo'

**Hatchet gRPC health:**

grpcurl -plaintext hatchet-engine:7077 grpc.health.v1.Health/Check '{}'

**MinIO login**:

curl -u minioadmin:<newPw> http://localhost:9000/minio/health/ready

No authentication failures? You’re good.

## Firewall everything except 80 and 443

1. After SSHing into the server:

```bash
# Allow HTTP(S) and NPM Admin UI
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other incoming connections by default
sudo ufw default deny incoming

# Allow outgoing connections (needed for apt, certbot, DNS, etc.)
sudo ufw default allow outgoing

# Enable the firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

2. To access NPM configuration panel, open an SSH tunnel.

```bash
# From your local machine
ssh -L 8081:localhost:81 adminname@the-server-IP

# Then browse to http://localhost:8081
```

3. On the NPM configuration panel:

- r2r-api.cired.digital -> 7272
- r2r-dashboard.cired.digital -> 7273
- hatchet-dashboard.cired.digital -> 7274
- cirdi.cired.digital -> 8080
- cirdi-api.cired.digital -> 7277

4. Update the DNS zone file on Gandi so that all these point to the server IP

5. Use compose.override.yaml to open ports on localhost: for development

- Gitignore it so that it is not picked up in prod.
- Version a .template so that devs can conveniently make their own local copy.

## Hardening hints

- Pin images versions
- Keep all *.env and secrets/* in .gitignore and .dockerignore.
- Rotate DB, MinIO and RabbitMQ passwords on a schedule (30–90 days is typical).
- Enforce TLS everywhere once passwords are no longer default.
- Add --no-new-privileges:true and drop unnecessary Linux capabilities in your compose services for defence-in-depth.
- Some folders are mounted writable when RO would suffice
  - Allow the frontend process (nginx) to bind to priviledged port 80
  - Allow r2r and analytics processes to write to their bind mounted rw directories
