from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.domain.clock import FixedClock
from app.main import create_app
from fastapi.testclient import TestClient

START = datetime(2026, 7, 11, 18, 0, tzinfo=UTC)


def client_for(tmp_path: Path, clock: FixedClock):
    return TestClient(create_app(database_path=tmp_path / "test.sqlite3", clock=clock))


def advance_to_nudge(client, clock):
    assert client.post("/focus-sessions").status_code == 201
    clock.set(START + timedelta(minutes=45))
    r = client.post("/interactions/evaluate", json={})
    assert r.status_code == 200 and r.json()["allowed"] is True
    assert client.post("/interactions/current/attention-complete").status_code == 200


def test_initial_status_is_idle(tmp_path):
    with client_for(tmp_path, FixedClock(START)) as c:
        r = c.get("/status")
        assert r.status_code == 200
        assert r.json()["interaction_state"] == "idle"


def test_start_and_duplicate_start(tmp_path):
    with client_for(tmp_path, FixedClock(START)) as c:
        assert c.post("/focus-sessions").status_code == 201
        r = c.post("/focus-sessions")
        assert r.status_code == 409


def test_policy_blocks_before_threshold(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        c.post("/focus-sessions")
        clock.set(START + timedelta(minutes=20))
        r = c.post("/interactions/evaluate", json={})
        assert r.json()["allowed"] is False
        assert r.json()["reason"] == "blocked_threshold_not_reached"
        assert c.get("/status").json()["interaction_state"] == "focusing"


def test_full_accept_flow(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        advance_to_nudge(c, clock)
        r = c.post("/interactions/current/accept")
        assert r.status_code == 200
        assert r.json()["interaction_state"] == "on_break"
        assert c.post("/focus-sessions/current/resume").json()["interaction_state"] == "focusing"


def test_ten_minute_deferral_is_persisted_and_blocks(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        advance_to_nudge(c, clock)
        r = c.post("/interactions/current/defer", json={"minutes": 10})
        assert r.status_code == 200
        assert r.json()["interaction_state"] == "deferred"
        clock.set(START + timedelta(minutes=50))
        assert c.post("/interactions/evaluate", json={}).status_code == 409
        clock.set(START + timedelta(minutes=56))
        r = c.post("/interactions/evaluate", json={})
        assert r.status_code == 200


def test_dismissal_enforces_cooldown(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        advance_to_nudge(c, clock)
        c.post("/interactions/current/dismiss")
        r = c.post("/interactions/evaluate", json={})
        assert r.json()["reason"] == "blocked_cooldown"


def test_quiet_mode_blocks_and_can_end(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        c.post("/focus-sessions")
        r = c.post("/interactions/current/quiet", json={"minutes": 60})
        assert r.json()["interaction_state"] == "quiet"
        r = c.post("/interactions/current/quiet/end")
        assert r.json()["interaction_state"] == "focusing"


def test_explanation_uses_recorded_facts(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        advance_to_nudge(c, clock)
        r = c.get("/interactions/current/explanation")
        assert r.status_code == 200
        assert r.json()["facts"]["elapsed_minutes"] == 45
        assert "posture" not in r.json()["message"].lower()


def test_settings_patch_and_validation(tmp_path):
    with client_for(tmp_path, FixedClock(START)) as c:
        r = c.patch("/settings", json={"initial_nudge_minutes": 30, "muted": True})
        assert r.status_code == 200
        assert r.json()["initial_nudge_minutes"] == 30 and r.json()["muted"] is True
        assert c.patch("/settings", json={"initial_nudge_minutes": 0}).status_code == 422


def test_events_endpoint_records_nudge(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        advance_to_nudge(c, clock)
        events = c.get("/events").json()
        assert len(events) == 1
        assert events[0]["policy_reason"] == "allowed_wellness_threshold"


def test_invalid_accept_returns_conflict_without_state_change(tmp_path):
    with client_for(tmp_path, FixedClock(START)) as c:
        c.post("/focus-sessions")
        r = c.post("/interactions/current/accept")
        assert r.status_code == 409
        assert c.get("/status").json()["interaction_state"] == "focusing"


def test_active_session_survives_app_restart(tmp_path):
    db = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=db, clock=clock)) as c:
        c.post("/focus-sessions")
    with TestClient(create_app(database_path=db, clock=clock)) as c:
        assert c.get("/status").json()["interaction_state"] == "focusing"


def test_stop_focus_works_during_quiet(tmp_path):
    with client_for(tmp_path, FixedClock(START)) as c:
        c.post("/focus-sessions")
        c.post("/interactions/current/quiet", json={"minutes": 60})
        r = c.post("/focus-sessions/current/stop")
        assert r.status_code == 200
        assert r.json()["interaction_state"] == "idle"


def test_ending_quiet_clears_active_interval(tmp_path):
    db = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=db, clock=clock)) as c:
        c.post("/focus-sessions")
        c.post("/interactions/current/quiet", json={"minutes": 60})
        status = c.post("/interactions/current/quiet/end").json()
        assert status["interaction_state"] == "focusing"
        assert status["active_quiet_interval"] is None
    with TestClient(create_app(database_path=db, clock=clock)) as c:
        status = c.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert status["active_quiet_interval"] is None


def test_quiet_mode_expires_without_manual_end(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        c.post("/focus-sessions")
        c.post("/interactions/current/quiet", json={"minutes": 10})
        clock.set(START + timedelta(minutes=11))
        status = c.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert status["active_quiet_interval"] is None
        assert c.post("/interactions/evaluate", json={}).status_code == 200


def test_stopping_focus_marks_pending_nudge_session_ended(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as c:
        advance_to_nudge(c, clock)
        status = c.post("/focus-sessions/current/stop").json()
        assert status["interaction_state"] == "idle"
        assert status["focus_session"] is None
        assert status["current_nudge"] is None
        assert c.get("/events").json()[0]["outcome"] == "session_ended"
