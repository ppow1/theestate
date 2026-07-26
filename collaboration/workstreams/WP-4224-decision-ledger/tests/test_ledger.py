import copy, json, subprocess, sys
from pathlib import Path
import pytest

ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT))
from decision_ledger.ledger import LedgerError, append_decision, create_ledger, query, validate_ledger

def fixture(name): return json.loads((ROOT/'fixtures'/f'{name}.json').read_text())
def ledger(name='accepted_recommendation'): return create_ledger(fixture(name),generated_at='2026-07-26T00:00:00Z')
def decide(value,state='acknowledged',rid='rec-accepted'):
 return append_decision(value,recommendation_id=rid,state=state,reviewer='Steward',review_timestamp='2026-07-26T01:00:00Z',rationale='Recorded for advisory review',comments='No execution',linked_snapshot='snapshot-001',linked_work_packages=['WP-4224'],linked_validation_evidence=['test-report'])

def test_deterministic_creation_hash_and_repeated_execution():
    assert ledger()==ledger()
    assert validate_ledger(ledger())==[]

def test_append_only_and_input_immutable():
    original=ledger(); before=copy.deepcopy(original); updated=decide(original)
    assert original==before and not original['decisions']
    assert len(updated['decisions'])==len(updated['audit_records'])==1

def test_history_chain_lineage_supersession_and_queries():
    value=decide(ledger()); value=append_decision(value,recommendation_id='rec-accepted',state='superseded',reviewer='Steward',review_timestamp='2026-07-26T02:00:00Z',rationale='new published advice')
    assert len(query(value,'history','rec-accepted'))==2
    assert query(value,'superseded')[0]['recommendation_identifier']=='rec-accepted'
    assert len(query(value,'lineage')[0]['decision_hashes'])==2
    assert query(value,'trends')['superseded']==1

def test_all_review_outcomes_and_unresolved_expired():
    value=ledger('deferred_recommendation')
    value=append_decision(value,recommendation_id='rec-deferred',state='deferred',reviewer='S',review_timestamp='t',rationale='later')
    assert query(value,'unresolved')
    value=append_decision(value,recommendation_id='rec-deferred',state='expired',reviewer='S',review_timestamp='t2',rationale='stale')
    assert query(value,'expired') and not query(value,'unresolved')

@pytest.mark.parametrize('name', ['duplicate_recommendation','malformed_recommendation','unsupported_schema_version'])
def test_invalid_published_inputs(name):
    with pytest.raises(LedgerError): create_ledger(fixture(name))

def test_tampering_and_bad_state_rejected():
    value=ledger(); value['recommendations'][0]['score']=999
    with pytest.raises(LedgerError): validate_ledger(value)
    with pytest.raises(LedgerError): decide(ledger(),state='executed')

def test_queries_are_read_only():
    value=ledger(); result=query(value,'current'); result[0]['score']=999
    assert value['recommendations'][0]['score']!=999

def test_cli_behavior_and_file_is_unchanged(tmp_path):
    path=tmp_path/'ledger.json'; path.write_text(json.dumps(ledger()))
    before=path.read_bytes()
    for args in [('recommendations',),('history',),('show','rec-accepted'),('compare','rec-accepted','rec-accepted'),('lineage',),('validate',),('explain','rec-accepted')]:
        run=subprocess.run([sys.executable,str(ROOT/'ledger_cli.py'),str(path),*args],capture_output=True,text=True)
        assert run.returncode==0,run.stderr
        json.loads(run.stdout)
    assert path.read_bytes()==before
