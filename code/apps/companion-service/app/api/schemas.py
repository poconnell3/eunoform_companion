from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.domain.models import InteractionIntensity

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class DeferRequest(StrictModel):
    minutes: int = Field(gt=0, le=1440)
class QuietRequest(StrictModel):
    minutes: int = Field(gt=0, le=10080)
class ReduceFrequencyRequest(StrictModel):
    additional_minutes: int = Field(default=15, gt=0, le=240)
class EvaluateRequest(StrictModel):
    explicit_reminder_due: bool = False
class SettingsPatch(StrictModel):
    initial_nudge_minutes: int | None = Field(default=None, gt=0, le=1440)
    repeat_nudge_minutes: int | None = Field(default=None, gt=0, le=1440)
    after_dismiss_cooldown_minutes: int | None = Field(default=None, gt=0, le=1440)
    after_accept_cooldown_minutes: int | None = Field(default=None, gt=0, le=1440)
    after_irritation_cooldown_minutes: int | None = Field(default=None, gt=0, le=10080)
    quiet_default_minutes: int | None = Field(default=None, gt=0, le=10080)
    interaction_intensity: InteractionIntensity | None = None
    visual_lead_in_seconds: int | None = Field(default=None, ge=0, le=60)
    maximum_nudge_words: int | None = Field(default=None, gt=0, le=100)
    wellness_nudges_enabled: bool | None = None
    muted: bool | None = None

class ActionResponse(BaseModel):
    interaction_state: str
    message: str
class PolicyResponse(BaseModel):
    allowed: bool
    reason: str
    elapsed_minutes: int
    threshold_minutes: int
    next_eligible_at: datetime | None
class StatusResponse(BaseModel):
    interaction_state: str
    elapsed_minutes: int
    focus_session: dict | None
    active_deferral: dict | None
    active_quiet_interval: dict | None
    current_nudge: dict | None
    settings: dict
class ExplanationResponse(BaseModel):
    message: str
    facts: dict
