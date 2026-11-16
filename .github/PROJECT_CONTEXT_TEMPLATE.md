# Project context template

Use one Project for a product, service, or governance domain.

## Hierarchy

```text
Project
├── parent Feature: outcome or historical phase
│   ├── Feature/Bug/Task: one reviewable concern
│   └── Feature/Bug/Task: one reviewable concern
└── parent Feature: next outcome or phase
```

Historical PRs are grouped by capability and phase. Parent Issues and Milestones express the evolution; `Others` holds evidence whose ownership remains unresolved.

## Fields

| Field | Values or purpose |
| --- | --- |
| Status | Todo, In Progress, Done |
| Type | Feature, Bug, Task |
| Lifecycle | Backlog, Ready, In Progress, Blocked, Done, Cancelled, Historical |
| Work Type | Feature, Bug, Task, Governance, Dependency, Documentation, Migration, Historical |
| Context Status | Draft, Ready, Complete, Historical |
| Priority / Risk | Local priority and operational exposure |
| Start / Target / Completed Date | Planned and verified chronology |

## Views

1. `List`: table with title, status, repository, type, parent, sub-issue progress, lifecycle, work type, context, and dates.
2. `Status`: board grouped by Status with context fields visible.
3. `Timeline`: roadmap using Start Date and Completed Date, with Target Date for active work.

## Delivery Issue

```markdown
## Outcome
<Observable result>

## Context
- Parent Issue: #
- Project: <link>
- Milestone: <phase>
- Branch/worktree: <name>

## Acceptance
- [ ] Static verification
- [ ] Runtime verification where applicable
- [ ] Evidence linked

## Evidence
<Checks, deployment status, sanitized runtime observation, Wiki or dashboard>
```
