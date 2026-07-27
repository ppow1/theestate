"""Open WebUI-facing Grace operations adapter over the shared client contract."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from estate.core.grace_momentum_service import GraceMomentumClient, reference_command

MUTATIONS={"approve":"momentum.authorize","pause":"directive.pause","resume":"directive.resume","stop":"directive.stop","revoke":"directive.revoke"}
@dataclass
class GraceConversationCorrelation:
 conversation_id:str; message_id:str; objective_id:str|None=None; directive_id:str|None=None; commission_id:str|None=None; evaluation_id:str|None=None; approval_state:str="not_requested"; completion_receipt_id:str|None=None
 def links(self):
  out={"conversation":f"/open-webui/conversations/{self.conversation_id}?objective_id={self.objective_id or ''}&directive_id={self.directive_id or ''}"}
  if self.objective_id: out["objective"]=f"/estate/objectives/{self.objective_id}";out["lifecycle"]=f"/estate/objectives/{self.objective_id}/lifecycle?cursor=0"
  if self.directive_id: out["directive"]=f"/estate/directives/{self.directive_id}"
  return out

class OpenWebUIGraceOperations:
 def __init__(self,client:GraceMomentumClient): self.client=client;self.delivered:set[str]=set()
 def route(self,text:str,correlation:GraceConversationCorrelation,*,approved:bool=False)->dict[str,Any]:
  lower=text.lower().strip(); action=next((v for k,v in MUTATIONS.items() if lower==k or lower.startswith(k+" ")),None)
  if not action:return {"kind":"discussion" if "inspect" not in lower else "inspection","correlation":asdict(correlation),"links":correlation.links(),"message":"Discussion does not create operational work."}
  if not approved:return {"kind":"approval_required","requested_action":action,"correlation":asdict(correlation),"links":correlation.links()}
  cmd=reference_command(action,objective_id=correlation.objective_id or "",directive_id=correlation.directive_id,idempotency_key=f"{correlation.conversation_id}:{correlation.message_id}:{action}")
  result=self.client.send(cmd);return {"kind":"command","action":action,"result":result,"correlation":asdict(correlation),"links":correlation.links()}
 def deliver(self,event:dict[str,Any],correlation:GraceConversationCorrelation)->dict[str,Any]|None:
  required={"event_id","event_type","payload","position"}
  if not required<=event.keys():return {"kind":"malformed_event","links":correlation.links()}
  if event["event_id"] in self.delivered:return None
  self.delivered.add(event["event_id"]); payload=event["payload"]
  if event["event_type"]=="grace.receipt.recorded": correlation.completion_receipt_id=payload.get("receipt_id")
  return {"kind":"canonical_progress","event_type":event["event_type"],"payload":payload,"correlation":asdict(correlation),"links":correlation.links()}
 def refresh(self,correlation:GraceConversationCorrelation,cursor:int=0)->dict[str,Any]:
  availability=self.client.availability()
  if not availability.get("available", False): return {"kind":"unavailable","availability":availability,"links":correlation.links()}
  projection=self.client.lifecycle_projection(correlation.objective_id or "")
  replay=self.client.replay(cursor)
  delivered=[item for event in replay.get("events",[]) if (item:=self.deliver(event,correlation))]
  return {"kind":"refresh","availability":availability,"projection":projection,"cursor":replay.get("next_cursor",cursor),"events":delivered,"links":correlation.links()}
