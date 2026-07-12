import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.domain.clock import FixedClock
from app.domain.models import Deferral
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


def assert_timed_state_consistent(status: dict) -> None:
    state = status["interaction_state"]
    active_quiet = status["active_quiet_interval"]
    active_deferral = status["active_deferral"]
    if state == "quiet":
        assert active_quiet is not None
    else:
        assert active_quiet is None
    if state == "deferred":
        assert active_deferral is not None
    elif state != "quiet":
        assert active_deferral is None


def persisted_status(database_path: Path, table: str) -> str:
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(f"SELECT status FROM {table} LIMIT 1").fetchone()
    assert row is not None
    return row[0]


def wait_for_state(client: TestClient, expected: str, timeout: float = 1.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get("/status").json()
        if status["interaction_state"] == expected:
            return status
        time.sleep(0.01)
    raise AssertionError(f"Timed out waiting for state {expected!r}.")


def test_initial_status_is_idle(tmp_path):
    with client_for(tmp_path, FixedClock(START)) as c:
        r = c.get("/status")
        assert r.status_code == 200
        assert r.json()["interaction_state"] == "idle"


def test_scheduler_automatically_starts_due_attention(tmp_path):
    clock = FixedClock(START)
    app = create_app(
        database_path=tmp_path / "automatic.sqlite3",
        clock=clock,
        scheduler_interval_seconds=0.01,
    )
    with TestClient(app) as client:
        started = client.post("/focus-sessions").json()
        assert datetime.fromisoformat(started["next_evaluation_at"]) == START + timedelta(
            minutes=45
        )
        clock.set(START + timedelta(minutes=45))
        status = wait_for_state(client, "attracting_attention")
        assert status["current_nudge"]["policy_reason"] == "allowed_wellness_threshold"


def test_scheduler_turns_expired_deferral_into_explicit_reminder(tmp_path):
    clock = FixedClock(START)
    app = create_app(
        database_path=tmp_path / "deferral.sqlite3",
        clock=clock,
        scheduler_interval_seconds=0.01,
    )
    with TestClient(app) as client:
        client.post("/focus-sessions")
        clock.set(START + timedelta(minutes=45))
        wait_for_state(client, "attracting_attention")
        client.post("/interactions/current/attention-complete")
        deferred = client.post("/interactions/current/defer", json={"minutes": 10}).json()
        assert datetime.fromisoformat(deferred["next_evaluation_at"]) == START + timedelta(
            minutes=55
        )
        clock.set(START + timedelta(minutes=56))
        status = wait_for_state(client, "attracting_attention")
        assert status["current_nudge"]["policy_reason"] == "allowed_explicit_reminder"


def test_scheduler_can_be_disabled_for_deterministic_hosts(tmp_path):
    clock = FixedClock(START)
    app = create_app(
        database_path=tmp_path / "disabled.sqlite3",
        clock=clock,
        scheduler_enabled=False,
    )
    with TestClient(app) as client:
        client.post("/focus-sessions")
        clock.set(START + timedelta(minutes=45))
        time.sleep(0.03)
        assert client.get("/status").json()["interaction_state"] == "focusing"


def test_scheduler_rejects_non_positive_interval(tmp_path):
    with pytest.raises(ValueError, match="greater than zero"):
        create_app(
            database_path=tmp_path / "invalid.sqlite3",
            scheduler_interval_seconds=0,
        )


def test_scheduler_recovers_expired_deferral_after_restart(tmp_path):
    database_path = tmp_path / "restart.sqlite3"
    clock = FixedClock(START)
    with TestClient(
        create_app(database_path=database_path, clock=clock, scheduler_enabled=False)
    ) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 10})
        clock.set(START + timedelta(minutes=56))
        assert client.get("/status").json()["interaction_state"] == "focusing"
    with TestClient(
        create_app(
            database_path=database_path,
            clock=clock,
            scheduler_interval_seconds=0.01,
        )
    ) as client:
        status = wait_for_state(client, "attracting_attention")
        assert status["current_nudge"]["policy_reason"] == "allowed_explicit_reminder"


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


