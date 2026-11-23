# Toolchain metrics and Sentry

This configuration reuses VMAgent `re8ch`, VMCluster `re8ch-metrics` tenant 0,
Grafana's existing `ds-prometheus` and `re8ch-vlogs` datasources, and the current
VictoriaLogs collector. It introduces no collector, metrics store, Sentry
datasource/API key or tracing identifier in metric labels.

## Signal contract

All components use `re8ch_toolchain_http_requests_total` and
`re8ch_toolchain_http_request_duration_seconds` with only component, environment,
phase, method, status_class, outcome and error_category. Outcome is success/error;
cancellation and panic are error categories. `re8ch_toolchain_build_info` carries
component/release/repository/environment. Dashboard queries join build identity
on the same job/instance, so release selection does not require request IDs or
release churn on every counter. Existing Core tool calls/duration are retained.

The dashboard UID is `re8ch-toolchain-sentry`. Choose a single component,
environment and release. Metric data links open the existing
`re8ch-studio/go-http` project (`4509349088985088`) with the same release,
environment, tool or phase, and time range. They are server-side measurements,
not proof a caller received a result.

Completion logs use camel-case traceId/operationId/sentryEventId/release/component/
environment. The logs panel parses structured JSON and retains the existing
fields, using the actual collector field `kubernetes.pod_namespace`. Native
VictoriaLogs derived fields link to Sentry traces, operation searches and event
searches. Empty fields are dropped so successful requests do not invent an error
event. Datasource provisioning escapes Grafana macros with `$$`; dashboard JSON
uses normal Grafana variables. Browser links use the viewer's Sentry session.

VM storage does not support exemplars. The unsupported exemplar-to-Jaeger setting
is removed. The unrelated existing Jaeger-compatible datasource remains intact;
none of these Sentry links pretend its store contains the SDK trace.

## Existing services and owners

- Core: existing `tenant-mcp-tool-usage`, Service tenant-infrastructure/tenant-api
  http 80 → runtime 19448. This scrape is not duplicated.
- Gateway: the same Service's catalog-mcp 19449, `/metrics` on the existing
  application listener. The public route only rewrites Exact
  `/tenant-native/mcp` to `/mcp`; it does not expose the metrics path.
- Cloud: ai-operations/re8ch-cloud-platform, named mcp port 19443, HTTP.
- Tenant control: tenant-infrastructure/tenant-control-controller, named http port
  80 → 19447. The application owns its metrics handler.
- Among hub: among-clusters/among-clusters-hub, named metrics port 9090.
- Among broker: credential-broker/among-clusters-credential-broker, named metrics
  port 9090. Among's new application version must expose the independent
  listener on its existing Service and permit only the reviewed VMAgent pods.
  Its public routes keep using HTTP 80 → 8080 and cannot route this listener.

Each new ServiceScrape has an exact namespace plus a service-name keep rule;
discovery of other Services never causes their endpoints to be scraped. The
existing managed=true selector admits these resources. Service/Pod IP changes
continue through Kubernetes endpoint discovery, without fixed Pod addresses.

## Reviewed delivery and acceptance

1. Deploy the reviewed application metrics implementations first. New SDK
   telemetry is not claimed to exist merely because old Core series are present.
2. Platform-bootstrap only the five reviewed new VMServiceScrape identities and
   their exact generated release access. The existing contracts require objects
   to exist and do not silently acquire create permission.
3. Apply the observability-system cohort's datasource/dashboard ConfigMaps before
   applying the Grafana cohort's template checksum. The checksum causes the
   normal existing Deployment rollout to load datasource provisioning. Preserve
   all other workload specs, PVCs, images, OAuth and organization settings.
4. Verify VMAgent's exact five new target groups plus the existing Core target are up;
   query build_info and new HTTP counters in VM storage for the actual deployed
   release; exercise real read-only tools. Confirm mounted dashboard/DS bytes and
   the actual Grafana dashboard's links resolve the selected labels/time.
5. Validate a real Sentry trace/error and operation link using the same completion
   log fields. Record source, signed digest, runtime generation and audit refs.
   Preserve missing-data/errors as failures, not successful configuration checks.

Before these changes, actual Admin evidence showed the existing Core scrape up
at 10.68.22.103:19448 and 13 tool-call series in VM storage. Grafana and the six
system observability probes were healthy. The ordinary monitoring catalog
returned `invalid server-side Grafana tenant bindings`. The ordinary tenant
binding explicitly excludes system Org1; that result is not evidence about the
Admin system datasource. Actual Grafana link acceptance must use its authorized
UI/provider context, without local credentials or broadening tenant scope.
Raw runtime evidence remains outside Git.

References: [Grafana data links](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/configure-data-links/),
[VM correlation/storage limitation](https://github.com/VictoriaMetrics/victoriametrics-datasource/blob/main/src/README.md#correlations),
[pinned logs plugin derived fields](https://github.com/VictoriaMetrics/victorialogs-datasource/blob/v0.17.0/src/getDerivedFields.ts).
