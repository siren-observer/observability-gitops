# Observability GitOps agent context

## Start work

1. Begin from current `origin/main` in a task-specific worktree.
2. Read the parent Issue, delivery Issue, Project fields, and relevant contract.
3. Keep one Issue and concern per branch and worktree.
4. Use signed commits, a closing pull request, and successful checks.

## Delivery context

```text
Project → parent Issue → Issue → branch/worktree → commits → PR
        → checks → runtime evidence → Project status
```

- Give Project items type, status, lifecycle, dates, priority, risk, and context readiness.
- Use parent Issues and Milestones for outcomes and phases.
- Build each source revision and configuration once, then reuse its immutable digest.
- Run each CI class once for an unchanged revision.

## Authority

- `clusters/re8ch` is the production root.
- Observability domain and locked chart contracts are repository-owned.
- Siren product source remains product-owned.
- The bounded cloud SSA executor applies accepted immutable artifacts.
- Credentials and decrypted SOPS material stay in approved secret systems.

## Code and narrative

- Keep implementations small and comments focused on invariants, safety boundaries, and external contracts.
- Remove obsolete commentary while changing its owning path.
- Put Kubernetes output, experiments, incidents, and migration stories in Issues, Discussions, Wiki, or observability.
- Use `.github/PROJECT_CONTEXT_TEMPLATE.md` and `docs/RUNTIME-CONTEXT.md`.
