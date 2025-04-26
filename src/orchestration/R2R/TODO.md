# TODO for the R2R orchestration

## Abstract the Makefile

Model-specific scripts do the work, but the interface to
fetch, start, populate, test and stop are the same.
CLI is fine, there is no need for a clicky backend now.

## Try without the centralized logging service
- The light version does not use it
- Causes most bugs

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

