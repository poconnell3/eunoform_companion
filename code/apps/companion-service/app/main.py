"""Local FastAPI entry point for the Eunoform Companion."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI

from app.api.router import router
from app.domain.clock import Clock, SystemClock
from app.persistence.database import Database
from app.persistence.repositories import (
    SQLiteDeferralRepository,
    SQLiteFocusSessionRepository,
    SQLiteNudgeRepository,
    SQLiteQuietIntervalRepository,
    SQLiteSettingsRepository,
)
from app.services.background_scheduler import run_scheduler
from app.services.companion_application_service import CompanionApplicationService


def create_app(
    *,
    database_path: str | Path = "eunoform_companion.sqlite3",
    clock: Clock | None = None,
    scheduler_enabled: bool = True,
    scheduler_interval_seconds: float = 1.0,
) -> FastAPI:
    if scheduler_interval_seconds <= 0:
        raise ValueError("Scheduler interval must be greater than zero.")
    db = Database(database_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db.initialize()
        settings_repo = SQLiteSettingsRepository(db)
        if settings_repo.get() is None:
            raise RuntimeError("Settings repository unavailable")
        app.state.companion_service = CompanionApplicationService(
            clock=clock or SystemClock(),
            settings_repo=settings_repo,
            focus_repo=SQLiteFocusSessionRepository(db),
            nudge_repo=SQLiteNudgeRepository(db),
            deferral_repo=SQLiteDeferralRepository(db),
            quiet_repo=SQLiteQuietIntervalRepository(db),
        )
        scheduler_task = None
        if scheduler_enabled:
            scheduler_task = asyncio.create_task(
                run_scheduler(
                    app.state.companion_service,
                    interval_seconds=scheduler_interval_seconds,
                )
            )
        try:
            yield
        finally:
            if scheduler_task is not None:
                scheduler_task.cancel()
                with suppress(asyncio.CancelledError):
                    await scheduler_task

    app = FastAPI(
        title="Eunoform Companion API",
        version="0.4.0",
        description="Local deterministic API for focus sessions and humane interactions.",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
