from dataclasses import asdict
from typing import Any, Dict


def normalize_market_result(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert the internal market-data result into a compact,
    LLM-safe factual context.

    The formatter never invents missing values and preserves
    provider/source/timestamp information.
    """

    operations = list(
        market_data.get("operations") or []
    )

    normalized: Dict[str, Any] = {
        "operations": operations,
        "planning_reason": market_data.get(
            "planning_reason"
        ),
        "source": None,
        "timestamp": None,
        "instrument": None,
        "data": [],
    }

    for item in market_data.get("results") or []:
        operation = item.get("operation")
        instrument = item.get("instrument") or {}
        result = item.get("result")

        if normalized["instrument"] is None:
            normalized["instrument"] = {
                "instrument_id": instrument.get(
                    "instrument_id"
                ),
                "display_name": instrument.get(
                    "display_name"
                ),
                "asset_type": instrument.get(
                    "asset_type"
                ),
                "exchange": instrument.get(
                    "exchange"
                ),
                "currency": instrument.get(
                    "currency"
                ),
            }

        normalized["data"].append(
            {
                "operation": operation,
                "result": result,
            }
        )

        if isinstance(result, dict):
            if normalized["source"] is None:
                normalized["source"] = result.get(
                    "source"
                )

            if normalized["timestamp"] is None:
                normalized["timestamp"] = result.get(
                    "timestamp"
                )

    if "range" in market_data:
        normalized["range"] = market_data["range"]

    if "date_range_reason" in market_data:
        normalized["date_range_reason"] = (
            market_data["date_range_reason"]
        )

    return normalized
