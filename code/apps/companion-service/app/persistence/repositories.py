"""SQLite repositories."""
from __future__ import annotations
from datetime import datetime
from app.domain.models import Deferral, FocusSession, FocusSessionStatus, InteractionIntensity, NudgeEvent, NudgeOutcome, QuietInterval, UserSettings
from app.persistence.database import Database

def _dt(v): return datetime.fromisoformat(v) if v is not None else None

class SQLiteSettingsRepository:
    def __init__(self, db: Database): self.db=db
    def save(self,s:UserSettings)->None:
        with self.db.connect() as c:
            c.execute("""INSERT INTO settings VALUES (1,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(singleton_id) DO UPDATE SET initial_nudge_minutes=excluded.initial_nudge_minutes,repeat_nudge_minutes=excluded.repeat_nudge_minutes,after_dismiss_cooldown_minutes=excluded.after_dismiss_cooldown_minutes,after_accept_cooldown_minutes=excluded.after_accept_cooldown_minutes,after_irritation_cooldown_minutes=excluded.after_irritation_cooldown_minutes,quiet_default_minutes=excluded.quiet_default_minutes,interaction_intensity=excluded.interaction_intensity,visual_lead_in_seconds=excluded.visual_lead_in_seconds,maximum_nudge_words=excluded.maximum_nudge_words,wellness_nudges_enabled=excluded.wellness_nudges_enabled,muted=excluded.muted""",(s.initial_nudge_minutes,s.repeat_nudge_minutes,s.after_dismiss_cooldown_minutes,s.after_accept_cooldown_minutes,s.after_irritation_cooldown_minutes,s.quiet_default_minutes,s.interaction_intensity.value,s.visual_lead_in_seconds,s.maximum_nudge_words,int(s.wellness_nudges_enabled),int(s.muted)))
    def get(self)->UserSettings:
        with self.db.connect() as c: r=c.execute("SELECT * FROM settings WHERE singleton_id=1").fetchone()
        if not r:return UserSettings()
        return UserSettings(r["initial_nudge_minutes"],r["repeat_nudge_minutes"],r["after_dismiss_cooldown_minutes"],r["after_accept_cooldown_minutes"],r["after_irritation_cooldown_minutes"],r["quiet_default_minutes"],InteractionIntensity(r["interaction_intensity"]),r["visual_lead_in_seconds"],r["maximum_nudge_words"],bool(r["wellness_nudges_enabled"]),bool(r["muted"]))

class SQLiteFocusSessionRepository:
    def __init__(self,db): self.db=db
    def save(self,s):
        with self.db.connect() as c:c.execute("""INSERT INTO focus_sessions VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET started_at=excluded.started_at,ended_at=excluded.ended_at,status=excluded.status,initial_nudge_at=excluded.initial_nudge_at,last_nudge_at=excluded.last_nudge_at,next_eligible_nudge_at=excluded.next_eligible_nudge_at,wellness_nudges_enabled=excluded.wellness_nudges_enabled""",(s.id,s.started_at.isoformat(),s.ended_at.isoformat() if s.ended_at else None,s.status.value,s.initial_nudge_at.isoformat() if s.initial_nudge_at else None,s.last_nudge_at.isoformat() if s.last_nudge_at else None,s.next_eligible_nudge_at.isoformat() if s.next_eligible_nudge_at else None,int(s.wellness_nudges_enabled)))
    def get_active(self):
        with self.db.connect() as c:r=c.execute("SELECT * FROM focus_sessions WHERE status='active' LIMIT 1").fetchone()
        return self._from(r) if r else None
    def get(self,id):
        with self.db.connect() as c:r=c.execute("SELECT * FROM focus_sessions WHERE id=?",(id,)).fetchone()
        return self._from(r) if r else None
    @staticmethod
    def _from(r): return FocusSession(id=r["id"],started_at=_dt(r["started_at"]),ended_at=_dt(r["ended_at"]),status=FocusSessionStatus(r["status"]),initial_nudge_at=_dt(r["initial_nudge_at"]),last_nudge_at=_dt(r["last_nudge_at"]),next_eligible_nudge_at=_dt(r["next_eligible_nudge_at"]),wellness_nudges_enabled=bool(r["wellness_nudges_enabled"]))

class SQLiteNudgeRepository:
    def __init__(self,db): self.db=db
    def save(self,e):
        with self.db.connect() as c:c.execute("""INSERT INTO nudge_events VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET outcome=excluded.outcome""",(e.id,e.focus_session_id,e.created_at.isoformat(),e.policy_reason,e.threshold_minutes,e.elapsed_minutes,e.interaction_intensity.value,e.expression_name,e.gesture_name,e.outcome.value))
    def get(self,id):
        with self.db.connect() as c:r=c.execute("SELECT * FROM nudge_events WHERE id=?",(id,)).fetchone()
        return self._from(r) if r else None
    def latest_for_session(self,sid):
        with self.db.connect() as c:r=c.execute("SELECT * FROM nudge_events WHERE focus_session_id=? ORDER BY created_at DESC LIMIT 1",(sid,)).fetchone()
        return self._from(r) if r else None
    def list_recent(self,limit=100):
        with self.db.connect() as c:rows=c.execute("SELECT * FROM nudge_events ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
        return [self._from(r) for r in rows]
    @staticmethod
    def _from(r): return NudgeEvent(id=r["id"],focus_session_id=r["focus_session_id"],created_at=_dt(r["created_at"]),policy_reason=r["policy_reason"],threshold_minutes=r["threshold_minutes"],elapsed_minutes=r["elapsed_minutes"],interaction_intensity=InteractionIntensity(r["interaction_intensity"]),expression_name=r["expression_name"],gesture_name=r["gesture_name"],outcome=NudgeOutcome(r["outcome"]))

class SQLiteDeferralRepository:
    def __init__(self,db): self.db=db
    def save(self,d):
        with self.db.connect() as c:c.execute("""INSERT INTO deferrals VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET duration_minutes=excluded.duration_minutes,expires_at=excluded.expires_at,status=excluded.status""",(d.id,d.nudge_event_id,d.created_at.isoformat(),d.duration_minutes,d.expires_at.isoformat(),d.status))
    def get_active(self,now):
        with self.db.connect() as c:r=c.execute("SELECT * FROM deferrals WHERE status='active' AND expires_at>? ORDER BY expires_at DESC LIMIT 1",(now.isoformat(),)).fetchone()
        return Deferral(id=r["id"],nudge_event_id=r["nudge_event_id"],created_at=_dt(r["created_at"]),duration_minutes=r["duration_minutes"],expires_at=_dt(r["expires_at"]),status=r["status"]) if r else None

class SQLiteQuietIntervalRepository:
    def __init__(self,db): self.db=db
    def save(self,q):
        with self.db.connect() as c:c.execute("""INSERT INTO quiet_intervals VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET ends_at=excluded.ends_at,status=excluded.status""",(q.id,q.started_at.isoformat(),q.ends_at.isoformat(),q.source,q.status))
    def get_active(self,now):
        with self.db.connect() as c:r=c.execute("SELECT * FROM quiet_intervals WHERE status='active' AND started_at<=? AND ends_at>? ORDER BY ends_at DESC LIMIT 1",(now.isoformat(),now.isoformat())).fetchone()
        return QuietInterval(id=r["id"],started_at=_dt(r["started_at"]),ends_at=_dt(r["ends_at"]),source=r["source"],status=r["status"]) if r else None
