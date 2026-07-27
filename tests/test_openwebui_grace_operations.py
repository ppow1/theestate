from estate.core.grace_momentum_service import FakeGraceMomentumService,GraceMomentumClient,TEST_IDENTITIES,reference_command
from estate.core.openwebui_grace_operations import OpenWebUIGraceOperations,GraceConversationCorrelation
def test_discussion_requires_no_action_and_approval_calls_contract(tmp_path):
 service=FakeGraceMomentumService(tmp_path); service.command(reference_command('momentum.authorize',objective_id='obj',directive_id='dir',idempotency_key='seed'),TEST_IDENTITIES['grace']);o=OpenWebUIGraceOperations(GraceMomentumClient(service,TEST_IDENTITIES['grace']));c=GraceConversationCorrelation('c','m','obj','dir')
 assert o.route('hello',c)['kind']=='discussion';assert o.route('pause',c)['kind']=='approval_required';assert o.route('pause',c,approved=True)['result']['record']['status']=='paused'
def test_canonical_delivery_deduplicates_and_links(tmp_path):
 o=OpenWebUIGraceOperations(GraceMomentumClient(FakeGraceMomentumService(tmp_path),TEST_IDENTITIES['grace']));c=GraceConversationCorrelation('c','m','obj','dir')
 e={'event_id':'e','event_type':'blocker.raised','position':1,'payload':{'responsible_office':'Engineering'}}
 assert o.deliver(e,c)['links']['objective']=='/estate/objectives/obj';assert o.deliver(e,c) is None;assert o.deliver({},c)['kind']=='malformed_event'
