# TODO for the R2R orchestration


## Try without the centralized logging service
- The light version does not use it
- Causes most bugs

## docker network prune in  stop

## Use podman

## Deployment bugs

*hatchet engine is stuck on Starting on boot*.
Compose is configured to restart this service on-failure.
but it does not also restart its dependencies.
Solution: stop everything manually before starting.

*r2r container is stuck on stopping*. Solution: restart the whole docker service.

*compose complains that the volumes were created by another project*.
I changed project name in compose from the default "docker" to "myrag".
But there is no command to rename volumes.
Solution: Ignore the WARN messages and use the volumes as they are.

