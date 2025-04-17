# R2R install notes

minh.ha-duong@cnrs.fr, 2025-04-12

I did a full installation with CLI on Linux using OpenAI key, no agentic search, logging disabled.

This note follows:
https://r2r-docs.sciphi.ai/self-hosting/installation/full

## Cleanup docker

### Stop running containers

```bash
docker stop $(docker ps -aq)
```

### Remove all containers, running or not

```bash
docker rm $(docker ps -aq)
```

### Remove all images

```bash
docker rmi -f $(docker images -aq)
```

### Remove all volumes

```bash
$ docker volume rm $(docker volume ls -q)
```

### Remove all networks except built-ins: bridge, host and none 

```bash
$ docker network rm $(docker network ls -q)
```

### Prune everything

```bash
docker system prune -a --volumes
```

## Clone the R2R repository

This will create the ./R2R directory

```bash
git clone https://github.com/SciPhi-AI/R2R.git

cd R2R/docker
```
## Setup the environment variables

Containers are isolated, so it won't inherit automatically the key value set in the environment variable.
It needs to be configured.

```bash
set | grep API_KEY
gedit env/r2r-full.env
```

The first command will display existing OPENAI_API_KEY=...
Paste the line in the r2r-full.env file.

Verify that R2R is configured to use OpenAI models. This is the default option.

```bash
$ grep R2R_CONFIG_NAME env/r2r-full.env 
R2R_CONFIG_NAME=full
```

Do nothing about Serper and Firecrawl.

## Start the R2R services

```bash
docker compose -f compose.full.yaml --profile postgres up -d
```

This is going to pull lots of images on the first time, including :

- unstructured
- graph_clustering
- hatchett

and it is going to fail because on Linux, Docker does not provide built-in DNS resolution for host.docker.internal

## Linux network issue

Starting with Docker 18.03, Docker introduced ```host.docker.internal```, a special DNS name that resolves to the host’s IP. This works well on Docker for Windows and Mac but isn’t natively supported on Linux.

Explanations:
<https://collabnix.com/how-to-reach-localhost-on-host-from-docker-container/>

The compose.full.yaml file has the line
``` 
extra_hosts:
      - "host.docker.internal:host-gateway"
```

This works in Docker 20.10 and later, but is not enough.
ChatGPT 4o surmises that the Docker daemon must initialize logging before configuring the extra_hosts. 

### Hacking /etc/hosts is the solution.

Add this line to /etc/hosts:
```
# For Docker
127.0.0.1	host.docker.internal
```

### Bad ideas:

- Disabling logging (not a real solution).
- Trying to use the ```host``` networking mode (this reduces the container’s isolation, works only on Linux and is not supported by docker compose.)

## Verify it works

```bash
docker ps
```

The r2r-1 container should shows as "(healthy)".
If it remains stuck at "(health: starting)", there is a problem.
The solution may be to ```sudo systemctl restart docker```, because I can't ```docker stop docker-r2r-1``` or ```docker kill docker-r2r-1``` effectively.

```bash
docker logs docker-r2r-1
```

Should not show problems.

```bash
curl http://localhost:7272/v3/health
# {"results":{"response":"ok"}}
```
<http://localhost:7273>

Should show the login screen or the docs screen.

## Stopping it

If

----

# The light version

Instructions at
<https://r2r-docs.sciphi.ai/self-hosting/installation/light>

```bash
uv venv r2r-env
uv pip install 'r2r[core]'
```

It needs a postgres+pgvector database to connect to. I don't have any.
