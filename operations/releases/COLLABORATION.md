# Stalwart collaboration runtime activation

Tracking: https://github.com/siren-observer/observability-gitops/issues/50

This repository owns tenant-api deployment, module registration and self-service
routing. The chart now prepares two independent switches, both off by default:
`tenantPlatform.tenantAPI.collaboration.enabled` and `stalwartAdminEnabled`.
No user connection, tenant grant or management credential is created by this PR.

## Release evidence and prerequisites

The disabled runtime snapshot consumes the already published tenant image
`registry.re8ch.com/image/re8ch-tenant-mcp@sha256:52448f2e026c928579a3ecb986fe88ca279adb5e667881b384629e92de0112a0`.
It came from source `ee126a1dd398ab41e83b04f4aab6e4a773de1dde`, GitHub Actions
[41028840498](https://github.com/re8ch/service-backend/actions/runs/41028840498),
artifact `tenant-go-release-ee126a1dd398ab41e83b04f4aab6e4a773de1dde/tenant-mcp.image`.
It predates the isolation fix and MUST NOT be enabled with the new credential role.
Before enabling, consume the verified image from the merged namespace isolation
fix https://github.com/re8ch/service-backend/pull/2524 (or a descendant containing
it). Build only once per new source revision; reuse the existing published digest.

The Git-declared Stalwart v0.16.18 is not verified to support the required
scoped OAuthClient contract; the actual runtime version still requires authenticated
verification. OAuth readiness is tracked in
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
   via its reviewed Tenant grants, after provider readiness. Admin organization
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
roleRef: operator
lifecycle: Suspended
```

Do not add it to the Admin tenant. After readiness evidence, approve the
Consumable and change only this grant to `Active` in a signed PR. No service
instance provisioning class is implied: this capability binds an existing
provider account through user consent. The generic service-instance API is not
used. The application currently checks the active Tenant grant directly, so a
Draft Consumable by itself is not an enforcement gate; leaving the grant absent
or Suspended and `collaboration.enabled=false` is essential until validation.
