import json
from pathlib import Path
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / 'clusters/re8ch/charts/birfucate-metering'
VALUES = ROOT / 'releases/observability-chart-birfucate-metering/values.yaml'


def render(*extra, success=True):
    run = subprocess.run(['helm', 'template', 'birfucate-metering', str(CHART), '--kube-version', '1.35.0', '-n', 'observability-ai', '-f', str(VALUES), *extra], capture_output=True, text=True)
    if not success:
        assert run.returncode != 0
        return run.stderr
    assert run.returncode == 0, run.stderr
    return [d for d in yaml.safe_load_all(run.stdout) if d]


def test_public_re8ch_plugin_uses_reviewed_tool_endpoint():
    route = next(d for d in render() if d['kind'] == 'HTTPRoute' and d['metadata']['name'] == 'tenant-native-mcp')
    rule = next(r for r in route['spec']['rules'] if r['matches'][0]['path']['value'] == '/tenant-native/mcp')
    assert rule['filters'][0]['urlRewrite']['path']['replaceFullPath'] == '/plugin/mcp'


def test_disabled_collaboration_has_no_credential_write_or_admin_publication():
    docs = render('--set', 'tenantPlatform.tenantAPI.stalwartBootstrapEnabled=false',
                  '--set', 'tenantPlatform.tenantAPI.collaboration.enabled=false')
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
    assert 'validationRef' in render('--set', 'tenantPlatform.tenantAPI.collaboration.enabled=true', '--set', 'tenantPlatform.tenantAPI.collaboration.origin=https://provider.example', '--set', 'tenantPlatform.tenantAPI.collaboration.clientID=fixture', '--set-string', 'tenantPlatform.tenantAPI.collaboration.validationRef=', success=False)


def test_userhub_authorization_requires_exact_endpoints():
    error = render('--set', 'tenantPlatform.tenantAPI.collaboration.enabled=true',
                   '--set', 'tenantPlatform.tenantAPI.collaboration.origin=https://provider.example',
                   '--set', 'tenantPlatform.tenantAPI.collaboration.clientID=stalwart-webui',
                   '--set', 'tenantPlatform.tenantAPI.collaboration.authorizationMode=auth-hub-pkce',
                   '--set-string', 'tenantPlatform.tenantAPI.collaboration.authorizationURL=',
                   '--set', 'tenantPlatform.tenantAPI.collaboration.validationRef=fixture', success=False)
    assert 'collaboration.authorizationURL is required' in error


def test_management_allowlist_is_exact_and_separate_from_collaboration():
    docs = render('--set', 'tenantPlatform.tenantAPI.stalwartAdminEnabled=true',
                  '--set', 'tenantPlatform.tenantAPI.collaboration.enabled=false')
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
    jsonschema.validate({'name': 'collaboration-stalwart', 'consumableRef': 'collaboration.stalwart.v1', 'roleRef': 'viewer', 'lifecycle': 'Suspended'}, grant_schema)


def test_staged_personal_grant_is_exactly_re8ch_viewer_only():
    source = [d for d in yaml.safe_load_all((ROOT / 'clusters/re8ch/resources.yaml').read_text()) if d]
    release = next(d for d in source if d['kind'] == 'HelmRelease' and d['metadata']['name'] == 'birfucate-metering')
    tenants = release['spec']['values']['tenantPlatform']['tenants']
    candidate = {'name': 're8ch-stalwart-personal-consent', 'consumableRef': 'collaboration.stalwart.v1',
                 'roleRef': 'viewer', 'lifecycle': 'Active'}
    assert [g for t in tenants for g in t['grants'] if g['consumableRef'] == 'collaboration.stalwart.v1'] == [candidate]
    assert [g for t in tenants if t['name'] == 're8ch' for g in t['grants'] if g['consumableRef'] == 'collaboration.stalwart.v1'] == [candidate]
    for values in (ROOT / 'releases').glob('observability-chart-birfucate-metering*/values.yaml'):
        tenants = yaml.safe_load(values.read_text())['tenantPlatform']['tenants']
        assert [g for t in tenants if t['name'] == 're8ch' for g in t['grants'] if g['consumableRef'] == 'collaboration.stalwart.v1'] == [candidate]


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
    docs = render('--set', 'tenantPlatform.tenantAPI.stalwartBootstrapEnabled=true',
                  '--set', 'tenantPlatform.tenantAPI.collaboration.enabled=false')
    modules = next(d for d in docs if d['kind'] == 'ConfigMap' and d['metadata']['name'] == 'tenant-platform-modules')
    allowed = json.loads(modules['data']['modules.json'])['backends']['native']['allowed']
    assert {k for k, v in allowed.items() if k.startswith('credentials.stalwart.') and v} == {
        'credentials.stalwart.ensure', 'credentials.stalwart.authority.ensure'}
    assert not any(k.startswith('stalwart.admin.') for k in allowed)
    assert not any(d['metadata'].get('namespace') == 'stalwart-credentials' for d in docs)


def test_production_activation_enables_user_collaboration_and_closes_bootstrap_window():
    docs = list(yaml.safe_load_all((ROOT / 'releases/observability-chart-birfucate-metering-tenant-infrastructure/resources.yaml').read_text()))
    modules = next(d for d in docs if d['kind'] == 'ConfigMap' and d['metadata']['name'] == 'tenant-platform-modules')
    allowed = json.loads(modules['data']['modules.json'])['backends']['native']['allowed']
    assert not {k for k in allowed if 'stalwart' in k}
    dep = next(d for d in docs if d['kind'] == 'Deployment' and d['metadata']['name'] == 'tenant-api')
    env = {e['name']: e.get('value') for e in dep['spec']['template']['spec']['containers'][0]['env']}
    assert env['COLLABORATION_ENABLED'] == 'true'
    assert env['STALWART_URL'] == 'https://id.re8ch.com'
    assert env['STALWART_CONNECT_URL'] == 'http://stalwart.mail-system.svc.cluster.local:8080'
    assert env['STALWART_CLIENT_ID'] == 'stalwart-webui'
    assert env['COLLABORATION_AUTH_MODE'] == 'auth-hub-pkce'
    assert env['STALWART_AUTHORIZATION_URL'] == 'https://auth.re8ch.com/authorize'
    assert env['STALWART_TOKEN_URL'] == 'https://auth.re8ch.com/token'
    assert env['STALWART_REDIRECT_URI'] == 'https://tools.service.re8ch.com/collaboration/oauth/callback'
    route = next(d for d in docs if d['kind'] == 'HTTPRoute' and d['metadata']['name'] == 'tenant-native-mcp')
    paths = {m['path']['value'] for rule in route['spec']['rules'] for m in rule.get('matches', [])}
    assert '/collaboration/oauth/callback' in paths
    assert dep['spec']['template']['spec']['containers'][0]['image'].endswith('@sha256:18a88733d5f5cd103623e5f0ca32527932561c3434e7efcbac3f55e0e7d7e4ea')
    assert not any(d['kind'] in {'Secret', 'Role', 'RoleBinding', 'Namespace'} for d in docs)
