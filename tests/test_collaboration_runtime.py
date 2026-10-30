import json
from pathlib import Path
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / 'clusters/re8ch/charts/birfucate-metering'
VALUES = ROOT / 'releases/observability-chart-birfucate-metering/values.yaml'


def render(*extra, success=True):
    run = subprocess.run(['helm', 'template', 'birfucate-metering', str(CHART), '-n', 'observability-ai', '-f', str(VALUES), *extra], capture_output=True, text=True)
    if not success:
        assert run.returncode != 0
        return run.stderr
    assert run.returncode == 0, run.stderr
    return [d for d in yaml.safe_load_all(run.stdout) if d]


def test_disabled_collaboration_has_no_credential_write_or_admin_publication():
    docs = render('--set', 'tenantPlatform.tenantAPI.stalwartBootstrapEnabled=false')
    assert not any(d['metadata'].get('namespace') == 'stalwart-credentials' for d in docs)
    dep = next(d for d in docs if d['kind'] == 'Deployment' and d['metadata']['name'] == 'tenant-api')
    env = {e['name']: e.get('value') for e in dep['spec']['template']['spec']['containers'][0]['env']}
    assert env['COLLABORATION_ENABLED'] == 'false'
    assert env['COLLABORATION_CREDENTIAL_NAMESPACE'] == 'stalwart-credentials'
    shared = next(d for d in docs if d['kind'] == 'Role' and d['metadata']['name'] == 'tenant-api-credential-read')
    assert shared['rules'] == [{'apiGroups': [''], 'resources': ['secrets'], 'verbs': ['get']}]
    modules = next(d for d in docs if d['kind'] == 'ConfigMap' and d['metadata']['name'] == 'tenant-platform-modules')
    allowed = json.loads(modules['data']['modules.json'])['backends']['native']['allowed']
    assert not any(k.startswith('stalwart.') for k in allowed)
    assert not any(k.startswith('credentials.stalwart.') for k in allowed)


def test_enabled_credentials_have_only_namespaced_lifecycle_permissions():
    docs = render('--set', 'tenantPlatform.tenantAPI.collaboration.enabled=true', '--set', 'tenantPlatform.tenantAPI.collaboration.origin=https://provider.example', '--set', 'tenantPlatform.tenantAPI.collaboration.clientID=reviewed-client', '--set', 'tenantPlatform.tenantAPI.collaboration.validationRef=fixture')
    role = next(d for d in docs if d['kind'] == 'Role' and d['metadata']['name'] == 'tenant-api-stalwart-credentials')
    assert role['metadata']['namespace'] == 'stalwart-credentials'
    assert role['rules'] == [{'apiGroups': [''], 'resources': ['secrets'], 'verbs': ['get', 'create', 'update', 'delete']}]
    binding = next(d for d in docs if d['kind'] == 'RoleBinding' and d['metadata']['name'] == role['metadata']['name'])
    assert binding['subjects'] == [{'kind': 'ServiceAccount', 'name': 'tenant-api', 'namespace': 'tenant-infrastructure'}]


def test_activation_requires_reviewed_evidence():
    assert 'validationRef' in render('--set', 'tenantPlatform.tenantAPI.collaboration.enabled=true', '--set', 'tenantPlatform.tenantAPI.collaboration.origin=https://provider.example', '--set', 'tenantPlatform.tenantAPI.collaboration.clientID=fixture', success=False)


def test_management_allowlist_is_exact_and_separate_from_collaboration():
    docs = render('--set', 'tenantPlatform.tenantAPI.stalwartAdminEnabled=true')
    modules = next(d for d in docs if d['kind'] == 'ConfigMap' and d['metadata']['name'] == 'tenant-platform-modules')
    allowed = json.loads(modules['data']['modules.json'])['backends']['native']['allowed']
    assert {k for k, v in allowed.items() if k.startswith('stalwart.') and v} == {'stalwart.admin.read', 'stalwart.admin.plan', 'stalwart.admin.apply'}
    assert not any(d['metadata'].get('namespace') == 'stalwart-credentials' for d in docs)


