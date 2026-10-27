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
