# RE8CH Observability GitOps

Private desired-state authority for RE8CH metrics, logs, alerts, and metering. Siren product source remains outside this repository.

The `observability-kube-state-metrics` ReleaseContract is the first static
executor migration. It binds the reviewed render to both the Helm chart digest
and the multi-architecture container image digest. Flux remains live until the
protected server-side dry-run and conflict takeover are recorded.

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
