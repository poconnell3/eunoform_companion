"""Small cancellable scheduler for automatic deterministic policy evaluation."""

from __future__ import annotations

import asyncio
import logging

from app.services.companion_application_service import CompanionApplicationService

logger = logging.getLogger(__name__)


async def run_scheduler(
    service: CompanionApplicationService,
    *,
    interval_seconds: float = 1.0,
) -> None:
    if interval_seconds <= 0:
        raise ValueError("Scheduler interval must be greater than zero.")
    while True:
        try:
            await asyncio.to_thread(service.scheduler_tick)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Automatic policy evaluation failed; the scheduler will retry.")
        await asyncio.sleep(interval_seconds)
