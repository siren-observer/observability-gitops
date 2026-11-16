# Local observability context

- `AGENTS.md` is authoritative.
- GitHub Actions OIDC and the bounded cloud SSA executor own reconciliation;
  local Flux is retired.
- Follow `docs/GITHUB_OPS_RECONCILE_DEBUGGING.md` and distinguish selection,
  authorization, execution and observation failures.
- Preserve immutable digests and keep credentials out of Git and logs.
