#!/usr/bin/env python3
"""Emit exact, non-RBAC runtime access for locked chart snapshots."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import yaml
from compile_domain import ROOT, PLURALS, CUSTOM_TYPES, rendered, group
from operation_materialize import state_configmap_name
from profile import GROUP, validate_contract
from unified_bundle import compile_bundle

def outputs():
    access=[]; summary=[]
    for path in sorted((ROOT/'contracts').glob('observability-chart-*.yaml')):
        validate_contract(path);contract=yaml.safe_load(path.read_text());spec=contract['spec'];name=contract['metadata']['name'];ns=spec['target']['namespace']
        objects=rendered(ROOT/spec['source']['path'])
        compile_bundle(contract,yaml.safe_dump_all(objects,sort_keys=False).encode())
        rules=defaultdict(set)
        for d in objects:
            if group(d)=='rbac.authorization.k8s.io' or d['kind']=='Secret' or d['metadata'].get('namespace')!=ns:
                raise ValueError('chart runtime snapshot contains platform-owned authority')
            plural=PLURALS.get(d['kind']) or CUSTOM_TYPES.get(group(d)+'/'+d['kind']) or {'Certificate':'certificates','Issuer':'issuers'}.get(d['kind'])
            if not plural:raise ValueError('unregistered chart resource kind')
            rules[(group(d),plural)].add(d['metadata']['name'])
        state=state_configmap_name(name);rules[('core','configmaps')].add(state)
        access += [{'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':state,'namespace':ns,'labels':{'delivery.re8ch.com/state':'accepted','delivery.re8ch.com/authority-domain':'observability-metering'}}},
          {'apiVersion':'rbac.authorization.k8s.io/v1','kind':'Role','metadata':{'name':name,'namespace':ns},'rules':[{'apiGroups':['' if api=='core' else api],'resources':[resource],'resourceNames':sorted(names),'verbs':['get','patch','update']} for (api,resource),names in sorted(rules.items())]},
          {'apiVersion':'rbac.authorization.k8s.io/v1','kind':'RoleBinding','metadata':{'name':name,'namespace':ns},'roleRef':{'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':name},'subjects':[{'apiGroup':'rbac.authorization.k8s.io','kind':'Group','name':GROUP}]}]
        summary.append({'release':name,'contract':str(path.relative_to(ROOT)),'namespace':ns,'objects':len(objects)})
    return {ROOT/'operations/releases/chart-access.yaml':yaml.safe_dump_all(access,sort_keys=False,explicit_start=True),ROOT/'operations/releases/chart-releases.json':json.dumps(summary,indent=2)+'\n'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    for path,body in outputs().items():
        if args.check:
            if not path.exists() or path.read_text()!=body:raise SystemExit('stale chart access: '+str(path))
        else:path.write_text(body)
    print('validated locked chart runtime profiles')
