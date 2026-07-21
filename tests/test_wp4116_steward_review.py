import copy, json
from pathlib import Path
import pytest
from estate.visual_bible import (ValidationError, create_rollback, validate_anchor, validate_approval,
 validate_comparison_manifest, validate_note, validate_queue, validate_recognition_test,
 validate_revision_packet, validate_review_transition)
ROOT=Path(__file__).resolve().parents[1]
P={"created_at":"2026-07-21T00:00:00Z","created_by":"worker","source_ids":["asset-1"],"content_hash":"sha256:abc","lineage":["draft"],"revision":"1"}
def transition(a='draft',b='pending_steward_review'):
 return {"transition_id":"t1","subject_id":"a1","from_state":a,"to_state":b,"occurred_at":"2026-07-21T00:00:00Z","reviewer_id":"pat","reviewer_authority":"Steward","reason":"exact decision","source_asset_ids":["a1"],"provenance":P}
def manifest():
 return {"manifest_id":"m1","resident_ids":["evelyn"],"comparison_type":"three_variant","layout":{"vertical_stack":True,"angle_order":["front","front_three_quarter","side","rear_three_quarter","rear"],"labels_outside_image":True,"originals_zoomable":True},"assets":[{"id":"A"},{"id":"B"},{"id":"C"}],"intended_variables":["hips"],"fixed_variables":["identity","camera"],"difference_summary":"Only hips differ.","review_dimensions":["technical","emotional"],"audience_scope":"internal","provenance":P}
def approval(i='ap1',subject='a1'):
 return {"approval_id":i,"subject_ids":[subject],"approved_version":"1","approved_at":"2026-07-21T00:00:00Z","approver_id":"pat","approver_authority":"Steward","explicit_approval":True,"steward_note_ids":["n1"],"preserved_elements":["eye warmth"],"scope":"internal","provenance":P}
def test_state_authority_and_no_automatic_canon():
 validate_review_transition(transition())
 x=transition('pending_steward_review','canonical');x['approval_record_id']='ap1';validate_review_transition(x)
 x['reviewer_authority']='automation'
 with pytest.raises(ValidationError,match='Steward'):validate_review_transition(x)
 with pytest.raises(ValidationError,match='invalid review transition'):validate_review_transition(transition('draft','canonical'))
def test_exact_note_is_preserved_with_targets_and_provenance():
 d={"note_id":"n1","resident_id":"evelyn","recorded_at":"now","steward_id":"pat","authority":"Steward","exact_text":"preserve this exact eye warmth","exact_text_preserved":True,"normalized_summary":"Preserve warmth.","target_refs":[{"asset_id":"a1","angle":"front"}],"dimension":"both","provenance":P};validate_note(d)
 d['exact_text_preserved']=False
 with pytest.raises(ValidationError,match='exact Steward'):validate_note(d)
def test_queue_and_controlled_manifest():
 q={"queue_id":"q1","audience_scope":"internal","created_at":"now","items":[{"queue_item_id":"i","subject_id":"a1","subject_type":"asset","review_state":"pending_steward_review","priority":"normal","submitted_at":"now","manifest_id":"m1"}],"provenance":P};validate_queue(q)
 d=manifest();validate_comparison_manifest(d);d['fixed_variables']=['hips']
 with pytest.raises(ValidationError,match='overlap'):validate_comparison_manifest(d)
def test_360_requires_aligned_angles():
 d=manifest();d['comparison_type']='turnaround_360';d['assets']=[{'angles':d['layout']['angle_order']}];validate_comparison_manifest(d)
 d['assets'][0]['angles']=['front']
 with pytest.raises(ValidationError,match='five aligned'):validate_comparison_manifest(d)
def test_actionable_revision_packet_and_evelyn_example():
 ex=json.loads((ROOT/'data/visual_bibles/residents/evelyn/internal/review/nonbinding_example.json').read_text());assert ex['example_status']=='nonbinding_unreviewed_example';validate_anchor(ex['anchor_review']);validate_revision_packet(ex['revision_packet'])
 d=copy.deepcopy(ex['revision_packet']);d['variables_to_hold_fixed'].append('resident_to_furniture_scale')
 with pytest.raises(ValidationError,match='overlap'):validate_revision_packet(d)
def test_hidden_caption_group_recognition():
 d={"test_id":"r1","group_asset_id":"g1","expected_resident_ids":["evelyn","ingrid"],"captions_hidden":True,"steward_responses":[{"exact_text":"Evelyn, Ingrid"}],"recognition_result":"pass","review_state":"provisionally_approved","reviewer_authority":"Steward","provenance":P};validate_recognition_test(d)
 d['captions_hidden']=False
 with pytest.raises(ValidationError,match='hidden'):validate_recognition_test(d)
def test_explicit_approval_and_forward_history_rollback():
 old,new=approval('ap0','a0'),approval('ap1','a1');validate_approval(new);r=create_rollback(new,old,steward_id='pat',reason='restore prior accepted face',occurred_at='now');assert r['history_preserved'] and not r['automatic_deletion']
 new['explicit_approval']=False
 with pytest.raises(ValidationError,match='explicit'):validate_approval(new)
def test_schemas_are_valid():
 js=pytest.importorskip('jsonschema')
 for path in (ROOT/'data/schemas/visual_bible/steward_review').glob('*.json'):js.Draft202012Validator.check_schema(json.loads(path.read_text()))
