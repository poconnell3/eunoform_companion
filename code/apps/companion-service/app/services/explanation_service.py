"""Explain policy facts without inventing inferred human states."""

from __future__ import annotations

from app.domain.models import ExplanationFacts


class ExplanationService:
    @staticmethod
    def format(facts: ExplanationFacts) -> str:
        elapsed = ExplanationService._minutes_phrase(facts.elapsed_minutes)
        threshold = ExplanationService._minutes_phrase(facts.threshold_minutes)
        return (
            f"You started this focus session {elapsed} ago, "
            f"and your break-check interval is {threshold}."
        )

    @staticmethod
    def _minutes_phrase(minutes: int) -> str:
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit}"
