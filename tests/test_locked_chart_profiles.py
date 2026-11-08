from pathlib import Path
import json
import sys
import shutil
import pytest
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'operations/releases'))
import profile
from compile_chart_access import outputs

def test_chart_runtime_contains_no_secret_rbac_or_cluster_authority():
    files=outputs()
    access=list(yaml.safe_load_all(files[ROOT/'operations/releases/chart-access.yaml']))
    for d in access:
        for rule in d.get('rules',[]):
            assert 'rbac.authorization.k8s.io' not in rule['apiGroups']
            assert 'secrets' not in rule['resources']
            assert not {'bind','escalate','impersonate','delete'} & set(rule['verbs'])
    releases=json.loads(files[ROOT/'operations/releases/chart-releases.json'])
    assert len(releases)==8
    assert sum(r['objects'] for r in releases)==49

def test_changed_chart_values_require_new_locked_render(tmp_path,monkeypatch):
    name='observability-chart-incidentrelay'
    (tmp_path/'contracts').mkdir()
    shutil.copy(ROOT/'contracts'/f'{name}.yaml',tmp_path/'contracts'/f'{name}.yaml')
    shutil.copytree(ROOT/'releases'/name,tmp_path/'releases'/name)
    monkeypatch.setattr(profile,'ROOT',tmp_path)
    monkeypatch.setattr(profile,'CONTRACT_ROOT',tmp_path/'contracts')
    values=tmp_path/'releases'/name/'values.yaml'
    values.write_text(values.read_text()+'\nunreviewedChange: true\n')
    with pytest.raises(ValueError,match='values digest mismatch'):
        profile.validate_contract(tmp_path/'contracts'/f'{name}.yaml')

def test_admin_adoption_list_is_reviewed_and_locked_without_core_namespaces():
    values=yaml.safe_load((ROOT/'releases/observability-chart-birfucate-metering/values.yaml').read_text())
    admin=next(item for item in values['tenantPlatform']['tenants'] if item['name']=='admin')
    adopted=set(admin['namespacePolicy']['adoptedNamespaces'])
    assert {'tenant-infrastructure','toolhive-system','observability-system','rook-ceph','flux-system'} <= adopted
    assert not {'default','kube-system','kube-public','kube-node-lease'} & adopted
    assert admin['namespacePolicy']['maxNamespaces'] == 100
