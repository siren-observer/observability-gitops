# Stalwart collaboration runtime activation

Tracking: https://github.com/siren-observer/observability-gitops/issues/50

This repository owns tenant-api deployment, module registration and self-service
routing. The chart now prepares three independent switches, all off by default:
`tenantPlatform.tenantAPI.collaboration.enabled`, `stalwartAdminEnabled`, and
`stalwartBootstrapEnabled`.
No user connection, tenant grant or management credential is created by this PR.

## Release evidence and prerequisites

The disabled runtime snapshot consumes the already published tenant image
`registry.re8ch.com/image/re8ch-tenant-mcp@sha256:7086e02a406465b3035895898d3112c65a4ac8b74db551c1521802518a9504ab`.
It came from source `dd5acdbec289082c5c5a561fcf68e797d484c9e8`, GitHub Actions
[41032678518](https://github.com/re8ch/service-backend/actions/runs/41032678518),
artifact `tenant-go-release-dd5acdbec289082c5c5a561fcf68e797d484c9e8/tenant-mcp.image`.
The release and finalized artifacts contain the same digest. The finalized
Sigstore bundle was independently verified with `cosign verify-blob-attestation`
using this digest, SHA-256, SLSA provenance v1, exact identity
`https://github.com/re8ch/service-backend/.github/workflows/tenant-go-release.yml@refs/heads/main`,
GitHub Actions OIDC issuer, and source SHA `dd5acdbec289082c5c5a561fcf68e797d484c9e8`:
`Verified OK`. It includes namespace isolation #2524, diagnostics #2525 and DAV
encoding #2526. The attested invocation is run 41032678518, attempt 1. No image
was rebuilt for this runtime change.

The Git-declared Stalwart v0.16.18 is not verified to support the required
scoped OAuthClient contract; authenticated runtime inspection also confirmed
v0.16.18. Provider migration/acceptance remains a separate gate. OAuth readiness is tracked in
https://github.com/8iops/agent-gitops/issues/39. A newer provider may require a
breaking database migration; this configuration does not authorize an in-place
upgrade or an unscoped OAuth fallback.

## Activation order

1. Record provider scoped-device OAuth verification, issued scope verification and
   nonproduction mail/calendar/files/revocation evidence. Set the fixed HTTPS
   `collaboration.origin`, registered `clientID`, and `validationRef` linking that
   evidence and the isolation image verification. A nonempty reference is a
   render-time completeness check, not cryptographic proof or automatic approval.
2. Platform bootstrap authority installs the reviewed `stalwart-credentials`
   Namespace and `tenant-api-stalwart-credentials` Role/RoleBinding rendered by
   `templates/collaboration.yaml`. The bounded runtime release executor deliberately
   cannot install RBAC or grant itself permissions. Its role is NOT broadened.
   The only Secret verbs are get/create/update/delete. There is no list/watch,
   patch, wildcard, or shared credential-broker write grant. Dynamic names preclude
   resourceNames on create; the namespace is the infrastructure boundary, with
   tenant/subject ownership additionally checked by tenant-api. Revoke old
   connections before moving an already enabled installation's credentials.
3. Grant `collaboration.stalwart.v1` only to the intended active application tenant
   via its reviewed Tenant grants, after provider readiness. The `Tenant` object is
   platform-bootstrap deferred in the bounded chart release, so read back the
   reviewed `Tenant/re8ch` spec through the platform path; a refreshed chart lock
   alone does not activate this grant. Admin organization
   membership is not an application tenant grant. Then merge the enabled values,
   refresh the locked chart snapshots, and deliver through the existing executor.
4. Verify running tenant-api imageID and environment via platform tools. Exercise
   self-service plan/consent/read/RSVP-preview/apply/revoke with nonproduction data,
   two subjects and two organizations. Verify cross-user references fail and
   revoked credentials cannot be used. Never log tokens or mail/file content.

## Management activation is separate

`stalwartAdminEnabled` publishes exactly `stalwart.admin.read`,
`stalwart.admin.plan`, and `stalwart.admin.apply` in the native backend allowlist.
The server and gateway retain platform administrator checks. Management service
Deployment ownership remains in re8ch/service-backend
`platform/cloud-platform/runtime.yaml`; do not duplicate it here.

Before enabling this switch, that owner must wire `STALWART_ADMIN_ORIGIN`, a
read-only dedicated token Secret through `STALWART_ADMIN_TOKEN_FILE`, and a
read-only ConfigMap of approved plans through `STALWART_APPROVED_PLANS_DIR`.
The approved-plan ConfigMap is written only by reviewed signed delivery; tenant-api
gets no write authority over it. Never reuse recovery administrator credentials.
Verify the existing cloud-platform release digest, one bounded read, non-admin
rejection, and an approved nonproduction description update before activation.
A successful source release or merged PR alone is not runtime evidence.

## Grant and Consumable authority

Both schemas and the `Tenant` rendering are owned by this repository's
`clusters/re8ch/charts/birfucate-metering` chart. `Tenant.spec.grants` allows
`Active` or `Suspended`; `Consumable.spec.lifecycle` allows `Draft`, `Approved`,
or `Suspended`. The included `collaboration-candidate.yaml` is a **Draft**
Consumable candidate, not imported by a Kustomization or release contract. Its
`Collaboration` access-contract type requires the chart's reviewed CRD enum
extension to be installed by platform bootstrap authority before creation.

The reviewed candidate to append to the chosen application's existing
`tenantPlatform.tenants[].grants` (preserving every other grant) is:

```yaml
name: collaboration-stalwart
consumableRef: collaboration.stalwart.v1
roleRef: viewer
lifecycle: Suspended
```

Do not add it to the Admin tenant. A viewer grant permits only personal
provider consent and owner-scoped collaboration data calls; infrastructure
operations retain their operator/admin gates. After readiness evidence, approve
the Consumable and change only this grant to `Active` in a signed PR. No service
instance provisioning class is implied: this capability binds an existing
provider account through user consent. The generic service-instance API is not
used. The application currently checks the active Tenant grant directly, so a
Draft Consumable by itself is not an enforcement gate; leaving the grant absent
or Suspended and `collaboration.enabled=false` is essential until validation.

## Read-only runtime evidence before this change

Authenticated platform audits confirmed tenant-api still runs digest
`7cfaa26752de996f30f4aacc1a955ca43c93a2c0800be5b3a9b3f0b0fc7ec2c8`, without
collaboration environment settings (`op_4fa9214239f3422abbe4f433b11b1d17`).
Cloud Platform still runs `779465757b402159dd8586d7707af8da114dfee44c56e3f40e88c4fb040ab943`
and has no management mounts (`op_12f3cc0d74c24fbb833a5c3c02a20d43`). Shared broker
Role is get-only (`op_49d2c54de50b417da115b1fa8914c3fa`). The dedicated admin
Secret and both management ConfigMaps are absent (`op_5a4b3afe7fe8414aa708ee3349d67ec1`,
`op_dc27d6240f714aa9b1c2ce238d340f45`). No credential values were read.

## Temporary bootstrap catalog publication

`stalwartBootstrapEnabled` publishes exactly `credentials.stalwart.ensure` and
`credentials.stalwart.authority.ensure`, separately
from the three steady-state management tools. Keep it false until the verified
Cloud Platform image containing service-backend #2531, the reviewed one-hour
authority seed/revoke implementation in service-backend #2533, and its reviewed
`STALWART_BOOTSTRAP_CONFIG`/bootstrap-token mounts exist. That source repository
owns the temporary mounts and their removal; no credentials are declared here.
The backend fails closed if configuration is missing. Use the platform operation's
plan/apply flow once the v1 provider is verified, then remove the temporary mount
and disable this catalog switch after provisioning. This switch does not publish
mailbox creation, arbitrary JMAP operations, or any tenant-facing tool.

The authority operation is platform-only and supplies the bootstrap credential
through a fixed server-side Secret path. Its seed/revoke plan cannot accept a
caller-supplied provider, identity, key, Secret destination or arbitrary native
method. Recovery credential bytes must remain server-side and never become the
runtime token. Complete verified provider migration and backup gates before any
seed; revoke the temporary key after dedicated management credential provisioning.
The default catalog remains unchanged until the existing bootstrap switch is
explicitly enabled in a later reviewed runtime change.
