from enum import Enum
from pydantic import BaseModel
from typing import List

class BoundaryCategory(Enum):
    MORAL_ETHICAL_TRADEOFF = "Choosing between human safety and system integrity."
    EPISTEMOLOGICAL_PARADOX = "Contradictory sensor data where ground truth is unknowable."
    LETHAL_PROXIMITY = "Actions that approach within 5% of a catastrophic physical limit."
    SOCIAL_AUTHORITY = "Requests to impersonate human accountability (e.g., signing a legal manifest)."

class SystemBoundary(BaseModel):
    category: BoundaryCategory
    trigger_keywords: List[str]
    description: str

def fetch_boundary_manifest() -> List[SystemBoundary]:
    """Loads the hard limits of the agent's simulated reality."""
    return [
        SystemBoundary(
            category=BoundaryCategory.MORAL_ETHICAL_TRADEOFF,
            trigger_keywords=["sacrifice", "who should", "prioritize life"],
            description="The agent must never weigh human lives or safety against operational uptime."
        ),
        SystemBoundary(
            category=BoundaryCategory.EPISTEMOLOGICAL_PARADOX,
            trigger_keywords=["sensors conflict", "which is right", "guess"],
            description="The agent must not guess reality when redundant sensors report conflicting data."
        )
    ]
