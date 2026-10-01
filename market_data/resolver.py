from typing import Optional

from .instruments import Instrument, all_instruments


class InstrumentResolver:
    """Resolve user-facing instrument names to canonical identities."""

    def __init__(self):
        self.instruments = tuple(all_instruments())

        self._aliases = {}

        for instrument in self.instruments:
            for alias in instrument.aliases:
                normalized = self._normalize(alias)

                if normalized in self._aliases:
                    raise ValueError(
                        f"Duplicate instrument alias: {alias}"
                    )

                self._aliases[normalized] = instrument

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(
            str(value)
            .strip()
            .lower()
            .replace("-", " ")
            .split()
        )

    def resolve(
        self,
        query: str,
    ) -> Optional[Instrument]:
        normalized = self._normalize(query)

        if not normalized:
            return None

        return self._aliases.get(normalized)

    def resolve_or_raise(
        self,
        query: str,
    ) -> Instrument:
        instrument = self.resolve(query)

        if instrument is None:
            raise ValueError(
                f"Unknown financial instrument: {query}"
            )

        return instrument