def test_stopping_focus_during_quiet_ends_quiet_interval(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        client.post("/focus-sessions")
        client.post("/interactions/current/quiet", json={"minutes": 60})
        status = client.post("/focus-sessions/current/stop").json()
        assert status["interaction_state"] == "idle"
        assert status["focus_session"] is None
        assert_timed_state_consistent(status)
    assert persisted_status(database_path, "quiet_intervals") == "cancelled"
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        assert_timed_state_consistent(client.get("/status").json())
        client.post("/focus-sessions")
        clock.set(START + timedelta(minutes=45))
        decision = client.post("/interactions/evaluate", json={}).json()
        assert decision["allowed"] is True
        assert decision["reason"] != "blocked_quiet_mode"


def test_stopping_focus_during_deferral_ends_deferral(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 10})
        status = client.post("/focus-sessions/current/stop").json()
        assert status["interaction_state"] == "idle"
        assert status["focus_session"] is None
        assert_timed_state_consistent(status)
    assert persisted_status(database_path, "deferrals") == "cancelled"
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        assert_timed_state_consistent(client.get("/status").json())


def test_deferral_from_ended_session_does_not_block_new_session(tmp_path):
    clock = FixedClock(START)
    with client_for(tmp_path, clock) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 60})
        client.post("/focus-sessions/current/stop")
        client.post("/focus-sessions")
        clock.set(START + timedelta(minutes=90))
        response = client.post("/interactions/evaluate", json={})
        assert response.status_code == 200
        assert response.json()["allowed"] is True
        assert response.json()["reason"] != "blocked_active_deferral"


def test_status_reconciles_expired_deferral(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 10})
        clock.set(START + timedelta(minutes=56))
        status = client.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert_timed_state_consistent(status)
    assert persisted_status(database_path, "deferrals") == "expired"


def test_natural_quiet_expiration_is_persisted(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        client.post("/focus-sessions")
        client.post("/interactions/current/quiet", json={"minutes": 10})
        clock.set(START + timedelta(minutes=11))
        status = client.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert_timed_state_consistent(status)
    assert persisted_status(database_path, "quiet_intervals") == "expired"


def test_restart_restores_deferral_beneath_quiet(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 30})
        client.post("/interactions/current/quiet", json={"minutes": 10})
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        status = client.get("/status").json()
        assert status["interaction_state"] == "quiet"
        assert status["active_quiet_interval"] is not None
        assert status["active_deferral"] is not None
        assert_timed_state_consistent(status)
        clock.set(START + timedelta(minutes=56))
        status = client.get("/status").json()
        assert status["interaction_state"] == "deferred"
        assert status["active_quiet_interval"] is None
        assert status["active_deferral"] is not None
        assert_timed_state_consistent(status)
        clock.set(START + timedelta(minutes=76))
        status = client.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert_timed_state_consistent(status)


def test_deferral_can_expire_beneath_active_quiet(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 10})
        client.post("/interactions/current/quiet", json={"minutes": 30})
        clock.set(START + timedelta(minutes=56))
        status = client.get("/status").json()
        assert status["interaction_state"] == "quiet"
        assert status["active_quiet_interval"] is not None
        assert status["active_deferral"] is None
        assert persisted_status(database_path, "deferrals") == "expired"
        assert_timed_state_consistent(status)
        clock.set(START + timedelta(minutes=76))
        status = client.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert_timed_state_consistent(status)


def test_cancelled_deferral_preserves_original_expiration(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 30})
        with sqlite3.connect(database_path) as connection:
            original_expiration = connection.execute("SELECT expires_at FROM deferrals").fetchone()[
                0
            ]
        client.post("/focus-sessions/current/stop")
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM deferrals").fetchone()
    assert row is not None
    assert row["status"] == "cancelled"
    assert row["expires_at"] == original_expiration
    assert row["expires_at"] > row["created_at"]
    assert row["duration_minutes"] == 30
    restored = Deferral(
        id=row["id"],
        nudge_event_id=row["nudge_event_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        duration_minutes=row["duration_minutes"],
        expires_at=datetime.fromisoformat(row["expires_at"]),
        status=row["status"],
    )
    assert restored.status == "cancelled"


def test_restart_during_plain_quiet_returns_to_focusing(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        client.post("/focus-sessions")
        client.post("/interactions/current/quiet", json={"minutes": 10})
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        assert client.get("/status").json()["interaction_state"] == "quiet"
        clock.set(START + timedelta(minutes=11))
        status = client.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert_timed_state_consistent(status)


def test_both_timed_controls_expire_before_status(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    clock = FixedClock(START)
    with TestClient(create_app(database_path=database_path, clock=clock)) as client:
        advance_to_nudge(client, clock)
        client.post("/interactions/current/defer", json={"minutes": 15})
        client.post("/interactions/current/quiet", json={"minutes": 10})
        clock.set(START + timedelta(minutes=61))
        status = client.get("/status").json()
        assert status["interaction_state"] == "focusing"
        assert_timed_state_consistent(status)
    assert persisted_status(database_path, "quiet_intervals") == "expired"
    assert persisted_status(database_path, "deferrals") == "expired"
