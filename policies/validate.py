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
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"validated {policy['domain']}: {len(documents)} objects")
