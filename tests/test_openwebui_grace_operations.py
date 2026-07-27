from estate.core.grace_momentum_service import FakeGraceMomentumService,GraceMomentumClient,LoopbackGraceMomentumClient,TEST_IDENTITIES,reference_command
from estate.core.openwebui_grace_operations import OpenWebUIGraceOperations,GraceConversationCorrelation
def test_discussion_requires_no_action_and_approval_calls_contract(tmp_path):
 service=FakeGraceMomentumService(tmp_path); service.command(reference_command('momentum.authorize',objective_id='obj',directive_id='dir',idempotency_key='seed'),TEST_IDENTITIES['grace']);o=OpenWebUIGraceOperations(GraceMomentumClient(service,TEST_IDENTITIES['grace']));c=GraceConversationCorrelation('c','m','obj','dir')
 assert o.route('hello',c)['kind']=='discussion';assert o.route('pause',c)['kind']=='approval_required';assert o.route('pause',c,approved=True)['result']['record']['status']=='paused'
def test_canonical_delivery_deduplicates_and_links(tmp_path):
 o=OpenWebUIGraceOperations(GraceMomentumClient(FakeGraceMomentumService(tmp_path),TEST_IDENTITIES['grace']));c=GraceConversationCorrelation('c','m','obj','dir')
 e={'event_id':'e','event_type':'blocker.raised','position':1,'payload':{'responsible_office':'Engineering'}}
 assert o.deliver(e,c)['links']['objective']=='/estate/objectives/obj';assert o.deliver(e,c) is None;assert o.deliver({},c)['kind']=='malformed_event'

def test_refresh_uses_health_and_readiness_and_persists_replay_state(tmp_path):
 service=FakeGraceMomentumService(tmp_path)
 service.command(reference_command('momentum.authorize',objective_id='obj',directive_id='dir',idempotency_key='seed'),TEST_IDENTITIES['grace'])
 c=GraceConversationCorrelation('conversation','message','obj','dir')
 root=tmp_path/'openwebui'
 first=OpenWebUIGraceOperations(GraceMomentumClient(service,TEST_IDENTITIES['grace']),state_root=root).refresh(c)
 assert first['kind']=='refresh' and first['availability']['health']['healthy'] is True
 second=OpenWebUIGraceOperations(GraceMomentumClient(service,TEST_IDENTITIES['grace']),state_root=root).refresh(c)
 assert second['events']==[] and second['cursor']==first['cursor']

def test_refresh_fails_closed_for_malformed_or_unavailable_availability(tmp_path):
 class Client:
  def availability(self): return {'available': True}
  def lifecycle_projection(self, objective_id): return {}
  def replay(self, cursor): return {'events': [], 'next_cursor': cursor}
  def send(self, command): return {}
 o=OpenWebUIGraceOperations(Client(),state_root=tmp_path/'state')
 assert o.refresh(GraceConversationCorrelation('c','m'))['kind']=='unavailable'

def test_loopback_client_is_canonical_production_surface():
 client=LoopbackGraceMomentumClient('http://127.0.0.1:8765', {'iss':'estate-control','sub':'grace','office':'Grace','authority_source':'test','active':True})
 assert client.base_url=='http://127.0.0.1:8765'

def test_inspection_does_not_mutate_and_approval_is_required(tmp_path):
 service=FakeGraceMomentumService(tmp_path)
 o=OpenWebUIGraceOperations(GraceMomentumClient(service,TEST_IDENTITIES['grace']))
 c=GraceConversationCorrelation('c','m','obj','dir')
 assert o.route('inspect',c)['kind']=='inspection'
 assert o.route('revoke',c)['kind']=='approval_required'
 assert not (tmp_path/'runtime'/'production'/'grace_momentum'/'events.jsonl').exists()
