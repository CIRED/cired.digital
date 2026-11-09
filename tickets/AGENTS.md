# tickets/

Local file-based tickets store for the project.

Agents should ensure the `erg` binary helper is available to manipulate tickets.
To get it: check `tickets/erg` (committed bootstrap binary, Linux x86-64 only).

As a fallback, agents can read/write directly using the example template:

```text
%erg 0.1
Title: Add retry logic for failed API requests
Created: 2026-05-04
Author: alice
Blocked-by: 0007

--- log ---
2026-05-04T09:00Z alice created
2026-05-04T14:22Z bob note Was blocked, 0007 now merged

--- body ---
## Context
The HTTP client silently drops requests when the upstream returns 503.
We need exponential backoff with jitter, capped at 3 retries.

## Exit criteria
- [ ] `client.Fetch()` retries up to 3 times on 5xx
- [ ] Backoff is 1s, 2s, 4s + random jitter less than 500ms
- [ ] Unit test covers retry exhaustion path
- [ ] `make check` passes
```

Rules agents must know:
- No `Status:` header in %erg 0.1 (use `erg migrate` for legacy files)
- Closed/not-closed is inferred from path conventions or a non-empty `Closed:` header
- `Label:` is optional and repeatable; accepted values are defined in `tickets/.ergrc` (defaults: `needs-human`, `deferred`)
- Log entries are append-only: `YYYY-MM-DDTHH:MMZ author verb detail`
- Ticket IDs are atomic 4-digit numbers -- never suffix them (`0134a`, `0134b`). To split a ticket, create new numbered tickets with descriptive slugs that cross-reference the parent in their body.
- A ticket's artifacts (reports, data, generated files, scripts) live in their natural place in the tree, referenced from the body by path: not embedded, not a `0002-slug.md` sidecar.
- Commit `tickets/.claims/NNNN` with ticket NNNN; a git conflict on it means the number is taken: renumber yours (`erg integration`).

On GitHub, `erg-github install` (a separate committed helper, not an `erg` subcommand) can add a `verify` check that fails a PR referencing a still-open ticket. Either way, close the ticket in the same PR (`erg close`).

Long-form conventions (ID claims, collision recovery, handoff-document sections) print on demand: `erg integration`. Project-specific lore -- CI job names, local scripts, past incidents -- goes in `tickets/LOCAL.md`, which erg never touches; this file it upgrades.

In doubt, run `erg spec` (file format) or `erg --help --all` / `erg COMMAND --help` for command documentation.
