import json
from pathlib import Path

from estate.core.estate_discovery_engine import apply, diff, inspect, scan


def cfg(root, roots=None):
    p=root/'config/discovery'; p.mkdir(parents=True)
    (p/'approved_roots.json').write_text(json.dumps({'approved_roots': roots or [{'path':'approved','owner':'test'}]}), encoding='utf-8')


def test_move_duplicate_stale_and_idempotent_rediscovery(tmp_path):
    cfg(tmp_path); d=tmp_path/'approved'; d.mkdir(); (d/'a.md').write_text('same'); (d/'copy.md').write_text('same')
    first=apply(tmp_path); assert first['applied']; assert first['diff']['added'] == ['approved/a.md','approved/copy.md']; assert first['duplicates']
    (d/'b.md').write_text((d/'a.md').read_text()); (d/'a.md').unlink()
    second=diff(tmp_path); assert {'from':'approved/a.md','to':'approved/b.md','content_hash':second['items'][0]['content_hash']} in second['diff']['moved']; assert 'approved/a.md' in second['diff']['missing']
    apply(tmp_path); third=apply(tmp_path); assert third['diff']['added'] == [] and third['diff']['changed'] == [] and third['diff']['missing'] == []


def test_ignored_protected_and_malformed_artifacts(tmp_path):
    cfg(tmp_path); d=tmp_path/'approved'; (d/'node_modules').mkdir(parents=True); (d/'private').mkdir(); (d/'ok.md').write_text('# ok'); (d/'node_modules/x.md').write_text('ignore'); (d/'private/secret.md').write_text('no')
    out=scan(tmp_path); paths=[i['canonical_path'] for i in out['items']]
    assert paths == ['approved/ok.md']
    (d/'bad.json').write_bytes(b'\xff')
    out=scan(tmp_path)
    assert any(i['canonical_path']=='approved/bad.json' for i in out['items'])


def test_inspect_and_changed_detection(tmp_path):
    cfg(tmp_path); d=tmp_path/'approved'; d.mkdir(); f=d/'artifact.md'; f.write_text('one')
    applied=apply(tmp_path); item=applied['items'][0]
    assert inspect(tmp_path, discovery_id=item['discovery_id'])['match_count'] == 1
    f.write_text('two')
    out=diff(tmp_path); assert out['diff']['changed'] == ['approved/artifact.md']
