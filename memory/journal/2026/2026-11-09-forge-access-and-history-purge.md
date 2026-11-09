# 2026-11-09: forge access restored, pre-rewrite history purged, housekeeping landed

## Context
The swarm session's housekeeping sweep (19:05 UTC) handed four items to this session: local main had diverged 36/36 from origin/main and still held the pre-rewrite history with client IPs; pushes from padme were refused; commit b433319 (tickets 0051 and 0052) was unpushed; Dependabot PRs #276 and #273 were open.

## Events
- Purge, with the author's approval: local main was moved to origin/main with `reset --keep` (the trees differed only by ticket commit d980e16), then `reflog expire --expire=now --all` and `gc --prune=now`. No other ref held the purged commits. Afterwards the oldest purged commit (631834d) was absent and the origin tip was present.
- Forge access: the agent gh config (`GH_CONFIG_DIR=~/.config/gh-agent`, a fine-grained PAT) got HTTPS 403 on push, although the API reported admin and push permissions. A web `gh auth login` by the author did not change the credential git uses. A dry-run push with the author's personal gh config succeeded. The author declined to fix the agent token and gave standing permission to use the personal login for this repository only.
- Merge method: `gh pr merge --merge` was refused ("Merge commits are not allowed"), although `allow_merge_commit` is true. The main branch ruleset includes `required_linear_history`, so the merges used `--rebase`.
- Landed: #286 (bookkeeping tier, ungated base, rebase), #276 (actions/setup-python v7) and #273 (actions/checkout v7). Each Dependabot PR got gaze REVIEWED and verify-gate APPROVED in round 1 after a Dependabot rebase.

## Outcome
Local main equals origin/main at ea08e18. Clones made before the history rewrite elsewhere still hold the old history; this purge covers padme's clone only.
