#!/usr/bin/env python3
"""Refresh reviewed Helm runtime snapshots; never apply or read cluster Secrets.

Pinned images: deployed operator image IDs were observed through platform audit
op_f0e06203a3da44abbaeb0e15129bf4bd. The pause index digest was verified from the
registry content digest. Updating those pins is an explicit reviewed change.
Remaining bootstrap objects are recorded by identity without Secret payloads.
"""
from pathlib import Path
import yaml,json,hashlib,subprocess,tempfile,sys
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'operations/releases'))
from unified_bundle import canonical,digest,compile_bundle,object_identity
from profile import REPOSITORY,WORKFLOW,ENVIRONMENT,AUDIENCE,SIGNER,GROUP
from operation_materialize import state_configmap_name
from compile_domain import PLURALS,CUSTOM_TYPES
cache_context=tempfile.TemporaryDirectory(prefix='observability-chart-render-')
chart_cache=Path(cache_context.name)
source_docs=[d for d in yaml.safe_load_all((root/'clusters/re8ch/resources.yaml').read_text()) if d]
oci={d['metadata']['name']:d['spec'] for d in source_docs if d['kind']=='OCIRepository'}
images={'registry.k8s.io/pause:3.10.1':'registry.k8s.io/pause@sha256:278fb9dbcca9518083ad1e11276933a2e96f23de604a3a08cc3c80002767d24c','ghcr.io/open-telemetry/opentelemetry-operator/opentelemetry-operator:0.153.0':'ghcr.io/open-telemetry/opentelemetry-operator/opentelemetry-operator@sha256:71c80734e698e0a38039aeb5a6fad7129ca68eaa31eb262752c1e5015b319a24','victoriametrics/operator:v0.74.0':'docker.io/victoriametrics/operator@sha256:c4fde419a4f03c7c45d7ee554e7039c12c75af161f7f7e1baef1b343015e3df9'}
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def treehash(p):return digest(canonical([(str(f.relative_to(p)),sha(f.read_bytes())) for f in sorted(p.rglob('*')) if f.is_file()]))
def replace_images(v):
 if isinstance(v,dict):
  for k,c in v.items():
   if k=='image' and c in images:v[k]=images[c]
   else:replace_images(c)
 elif isinstance(v,list):
  for c in v:replace_images(c)
