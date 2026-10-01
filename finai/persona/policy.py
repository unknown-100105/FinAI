from __future__ import annotations

from dataclasses import dataclass

from .prompts import VALID_PERSONAS


@dataclass(frozen=True)
class PersonaPolicy:
    name: str
    display_name: str
    description: str


PERSONA_POLICIES = {
    "hype": PersonaPolicy(
        name="hype",
        display_name="Financial Hype Man",
        description="Energetic and encouraging communication.",
    ),
    "accountant": PersonaPolicy(
        name="accountant",
        display_name="Stern Accountant",
        description="Direct and analytical communication.",
    ),
}


def get_persona_policy(persona: str) -> PersonaPolicy:
    normalized = persona.strip().lower()

    if normalized not in VALID_PERSONAS:
        raise ValueError(
            f"Unsupported persona '{persona}'."
        )

    return PERSONA_POLICIES[normalized]