"""Explain policy facts without inventing inferred human states."""

from app.domain.models import ExplanationFacts


class ExplanationService:
    @staticmethod
    def format(facts: ExplanationFacts) -> str:
        def minutes(value: int) -> str:
            return f"{value} {'minute' if value == 1 else 'minutes'}"

        elapsed = minutes(facts.elapsed_minutes)
        threshold = minutes(facts.threshold_minutes)
        return (
            f"You started this focus session {elapsed} ago, "
            f"and your break-check interval is {threshold}."
        )
