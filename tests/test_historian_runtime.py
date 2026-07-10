import pytest
from pathlib import Path

from estate.core.historian import create_event, correct_event, generate_timeline, historical_query, inspect_source, summarize


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_timeline_chronology_citations_and_filters(tmp_path):
    write(tmp_path/'docs'/'decision.md', '# Decision\naccepted timeline source')
    event = create_event(root=tmp_path, date='2026-07-01', title='Decision accepted', office='archives', project='historian', resident='alfred', artifact_type='decision', significance='high', source_paths=['docs/decision.md'], claims=[{'text':'The decision artifact exists as an accepted source fact.', 'claim_type':'source_fact', 'citation_paths':['docs/decision.md']}])
    timeline = generate_timeline(root=tmp_path, office='archives', significance='high')
    assert timeline['uses_knowledge_index'] is True
    assert [e['event_id'] for e in timeline['events']] == [event['event_id']]
    assert timeline['events'][0]['citations'][0]['source_hash']
    assert (tmp_path/'runtime'/'office'/'historian_timeline.json').exists()


def test_duplicate_event_handling_and_correction_preserves_history(tmp_path):
    write(tmp_path/'operations'/'validation'/'receipt.md', '# Receipt\nvalidated')
    kwargs = dict(root=tmp_path, date='2026-07-02', title='Validation receipt', source_paths=['operations/validation/receipt.md'], claims=[{'text':'A validation receipt was recorded.', 'citation_paths':['operations/validation/receipt.md']}])
    first = create_event(**kwargs)
    with pytest.raises(ValueError, match='duplicate active'):
        create_event(**kwargs)
    new = correct_event(first['event_id'], {'title':'Validation receipt corrected'}, 'title clarity', root=tmp_path)
    store = generate_timeline(root=tmp_path)
    assert [e['event_id'] for e in store['events']] == [new['event_id']]
    assert new['corrects'] == first['event_id']


def test_source_disappearance_and_summary_boundaries(tmp_path):
    src = tmp_path/'archive'/'institutional_memory'/'origin.md'
    write(src, '# Origin\nsource')
    event = create_event(root=tmp_path, date='2026-07-03', title='Origin noted', source_paths=['archive/institutional_memory/origin.md'], claims=[
        {'text':'The origin note exists.', 'claim_type':'source_fact', 'citation_paths':['archive/institutional_memory/origin.md']},
        {'text':'It may represent institutional continuity.', 'claim_type':'interpretation', 'citation_paths':['archive/institutional_memory/origin.md']},
        {'text':'Acceptance status remains unresolved.', 'claim_type':'uncertainty', 'citation_paths':['archive/institutional_memory/origin.md']},
    ])
    assert inspect_source('archive/institutional_memory/origin.md', root=tmp_path)['exists'] is True
    summary = summarize([event])
    assert summary['source_facts'] and summary['interpretations'] and summary['unresolved_uncertainty']
    src.unlink()
    assert inspect_source('archive/institutional_memory/origin.md', root=tmp_path)['exists'] is False
    with pytest.raises(ValueError, match='citation source disappeared'):
        correct_event(event['event_id'], {'title':'Cannot correct against missing source'}, 'missing source check', root=tmp_path)


def test_historical_query_reuses_knowledge_index(tmp_path):
    write(tmp_path/'constitution'/'constitution.md', '# Constitution\nconstitutional change')
    create_event(root=tmp_path, date='2026-07-04', title='Constitution noted', office='steward', source_paths=['constitution/constitution.md'], claims=[{'text':'The constitution artifact is present.', 'citation_paths':['constitution/constitution.md']}])
    result = historical_query('constitution', root=tmp_path, office='steward')
    assert result['events'][0]['title'] == 'Constitution noted'
    assert result['knowledge_index']['results']
