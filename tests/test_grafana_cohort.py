from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_grafana_is_independent_of_unhealthy_fair_value_workload():
    objects = list(yaml.safe_load_all((ROOT / 'releases/observability-domain-grafana/resources.yaml').read_text()))
    assert len(objects) == 15
    deployments = [obj for obj in objects if obj['kind'] == 'Deployment']
    assert {obj['metadata']['name'] for obj in deployments} == {'re8ch-grafana', 're8ch-grafana-renderer', 're8ch-grafana-postgresql'}
    assert all(obj['metadata']['namespace'] == 'observability-system' for obj in objects)
    assert all('@sha256:' in container['image'] for obj in deployments for container in obj['spec']['template']['spec']['containers'])
    other = list(yaml.safe_load_all((ROOT / 'releases/observability-domain-observability-system/resources.yaml').read_text()))
    identity = lambda obj: (obj['apiVersion'], obj['kind'], obj['metadata']['name'])
    assert not set(map(identity, objects)) & set(map(identity, other))
    assert any(obj['metadata']['name'] == 're8ch-fair-value-controller' for obj in other)
    contract = yaml.safe_load((ROOT / 'contracts/observability-domain-grafana.yaml').read_text())['spec']
    assert contract['lifecycle']['prune'] is False
    assert contract['authorization']['requireExisting'] is True
    assert not any('/PersistentVolumeClaim/' in identity for identity in contract['authorization']['forceConflictObjects'])
