#!/usr/bin/env python3
"""Validate the bounded observability-metering release profile."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts"
REPOSITORY = "siren-observer/observability-gitops"
WORKFLOW = ".github/workflows/static-release.yml"
ENVIRONMENT = "release-executor-observability-metering"
AUDIENCE = "https://kube-api.re8ch.com/release-executor-observability-metering"
GROUP = "re8ch:release-executor:observability-metering"
SIGNER = f"https://github.com/{REPOSITORY}/{WORKFLOW}@refs/heads/main"
REPLAY_WORKFLOW = ".github/workflows/observability-metering-reconcile.yml"
REPLAY_ENVIRONMENT = "release-reconciler-observability-metering"
REPLAY_AUDIENCE = "https://kube-api.re8ch.com/release-reconciler-observability-metering"


# The historical bundle includes workloads currently owned by agent-runtime.
# Preserve its state for inspection while both scheduled and direct writes are fenced.
WRITE_FENCED = {"observability-chart-birfucate-metering-tenant-infrastructure"}


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_contract(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    if CONTRACT_ROOT.resolve() not in resolved.parents or resolved.suffix not in {".yaml", ".yml"}:
        raise ValueError("contract must be a YAML file under contracts")
    contract = yaml.safe_load(resolved.read_text())
    spec = contract["spec"]
    if spec.get("authorityDomain") != "observability-metering":
        raise ValueError("contract authorityDomain must be observability-metering")
    if not contract["metadata"]["name"].startswith("observability-"):
        raise ValueError("contract name is outside observability-metering")
    expected = {
        "repository": REPOSITORY,
        "workflow": WORKFLOW,
        "ref": "refs/heads/main",
        "environment": ENVIRONMENT,
        "audience": AUDIENCE,
        "signer": SIGNER,
    }
    for field, value in expected.items():
        if spec["provenance"].get(field) != value:
            raise ValueError(f"contract provenance {field} must be {value}")
    source = spec["source"]
    source_path = source.get("path", "")
    if source.get("repository") != REPOSITORY or not source_path.startswith("releases/"):
        raise ValueError("contract source must resolve inside this repository")
    if source.get("revision") == "github-main-reviewed":
        if source.get("renderer") != "kustomize" or not source_path.startswith("releases/" + ("observability" if spec["authorityDomain"] == "observability-metering" else spec["authorityDomain"]) + "-domain-"):
            raise ValueError("static domain source must use its generated namespace cohort")
    else:
        if source.get("renderer") != "kustomize" or ("@sha256:" not in source.get("chartOCI", "") and not source.get("chartDigest")):
            raise ValueError("shadow source must bind a digest-pinned Helm chart and reviewed Kustomize render")
        for value in source.get("values", []):
            value_path = (ROOT / value["path"]).resolve()
            if ROOT.resolve() not in value_path.parents or sha256(value_path) != value["digest"]:
                raise ValueError(f"values digest mismatch: {value['path']}")
        locked = yaml.safe_load((ROOT / source_path / "source.yaml").read_text())["spec"]
        if locked["chart"] != source.get("chartOCI", source.get("chart")):
            raise ValueError("locked render chart differs from contract")
        if locked["valuesDigest"] != sha256(ROOT / source_path / locked["values"]):
            raise ValueError("locked render values digest mismatch")
        if locked["renderedResourcesDigest"] != sha256(ROOT / source_path / locked["renderedResources"]):
            raise ValueError("locked rendered resources digest mismatch")
    if source.get("chartDigest"):
        from unified_bundle import canonical, digest
        chart = (ROOT / source["chart"]).resolve()
        if ROOT.resolve() not in chart.parents:
            raise ValueError("local chart is outside repository")
        entries = [(str(f.relative_to(chart)), sha256(f)) for f in sorted(chart.rglob("*")) if f.is_file()]
        if digest(canonical(entries)) != source["chartDigest"]:
            raise ValueError("local chart source changed; regenerate the locked render")
    if source.get("chartOCI") or source.get("chartDigest"):
        locked = yaml.safe_load((ROOT / source_path / "source.yaml").read_text())["spec"]
        if locked.get("helmDeclarationDigest"):
            from unified_bundle import canonical, digest
            reference = locked["helmRelease"]
            declaration = next(d for d in yaml.safe_load_all((ROOT / "clusters/re8ch/resources.yaml").read_text())
                               if d and d.get("kind") == "HelmRelease" and d["metadata"]["name"] == reference["name"]
                               and d["metadata"]["namespace"] == reference["namespace"])
            if digest(canonical(declaration["spec"])) != locked["helmDeclarationDigest"]:
                raise ValueError("Helm desired values changed; regenerate the locked render")
    return {
        "release-id": contract["metadata"]["name"],
        "namespace": spec["target"]["namespace"],
        "domain": "observability-metering",
        "environment": ENVIRONMENT,
        "audience": AUDIENCE,
        "kubernetes-group": GROUP,
        "signer": SIGNER,
    }


def replay_provenance(contract: dict) -> dict[str, str] | None:
    spec = contract["spec"]
    expected = {"repository": REPOSITORY, "workflow": WORKFLOW, "ref": "refs/heads/main",
                "environment": ENVIRONMENT, "audience": AUDIENCE, "signer": SIGNER}
    if spec.get("authorityDomain") != "observability-metering" or any(spec.get("provenance", {}).get(k) != v for k, v in expected.items()):
        return None
    return {"repository": REPOSITORY, "workflow": REPLAY_WORKFLOW, "ref": "refs/heads/main",
            "environment": REPLAY_ENVIRONMENT, "audience": REPLAY_AUDIENCE}


def replay_matrix() -> list[dict[str, str]]:
    result = []
    for path in sorted(CONTRACT_ROOT.glob("observability-*.yaml")):
        if path.stem in WRITE_FENCED:
            continue
        profile = validate_contract(path.relative_to(ROOT))
        result.append({**profile, "contract": str(path.relative_to(ROOT)),
                       "environment": REPLAY_ENVIRONMENT, "audience": REPLAY_AUDIENCE})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--replay-matrix", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    if args.replay_matrix:
        print(json.dumps({"include": replay_matrix()}, separators=(",", ":")))
        return 0
    if args.contract is None:
        parser.error("--contract is required unless --replay-matrix is used")
    result = validate_contract(args.contract)
    if args.github_output:
        with args.github_output.open("a") as output:
            for key, value in result.items():
                output.write(f"{key}={value}\n")
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
