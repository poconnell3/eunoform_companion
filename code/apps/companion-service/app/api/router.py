from __future__ import annotations
from dataclasses import asdict
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from app.api.schemas import ActionResponse, DeferRequest, EvaluateRequest, ExplanationResponse, PolicyResponse, QuietRequest, ReduceFrequencyRequest, SettingsPatch, StatusResponse
from app.domain.interaction_state import InvalidTransitionError
from app.services.companion_application_service import CompanionApplicationService

router=APIRouter()
def get_service(request:Request)->CompanionApplicationService: return request.app.state.companion_service
Service=Annotated[CompanionApplicationService,Depends(get_service)]
def serialize(value):
    if value is None:return None
    data=asdict(value)
    return {k:(v.value if hasattr(v,"value") else v) for k,v in data.items()}
def status_payload(service):
    s=service.status(); return {"interaction_state":s["interaction_state"].value,"elapsed_minutes":s["elapsed_minutes"],"focus_session":serialize(s["focus_session"]),"active_deferral":serialize(s["active_deferral"]),"active_quiet_interval":serialize(s["active_quiet_interval"]),"current_nudge":serialize(s["current_nudge"]),"settings":serialize(s["settings"])}
def conflict(exc): raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=str(exc)) from exc

@router.get("/status",response_model=StatusResponse)
def read_status(service:Service): return status_payload(service)
@router.post("/focus-sessions",status_code=201,response_model=StatusResponse)
def start_focus(service:Service):
    try: service.start_focus(); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.get("/focus-sessions/current",response_model=StatusResponse)
def current_focus(service:Service): return status_payload(service)
@router.post("/focus-sessions/current/stop",response_model=StatusResponse)
def stop_focus(service:Service):
    try: service.stop_focus(); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/focus-sessions/current/resume",response_model=StatusResponse)
def resume_focus(service:Service):
    try: service.resume_focus(); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/evaluate",response_model=PolicyResponse)
def evaluate(body:EvaluateRequest,service:Service):
    try:
        d=service.evaluate(body.explicit_reminder_due); return {"allowed":d.allowed,"reason":d.reason.value,"elapsed_minutes":d.elapsed_minutes,"threshold_minutes":d.threshold_minutes,"next_eligible_at":d.next_eligible_at}
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/current/attention-complete",response_model=StatusResponse)
def attention_complete(service:Service):
    try: service.attention_complete(); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/current/accept",response_model=StatusResponse)
def accept(service:Service):
    try: service.accept(); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/current/defer",response_model=StatusResponse)
def defer(body:DeferRequest,service:Service):
    try: service.defer(body.minutes); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/current/dismiss",response_model=StatusResponse)
def dismiss(service:Service):
    try: service.dismiss(); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/current/quiet",response_model=StatusResponse)
def quiet(body:QuietRequest,service:Service):
    try: service.quiet(body.minutes); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/current/quiet/end",response_model=StatusResponse)
def end_quiet(service:Service):
    try: service.exit_quiet(); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.post("/interactions/current/reduce-frequency",response_model=StatusResponse)
def reduce_frequency(body:ReduceFrequencyRequest,service:Service):
    try: service.reduce_frequency(body.additional_minutes); return status_payload(service)
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.get("/interactions/current/explanation",response_model=ExplanationResponse)
def explanation(service:Service):
    try:
        facts,text=service.explanation(); return {"message":text,"facts":serialize(facts)}
    except (ValueError,InvalidTransitionError) as e: conflict(e)
@router.get("/settings")
def read_settings(service:Service): return serialize(service.settings)
@router.patch("/settings")
def patch_settings(body:SettingsPatch,service:Service):
    try:return serialize(service.patch_settings(body.model_dump(exclude_unset=True)))
    except ValueError as e: conflict(e)
@router.get("/events")
def read_events(service:Service,limit:int=Query(default=100,ge=1,le=500)): return [serialize(e) for e in service.events(limit)]
