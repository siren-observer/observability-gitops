import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]


def dashboard():
    patch = yaml.safe_load((ROOT / 'clusters/re8ch/toolchain-dashboard.patch.yaml').read_text())
    return json.loads(patch['data']['re8ch-toolchain-sentry.json'])


def test_scrapes_follow_only_reviewed_existing_service_identities():
    objects = list(yaml.safe_load_all((ROOT / 'clusters/re8ch/toolchain-scrapes.yaml').read_text()))
    expected = {
        'toolchain-connectool-gateway': ('tenant-infrastructure', 'tenant-api', 'catalog-mcp'),
        'toolchain-cloud-platform': ('ai-operations', 're8ch-cloud-platform', 'mcp'),
        'toolchain-tenant-control': ('tenant-infrastructure', 'tenant-control-controller', 'http'),
        'toolchain-among-hub': ('among-clusters', 'among-clusters-hub', 'metrics'),
        'toolchain-among-broker': ('credential-broker', 'among-clusters-credential-broker', 'metrics'),
    }
    assert {item['metadata']['name'] for item in objects} == set(expected)
    for item in objects:
        namespace, service, port = expected[item['metadata']['name']]
        assert item['kind'] == 'VMServiceScrape'
        assert item['metadata']['namespace'] == 'observability-system'
        assert item['metadata']['labels']['observability.re8ch.com/managed'] == 'true'
        assert item['spec']['namespaceSelector'] == {'matchNames': [namespace]}
        endpoint, = item['spec']['endpoints']
        assert (endpoint['port'], endpoint['path'], endpoint['scheme']) == (port, '/metrics', 'http')
        assert endpoint['relabelConfigs'][0] == {
            'action': 'keep', 'sourceLabels': ['__meta_kubernetes_service_name'], 'regex': service,
        }
        assert endpoint['relabelConfigs'][1]['replacement'] == item['metadata']['name']
        assert not any(key in endpoint for key in ('sampleLimit', 'seriesLimit'))
    # The pre-existing Core scrape remains the sole collector of its HTTP port.
    assert all(item['spec']['endpoints'][0]['port'] != 'http' or expected[item['metadata']['name']][1] != 'tenant-api' for item in objects)


def test_native_datasource_links_use_sentry_fields_not_unsupported_exemplars():
    patch = yaml.safe_load((ROOT / 'clusters/re8ch/toolchain-datasources.patch.yaml').read_text())
    text = patch['data']['datasources.yaml']
    sources = yaml.safe_load(text)['datasources']
    assert {item['uid'] for item in sources} == {'ds-prometheus', 're8ch-analytics', 're8ch-costs', 're8ch-traces', 're8ch-vlogs'}
    assert all('exemplarTraceIdDestinations' not in item.get('jsonData', {}) for item in sources)
    assert all('secureJsonData' not in item for item in sources)
    logs = next(item for item in sources if item['uid'] == 're8ch-vlogs')
    fields = logs['jsonData']['derivedFields']
    assert {field['matcherRegex'] for field in fields} == {'traceId', 'operationId', 'sentryEventId'}
    for field in fields:
        assert field['matcherType'] == 'label'  # Supported by the pinned v0.17.0 plugin.
        assert 'datasourceUid' not in field  # No false jump into the unrelated Jaeger store.
        assert urlsplit(field['url']).netloc == 're8ch-studio.sentry.io'
        assert 'project=4509349088985088' in field['url']
        # Datasource provisioning expands environment variables: preserve Grafana macros.
        assert '$${__value.raw}' in field['url']
    reload = yaml.safe_load((ROOT / 'clusters/re8ch/toolchain-grafana-reload.patch.yaml').read_text())
    assert reload['spec'] == {'template': {'metadata': {'annotations': {
        'observability.re8ch.com/datasources-sha256': hashlib.sha256(text.encode()).hexdigest(),
    }}}}


def test_metric_links_preserve_release_environment_and_selected_time():
    board = dashboard()
    variables = {item['name']: item for item in board['templating']['list']}
    assert set(variables) == {'component', 'environment', 'release'}
    assert all(item['multi'] is False and item['includeAll'] is False for item in variables.values())
    assert variables['release']['query'].startswith('label_values(re8ch_toolchain_build_info')
    links = [link for panel in board['panels'] for link in panel['fieldConfig']['defaults']['links']]
    assert any('tool_name%3A%22${__field.labels.tool_name}' in link['url'] for link in links)
    for link in links:
        assert urlsplit(link['url']).netloc == 're8ch-studio.sentry.io'
        for variable in ('component', 'environment', 'release'):
            assert '${' + variable + ':percentencode}' in link['url']
        assert 'start=${__from:date:iso}' in link['url'] and 'end=${__to:date:iso}' in link['url']
    metric_panels = [panel for panel in board['panels'] if panel.get('datasource', {}).get('uid') == 'ds-prometheus' and panel.get('targets')]
    for panel in metric_panels:
        query = panel['targets'][0]['expr']
        assert not any(identifier in query for identifier in ('traceId', 'trace_id', 'operation_id', 'sentryEventId'))
        if 'rate(' in query:
            assert 'group_left (release, repository)' in query and 're8ch_toolchain_build_info' in query
    log_panel = next(panel for panel in board['panels'] if panel['type'] == 'logs')
    query = log_panel['targets'][0]['expr']
    assert 'kubernetes.pod_namespace:in(' in query  # Actual VLAgent field, not a guessed alias.
    assert 'unpack_json keep_original_fields' in query and 'drop_empty_fields' in query
    assert all(identifier in query for identifier in ('traceId', 'operationId', 'sentryEventId'))
