# Tenant MCP image handoff

The active `flux-observability-system/birfucate-metering` HelmRelease takes
`tenantPlatform.tenantAPI.image` from the required `tenant-mcp-image` ConfigMap
in the same namespace. There is no inline image override.

The ConfigMap is owned by the existing signed service-backend Git source:
`re8ch/service-backend:clusters/re8ch/tenant-mcp-image/image.yaml`. That repository's
tenant Go release verifies the published image signature and uses the existing
domain-promoter App to propose one signed digest PR. Its Flux Kustomization
syncs the value; the ConfigMap's Flux watch label triggers Helm reconciliation.
An image update does not change this repository's chart source revision.

Merge prerequisite: service-backend PR #2332 must be merged and its
`flux-system/tenant-mcp-image` Kustomization Ready with the ConfigMap present.
The reference is intentionally required: absence must not deploy a chart default.
After activation, inspect the HelmRelease Ready condition and the tenant MCP
Deployment's image and rollout; a passed render check is not runtime evidence.

Rollback by reverting the digest in service-backend through a signed PR.
To retire the handoff, restore a verified explicit image and remove `valuesFrom`
in one reviewed change here before removing the producer ConfigMap.
