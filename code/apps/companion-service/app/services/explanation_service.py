"""Explain policy facts without inventing inferred human states."""
from app.domain.models import ExplanationFacts
class ExplanationService:
    @staticmethod
    def format(facts:ExplanationFacts)->str:
        p=lambda m:f"{m} {'minute' if m==1 else 'minutes'}"
        return f"You started this focus session {p(facts.elapsed_minutes)} ago, and your break-check interval is {p(facts.threshold_minutes)}."
