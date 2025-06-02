# Docker Operational Basics

Minh Ha-Duong | 2025-04-26

## Starting Docker Containers

### Single Container

This command pulls and starts a container:

```bash
docker run [options] <image-name>
```

Docker containers are isolated and do not inherit host environment variables automatically. Explicit configuration is required to pass environment variables (e.g., API keys) to the container.

### Multiple Containers with Docker Compose

Docker Compose is preferred for managing multiple containers simultaneously. Ensure a `compose.yaml` file exists that describes the services to be started.

```bash
docker compose up -d
```

The `-d` option runs containers in the background.

Note: The older `docker-compose` command is obsolete; prefer the newer `docker compose` integrated into Docker.

### Security Warning

Docker runs as root by default, posing security risks. Consider safer alternatives:

- Rootless Docker
- Podman
- Singularity/Apptainer

## Stopping and Cleaning Docker

### Stop All Running Containers

```bash
docker stop $(docker ps -aq)
```

Beware of any auto-restart options configured in Docker Compose.

### Remove All Containers (Running or Not)

Removing containers does not delete associated images or volumes; these persist separately.

```bash
docker rm $(docker ps -aq)
```

### Remove All Docker Images

Removed images will be automatically re-pulled by Docker if containers require them again.

```bash
docker rmi -f $(docker images -aq)
```

### Remove All Docker Volumes

Removing volumes permanently deletes stored data. Proceed with caution.

```bash
docker volume rm $(docker volume ls -q)
```

### Remove All Networks (excluding built-ins: bridge, host, none)

```bash
docker network rm $(docker network ls -q)
```

### Prune Docker (Remove unused data from the Docker environment)

This command removes all stopped containers, unused networks, and dangling images:

```bash
docker system prune
```

The `-a` option additionally removes unused images.

Warning: The `--volumes` option permanently deletes data from stopped or removed containers. Use with caution and ensure data is backed up before pruning.

## A Common Linux Network Issue

### Problem

Docker introduced `host.docker.internal` as a special DNS name in version 18.03 to simplify host-container networking. While seamless on Windows and Mac, Linux requires manual configuration due to network management differences.

### Solution

Edit `/etc/hosts` to manually map `host.docker.internal` to the localhost IP:

```bash
# For Docker
127.0.0.1 host.docker.internal
```

**Additional configuration (Docker Compose)**:
In `compose.full.yaml`, include:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

*(Works in Docker 20.10+)*

### Avoid These Bad Practices:

- Disabling Docker logging (ineffective for resolving network issues).
- Using `host` networking mode (reduces container isolation and lacks Docker Compose support).

---

## Verification Commands

Each verification step ensures your Docker environment and containers are correctly set up and functioning without issues.

### Check Running Containers

```bash
docker ps
```

Verify the container (e.g., `r2r-1`) status is marked `(healthy)` to confirm container health and proper initialization.

### Checking Logs

For a container named `r2r-1` running in a project named `docker`:

```bash
docker logs docker-r2r-1
```

Ensure no errors or critical warnings are reported. Standard practice is to send all logs to a centralized log manager.

### Health Check API

Many containers implement a health monitoring endpoint, making it a recommended practice to verify service availability:

```bash
curl http://localhost:7272/v3/health
# Expected response: {"results":{"response":"ok"}}
```

### App is Up Check

A typical app consists of a frontend connected to a backend through an API endpoint. For `r2r`, visit [http://localhost:7273](http://localhost:7273) to confirm the frontend is running. Also, check [http://localhost:7272](http://localhost:7272) to confirm backend availability, indicating successful deployment.
