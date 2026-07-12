"""Local FastAPI entry point for the Eunoform Companion."""

from __future__ import annotations

from contextlib import asynccontextmanager
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
from app.services.companion_application_service import CompanionApplicationService


def create_app(
    *, database_path: str | Path = "eunoform_companion.sqlite3", clock: Clock | None = None
) -> FastAPI:
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
        yield

    app = FastAPI(
        title="Eunoform Companion API",
        version="0.2.0",
        description="Local deterministic API for focus sessions and humane interactions.",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
