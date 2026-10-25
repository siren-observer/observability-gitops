"""Exercise the code actually shipped in the GitOps ConfigMap, without network."""
import json
from pathlib import Path
from types import ModuleType

import yaml


def test_missing_region_does_not_abort_other_valuations(tmp_path):
    docs = list(yaml.safe_load_all(Path('clusters/re8ch/resources.yaml').read_text()))
    maps = {d['metadata']['name']: d['data'] for d in docs if d['kind'] == 'ConfigMap'}
    runtime = ModuleType('fair_value_runtime')
    exec(compile(maps['re8ch-fair-value-controller-code']['fair-value-controller.py'],
                 'fair-value-controller.py', 'exec'), runtime.__dict__)
    config = json.loads(maps['re8ch-fair-value-controller-config']['fair-value-config.json'])
    # Keep the production inventory, including the unmapped eu-central target.
    runtime.fetch_ecb_usd_cny = lambda url: 7.0
    runtime.linode_offers = lambda *args: [dict(cpuCores=128, memoryGiB=1024,
        storageGiB=100000, monthlyCNY=100, region='fixture', sku='fixture')]
    runtime.vultr_offers = runtime.linode_offers
    runtime.azure_offers = lambda *args: []
    controller = runtime.Controller(config, str(tmp_path / 'history.jsonl'), fetcher=lambda url: {})
    controller.refresh()
    items = {i['node']: i for i in controller.snapshot['items']}
    missing = items['overseas-flk']
    assert missing['status'] == 'unknown'
    assert missing['reason'] == 'region-mapping-missing'
    assert missing['fairMonthlyCNY'] is None
    assert missing['sourceCount'] == 0
    assert any(i['status'] == 'usable' for i in items.values())
    assert len(items) == len(config['targets'])
    assert json.loads((tmp_path / 'history.jsonl').read_text()) == controller.snapshot