selected=['incidentrelay','re8ch-opentelemetry-operator','victoria-metrics-operator','birfucate-metering'];ledger=[];access=[]
for hr in source_docs:
 if hr['kind']!='HelmRelease' or hr['metadata']['name'] not in selected:continue
 hn=hr['metadata']['name'];spec=hr['spec'];namespace=spec['targetNamespace'];name='observability-chart-'+hn
 p=root/'releases'/name;p.mkdir(parents=True,exist_ok=True)
 values=spec.get('values',{}).copy()
 if hn=='birfucate-metering':
  values=json.loads(json.dumps(values));values.setdefault('tenantPlatform',{}).setdefault('tenantAPI',{})['image']='registry.re8ch.com/image/re8ch-tenant-mcp@sha256:b2b2e416e1e1eb6ca783d890dd057a9efea4a6c60fe6081d1d7cb0055399a674'
 values_bytes=yaml.safe_dump(values,sort_keys=False).encode();(p/'values.yaml').write_bytes(values_bytes)
 if hn=='birfucate-metering':
  chart=root/'clusters/re8ch/charts/birfucate-metering';chart_ref='clusters/re8ch/charts/birfucate-metering';chart_digest=treehash(chart);version=yaml.safe_load((chart/'Chart.yaml').read_text())['version']
  raw=subprocess.check_output(['helm','template',spec.get('releaseName',hn),str(chart),'--namespace',namespace,'--include-crds','-f',str(p/'values.yaml')],text=True)
 else:
  src=oci[spec['chartRef']['name']];chart_ref=src['url']+'@'+src['ref']['digest'];chart_digest=src['ref']['digest']
  subprocess.run(['helm','pull',chart_ref,'--destination',str(chart_cache)],check=True)
  chart=next(chart_cache.glob(src['url'].split('/')[-1]+'@*.tgz'))
  version=yaml.safe_load(subprocess.check_output(['helm','show','chart',str(chart)],text=True))['version']
  raw=subprocess.check_output(['helm','template',spec.get('releaseName',hn),str(chart),'--namespace',namespace,'--include-crds','-f',str(p/'values.yaml')],text=True)
 if spec.get('postRenderers'):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);(t/'resources.yaml').write_text(raw)
   for renderer in spec['postRenderers']:
    k={'apiVersion':'kustomize.config.k8s.io/v1beta1','kind':'Kustomization','resources':['resources.yaml'],**renderer['kustomize']};(t/'kustomization.yaml').write_text(yaml.safe_dump(k,sort_keys=False));raw=subprocess.check_output(['kubectl','kustomize',td],text=True);(t/'resources.yaml').write_text(raw)
 objects=[];deferred=[]
 for d in yaml.safe_load_all(raw):
  if not d:continue
  kind=d['kind'];api=d['apiVersion'].split('/')[0] if '/' in d['apiVersion'] else 'core'
  reason=None
  if kind=='Secret':reason='secret-provisioning'
  elif kind=='Namespace':reason='platform-bootstrap'
  elif api=='rbac.authorization.k8s.io':reason='platform-owned-rbac'
  elif d.get('metadata',{}).get('annotations',{}).get('helm.sh/hook'):reason='helm-hook'
  elif kind not in PLURALS and api+'/'+kind not in CUSTOM_TYPES and kind not in ['Certificate','Issuer']:reason='platform-bootstrap'
  if reason:
   deferred.append({'kind':kind,'name':d['metadata']['name'],'reason':reason});continue
  d['metadata'].setdefault('namespace',namespace);replace_images(d);objects.append(d)
 all_objects=objects
 for target_namespace in sorted({d['metadata']['namespace'] for d in all_objects}):
  namespace=target_namespace
  name='observability-chart-'+hn+('-'+namespace if namespace!=spec['targetNamespace'] else '')
  if len(name)>63:name=name[:52].rstrip('-')+'-'+hashlib.sha256(name.encode()).hexdigest()[:10]
  p=root/'releases'/name;p.mkdir(parents=True,exist_ok=True);(p/'values.yaml').write_bytes(values_bytes)
  objects=[d for d in all_objects if d['metadata']['namespace']==namespace]
  objects.sort(key=object_identity)
  body=yaml.safe_dump_all(objects,sort_keys=False,explicit_start=True).encode();(p/'resources.yaml').write_bytes(body)
  (p/'kustomization.yaml').write_text('apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources: [resources.yaml]\n')
  source={'renderer':'kustomize','revision':('git-chart@' if hn=='birfucate-metering' else 'helm-oci@')+chart_digest,'repository':REPOSITORY,'path':'releases/'+name,'values':[{'path':str((p/'values.yaml').relative_to(root)),'digest':sha(values_bytes)}]}
  source.update({'chart':chart_ref,'chartDigest':chart_digest} if hn=='birfucate-metering' else {'chartOCI':chart_ref})
  inventory=sorted(object_identity(d) for d in objects)
  contract={'apiVersion':'delivery.re8ch.com/v1alpha1','kind':'ReleaseContract','metadata':{'name':name},'spec':{'authorityDomain':'observability-metering','target':{'cluster':'re8ch','namespace':namespace},'source':source,'provenance':{'repository':REPOSITORY,'workflow':WORKFLOW,'ref':'refs/heads/main','environment':ENVIRONMENT,'audience':AUDIENCE,'signer':SIGNER,'issuer':'https://token.actions.githubusercontent.com'},'authorization':{'fieldManager':'re8ch-release/'+name,'resources':sorted({(d['apiVersion'].split('/')[0] if '/' in d['apiVersion'] else 'core')+'/'+d['kind'] for d in objects}),'objectNames':sorted({d['metadata']['name'] for d in objects}),'allowClusterScoped':False,'requireExisting':True,'forceConflictObjects':[object_identity(d) for d in objects if d['kind'] not in {'Namespace','CustomResourceDefinition','PersistentVolume','PersistentVolumeClaim','StorageClass'}]},'inventory':{'digest':digest(canonical(inventory))},'lifecycle':{'prune':False,'healthTimeoutSeconds':300,'protectedKinds':['Namespace','CustomResourceDefinition','PersistentVolume','PersistentVolumeClaim','StorageClass'],'deletionAllowlist':[]}}}
  compile_bundle(contract,body)
  (root/'contracts'/f'{name}.yaml').write_text(yaml.safe_dump(contract,sort_keys=False))
  lock={'apiVersion':'delivery.re8ch.com/locked-helm-render/v1alpha1','kind':'LockedHelmRender','metadata':{'name':name},'spec':{'chart':chart_ref,'version':version,'releaseName':spec.get('releaseName',hn),'namespace':namespace,'releaseNamespace':spec['targetNamespace'],'values':'values.yaml','valuesDigest':sha(values_bytes),'renderedResources':'resources.yaml','renderedResourcesDigest':sha(body),'helmRelease':{'namespace':hr['metadata']['namespace'],'name':hn},'helmDeclarationDigest':digest(canonical(spec)),'imagePins':images,'deferred':deferred}}
  if hn=='birfucate-metering':lock['spec']['chartDigest']=chart_digest;lock['spec']['valuesFromEvidence']={'configMap':'flux-observability-system/tenant-mcp-image','key':'image','releaseRun':'https://github.com/re8ch/service-backend/actions/runs/41492069309','sourceRevision':'f084f0fd056c495b3cddc643618251e9101c8630'}
  (p/'source.yaml').write_text(yaml.safe_dump(lock,sort_keys=False))
  ledger.append({'release':name,'helmRelease':hn,'objects':len(objects),'deferred':deferred})
  print(name,len(objects),'runtime objects',len(deferred),'platform-owned')
(root/'operations/releases/helm-cohort.json').write_text(json.dumps(ledger,indent=2)+'\n')