def test_draft_consumable_candidate_and_suspended_grant_match_owned_schemas():
    import jsonschema
    docs = list(yaml.safe_load_all((CHART / 'crds/finops.re8ch.com.yaml').read_text()))
    crd = next(d for d in docs if d['metadata']['name'] == 'consumables.finops.re8ch.com')
    candidate = yaml.safe_load((ROOT / 'operations/releases/collaboration-candidate.yaml').read_text())
    jsonschema.validate(candidate, crd['spec']['versions'][0]['schema']['openAPIV3Schema'])
    assert candidate['spec']['lifecycle'] == 'Draft'
    assert not any(d['kind'] == 'Consumable' and d['spec']['serviceClass'] == 'collaboration.stalwart.v1' for d in render())
    docs = list(yaml.safe_load_all((CHART / 'crds/tenancy.re8ch.com.yaml').read_text()))
    crd = next(d for d in docs if d['metadata']['name'] == 'tenants.tenancy.re8ch.com')
    grant_schema = crd['spec']['versions'][0]['schema']['openAPIV3Schema']['properties']['spec']['properties']['grants']['items']
    jsonschema.validate({'name': 'collaboration-stalwart', 'consumableRef': 'collaboration.stalwart.v1', 'roleRef': 'operator', 'lifecycle': 'Suspended'}, grant_schema)


def test_discovery_controller_does_not_provision_or_ready_draft_collaboration():
    from types import ModuleType
    module = ModuleType('collaboration_discovery_test')
    code = (CHART / 'files/controller.py').read_text()
    exec(compile(code, 'controller.py', 'exec'), module.__dict__)
    candidate = yaml.safe_load((ROOT / 'operations/releases/collaboration-candidate.yaml').read_text())
    class FakeKube:
        def __init__(self):
            self.statuses = []
        def list(self, api, plural):
            if plural == 'consumables':
                return [candidate]
            if plural == 'consumptionbindings':
                return [{'metadata': {'name': 'fixture', 'namespace': 'tenant-fixture'}, 'spec': {'consumableRef': 'collaboration-stalwart', 'access': {'type': 'Collaboration'}}}]
            return []
        def patch_status(self, plural, namespace, name, status):
            self.statuses.append(status)
        def apply(self, *args):
            raise AssertionError('Draft collaboration caused provisioning')
    kube = FakeKube()
    assert module.reconcile(kube, {}) == 0
    assert len(kube.statuses) == 1
    assert kube.statuses[0]['phase'] == 'Pending'
    assert kube.statuses[0]['conditions'][0]['reason'] == 'OfferingNotApproved'


def test_bootstrap_publication_is_exact_and_does_not_enable_steady_state_admin():
    docs = render('--set', 'tenantPlatform.tenantAPI.stalwartBootstrapEnabled=true')
    modules = next(d for d in docs if d['kind'] == 'ConfigMap' and d['metadata']['name'] == 'tenant-platform-modules')
    allowed = json.loads(modules['data']['modules.json'])['backends']['native']['allowed']
    assert {k for k, v in allowed.items() if k.startswith('credentials.stalwart.') and v} == {
        'credentials.stalwart.ensure', 'credentials.stalwart.authority.ensure'}
    assert not any(k.startswith('stalwart.admin.') for k in allowed)
    assert not any(d['metadata'].get('namespace') == 'stalwart-credentials' for d in docs)


def test_production_bootstrap_window_has_exact_two_tools_and_no_other_object_change():
    docs = list(yaml.safe_load_all((ROOT / 'releases/observability-chart-birfucate-metering-tenant-infrastructure/resources.yaml').read_text()))
    modules = next(d for d in docs if d['kind'] == 'ConfigMap' and d['metadata']['name'] == 'tenant-platform-modules')
    allowed = json.loads(modules['data']['modules.json'])['backends']['native']['allowed']
    assert {k for k in allowed if 'stalwart' in k} == {'credentials.stalwart.ensure', 'credentials.stalwart.authority.ensure'}
    dep = next(d for d in docs if d['kind'] == 'Deployment' and d['metadata']['name'] == 'tenant-api')
    env = {e['name']: e.get('value') for e in dep['spec']['template']['spec']['containers'][0]['env']}
    assert env['COLLABORATION_ENABLED'] == 'false'
    assert not any(d['kind'] in {'Secret', 'Role', 'RoleBinding', 'Namespace'} for d in docs)
