# RE8CH Observability GitOps

<!-- gitops-status:start -->
[![Reconcile](https://github.com/siren-observer/observability-gitops/actions/workflows/observability-metering-reconcile.yml/badge.svg?branch=main)](https://github.com/siren-observer/observability-gitops/actions/workflows/observability-metering-reconcile.yml?query=branch%3Amain)
[![Contract validation](https://github.com/siren-observer/observability-gitops/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/siren-observer/observability-gitops/actions/workflows/validate.yml?query=branch%3Amain)

These live badges show the latest workflow result on `main`, including scheduled
and manual runs. Reconcile runs can cover a single release; a passing badge is
not proof that every release is healthy or that SSA changed an object. Open the
run for its release scope, accepted digest, comparison, apply and health results.
The [domain observation Project](https://github.com/orgs/siren-observer/projects/1) retains release-level evidence;
receipt dispatch and governance checks do not replace runtime health verification.
Private workflow badges require repository access.
<!-- gitops-status:end -->

Private desired-state authority for RE8CH metrics, logs, alerts, and metering. Siren product source remains outside this repository.

## Local Flux prohibition

Local Flux writers are permanently retired and forbidden. Do not create,
restore, scale, restart, repair, proxy or authorize Source, Kustomize, Helm,
Notification, image automation, compatibility or domain Flux controllers.
Retained Flux APIs and manifests are historical/migration inputs only. GitHub
webhooks and Actions select reviewed immutable artifacts; the bounded cloud SSA
executor is the sole runtime writer and the only recovery path.

The `observability-kube-state-metrics` ReleaseContract is the first static
executor migration. It binds the reviewed render to both the Helm chart digest
and the multi-architecture container image digest. The bounded cloud SSA
executor owns delivery; no local Flux writer may be restored before, during or
after server-side dry-run and conflict takeover.

## Native domain cloud handoff

`python operations/releases/compile_domain.py` reuses the established SSA contract
and bundle validators to partition the production root by namespace. Generated
`contracts/*-domain-*.yaml` run through the existing `static-release` workflow.
`operations/releases/domain-access.yaml` is the exact reviewed access/state seed
for platform bootstrap; it is not included in this domain's runtime root.

The cohort report lists every source object, either in a publishable release or
with a specific remaining migration reason. Secret payloads and encrypted
configuration never enter public OCI bundles. Existing chart snapshot contracts
remain separate owners. Initial adoption permits only the exact reviewed object
inventory through `force_takeover=true`, after the previous writer is stopped.
Pruning is disabled during this first adoption; no migration deletes resources.

CI verifies deterministic outputs and compiles every generated contract. Actual
cloud adoption still requires the platform access seed and a successful release
run; generated bundles alone do not establish runtime ownership.

Role and RoleBinding desired objects remain platform-owned until admission can enforce their exact reviewed contents. Runtime groups receive no RBAC writes, bind, escalate or impersonate permission. Exact role names alone are not an escalation boundary.

## Remaining Helm runtime adoption

Four remaining Helm declarations have digest-locked runtime snapshots under
`releases/observability-chart-*`: IncidentRelay, OpenTelemetry operator,
VictoriaMetrics operator and the local Birfucate chart. Birfucate's cross-namespace
output is split into five contracts. The existing kube-state-metrics snapshot
remains a separate contract. `compile_chart_access.py` emits exact namespace
access in `chart-access.yaml`, with no RBAC writes or Secret access.

`lock_chart_runtimes.py` explicitly refreshes snapshots from pinned charts;
normal publish/reconcile uses those snapshots without downloading charts again.
Values, render bytes, local-chart contents and Helm declaration digests are
checked before release. Operator image pins retain the observed running image
IDs. The resolved tenant image input is an immutable digest with platform audit
reference. Updating that input requires a reviewed snapshot refresh.

CRDs, RBAC, webhook configurations, generated TLS Secrets and Helm hook Pods are
listed as platform-owned in `helm-cohort.json`; their current runtime objects are
retained. These snapshots do not claim to implement their lifecycle or upgrades.

Adoption contracts set `authorization.requireExisting=true`: the executor verifies the artifact, reads each exact object's resourceVersion and sends it as the SSA precondition. Missing objects and concurrent changes fail closed; adoption never silently recreates a deleted object. Ordinary release contracts without this flag retain creation behavior. One-shot Jobs are platform-owned and excluded from replay, and protected storage objects are excluded from force-conflict requests.

## Independent SSA and Observe actions

Reconcile reports SSA execution and runtime observation separately. The SSA step
validates authorization and the signed accepted artifact, performs server-side
dry-run and apply, then records `outcome: applied` and `acceptedDigest`. It does
not claim a healthy runtime. The following read-only Observe step publishes a
separate observation artifact and records healthy, degraded or unknown health.
Runtime health does not fail SSA, lock the release or trigger rollback. Signature,
authorization, field ownership and API write failures remain execution failures.
Legacy `healthyDigest` is only a fallback for older accepted records; new replay
authorization uses the explicitly accepted digest without inventing health proof.
