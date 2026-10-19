#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

root = Path(__file__).resolve().parents[1]
policy = yaml.safe_load((root / "policies/domain.yaml").read_text())
documents = [d for d in yaml.safe_load_all((root / "clusters/re8ch/resources.yaml").read_text()) if d]
seen = set()
errors = []
for doc in documents:
    meta = doc.get("metadata", {})
    identity = (doc.get("apiVersion"), doc.get("kind"), meta.get("namespace", ""), meta.get("name"))
    if identity in seen:
        errors.append(f"duplicate object: {identity}")
    seen.add(identity)
for item in policy.get("forbidden", []):
    identity = (item["apiVersion"], item["kind"], item.get("namespace", ""), item["name"])
    if identity in seen:
        errors.append(f"product-owned object is forbidden: {identity}")
release_names = {
    "re8ch-kube-state-metrics": "re8ch-kube-state-metrics",
    "re8ch-opentelemetry-operator": "otel-operator",
    "victoria-metrics-operator": "victoria-metrics-operator",
}
oci_digests = {
    "prometheus-community": "sha256:1fe070bab14c87f6bcdbef42200cf39b207b5f3d3a20234c429cebfe1bdb4270",
    "open-telemetry": "sha256:9e3b657e793e7e7f69b7770de46851aebc5fc2fe00c1866ddee999ad61cb73dc",
    "victoriametrics": "sha256:454e94bbc58a44edf760c69d69d3e2cbc4a355b90b5adda2dcc28069213fb442",
}
for name, release_name in release_names.items():
    release = next((d for d in documents if d.get("kind") == "HelmRelease" and d.get("metadata", {}).get("name") == name), None)
    if not release or release.get("spec", {}).get("releaseName") != release_name:
        errors.append(f"Helm ownership key mismatch: {name} must use releaseName {release_name}")
for name, digest in oci_digests.items():
    source = next((d for d in documents if d.get("kind") == "OCIRepository" and d.get("metadata", {}).get("name") == name), None)
    if not source or source.get("spec", {}).get("ref", {}).get("digest") != digest:
        errors.append(f"OCI source is not pinned: {name}")
        continue
    if source.get("spec", {}).get("layerSelector") != {
        "mediaType": "application/vnd.cncf.helm.chart.content.v1.tar+gzip",
        "operation": "copy",
    }:
        errors.append(f"OCI Helm layer selector is not pinned: {name}")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"validated {policy['domain']}: {len(documents)} objects")
