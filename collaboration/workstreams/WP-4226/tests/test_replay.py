import copy, json, os, subprocess, sys
from pathlib import Path
import pytest
from estate.core.engineering_campaign_replay import *
from estate.core.engineering_campaign_replay import _without_hash
ROOT=Path(__file__).parents[1]; FIX=ROOT/'fixtures'; NOW='2026-07-26T00:00:00Z'
def sources(name='healthy_campaign'): return json.loads((FIX/f'{name}.json').read_text())
def snap(name='healthy_campaign'): return create_snapshot(sources(name),generated_at=NOW)
def test_snapshot_is_deterministic_and_repeated(): assert snap()==snap()
def test_input_and_provenance_preserved_without_mutation():
 x=sources(); before=copy.deepcopy(x); s=create_snapshot(x,generated_at=NOW); assert x==before and s['source_records']==x and len(s['provenance']['source_hashes'])==6
def test_hashing_and_tamper_rejection():
 s=snap(); assert s['deterministic_content_hash']==content_hash(_without_hash(s)); s['freshness']='bad'
 with pytest.raises(ReplayError,match='hash'): validate_snapshot(s)
def test_replay_equivalence_and_determinism():
 s=snap(); assert replay(s)==replay(s); assert replay(s)['dashboard']==s['source_records']['dashboard']
def test_comparison_reports_captured_changes():
 a=snap(); raw=sources('analytics_evolution'); raw['engineering_queue']['candidates'][0]['priority']['score']=20; raw['engineering_queue']['candidates'].append({'item_identifier':'WP-2','dependencies':['WP-1']}); b=create_snapshot(raw,generated_at='2026-07-27T00:00:00Z'); c=compare(a,b)
 assert c['new_work']==['WP-2'] and c['changed_priorities']==['WP-1'] and c['analytics_deltas']['engineering_throughput']==2
def test_malformed_and_unsupported_rejected():
 for name in ('malformed_snapshot','incompatible_schema'):
  with pytest.raises(ReplayError): validate_snapshot(load(FIX/f'{name}.json'))
def test_read_only_boundary_and_copies():
 s=snap(); out=replay(s); out['dashboard'].clear(); assert s['source_records']['dashboard']
def test_history_stable(): assert history([snap(),snap()])==history([snap(),snap()])
def test_cli_commands(tmp_path):
 source=FIX/'healthy_campaign.json'; shot=tmp_path/'s.json'
 cmd=[sys.executable,'-m','estate.cli.engineering_campaign_replay','snapshot',str(source),'--generated-at',NOW]
 env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[4]/'src')}; r=subprocess.run(cmd,text=True,capture_output=True,check=True,env=env); shot.write_text(r.stdout)
 for op in ('validate','replay','explain'):
  assert subprocess.run([sys.executable,'-m','estate.cli.engineering_campaign_replay',op,str(shot)],capture_output=True,env=env).returncode==0
 assert subprocess.run([sys.executable,'-m','estate.cli.engineering_campaign_replay','list',str(shot)],capture_output=True,env=env).returncode==0
