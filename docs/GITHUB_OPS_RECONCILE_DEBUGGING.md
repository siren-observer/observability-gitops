# Observability reconcile debugging

Use the service-backend [authoritative GitHub Actions to Kubernetes runbook](https://github.com/re8ch/service-backend/blob/main/docs/GITHUB_OPS_RECONCILE_DEBUGGING.md).

For `observability-metering-reconcile.yml`, record the selected release,
namespace, immutable accepted digest, OIDC audience and first failed job. Verify
the exact `ssa-state-<release>` read and the metering executor's namespace and
resource-name authorization before investigating apply or health observation.
Successful signature verification or extraction proves only those stages.

Do not restore local Flux, disable TLS validation, use local GitHub credentials,
rebuild an accepted artifact, or force shared SSA ownership. Dispatch through
the Re8ch Admin GitHub Governance service. A terminal-success run plus runtime
read-back matching accepted state is the completion condition.
