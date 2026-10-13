"""Dynamic crypto market universe and cross-exchange scanner.

The regulatory registry is a separate concept from market connectivity:
FIU-IND reporting-entity registration is an AML/PMLA status, not a blanket
financial-market licence or government endorsement. The latest official
Parliament snapshot used here is dated 09-03-2026 and lists 54 registered VDA
service providers.

Only venues with a usable public market-data connector are scanned. The
scanner uses public ticker snapshots to identify candidates, then order-book
quotes for the final opportunity calculation where available.
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterable, List, Optional

from policy.network_mode import assert_external_network_allowed

REGULATORY_SOURCE = "Government of India, Lok Sabha AU5805, 30-03-2026"
REGULATORY_SOURCE_URL = "https://sansad.in/getFile/loksabhaquestions/annex/187/AU5805_lMTYNK.pdf?source=pqals"

FIU_REGISTERED_SNAPSHOT = (
    ("Coin DCX", "Neblio Technologies Private Limited", "India", "registered"),
    ("ANQ Finance", "ANQ Digital Finserv Private Limited", "India", "registered"),
    ("Unocoin", "Unocoin Technologies PVT LTD", "India", "registered"),
    ("Onramp", "Buyhatke internet private limited", "India", "registered"),
    ("Giottus", "Giottus Technologies Pvt Ltd", "India", "registered"),
    ("Bitbns", "Bitbns Internet Private Limited", "India", "registered"),
    ("Zebpay", "Awlencan Innovations India Limited", "India", "registered"),
    ("WazirX", "Zanmai Labs PVT LTD", "India", "registered"),
    ("Coinswitch", "Bitcipher Labs LLP", "India", "registered"),
    ("CoinswitchX", "Nextgendev Solutions Private Limited", "India", "registered"),
    ("Mudrex", "RPFAS Technologies Private Limited", "India", "registered"),
    ("Buyucoin", "IBLOCK Technologies Private Limited", "India", "registered"),
    ("Coindhan", "WOLLFISH Labs Pvt Ltd", "India", "registered"),
    ("Rario", "Rario Digital Private Limited", "India", "registered"),
    ("Suncrypto", "Angelic Infotech Private Limited", "India", "registered"),
    ("Carret", "Carretx Technologies Pvt. Ltd.", "India", "registered"),
    ("—", "Ante Multimedia Private Limited", "India", "registered"),
    ("Onmeta", "ABHIBHA Technologies Private Limited", "India", "registered"),
    ("Cryptosmartlife", "Smartliving Digital Technologies Pvt. Ltd", "India", "registered"),
    ("Pyor", "UCY Technology Private Limited", "India", "registered"),
    ("Rario", "Digital Collectibles Pte. Ltd.", "Singapore", "registered"),
    ("Valr", "Veeratva Technologies Private Limited", "India", "registered"),
    ("Transak", "Transak Technology India Private Limited", "India", "registered"),
    ("Getbit", "REMIZO Technologies India Private Limited", "India", "registered"),
    ("Bytex", "FIN GENIE Tech Private Limited", "India", "registered"),
    ("—", "ARDOUR Labs Private Limited", "India", "registered"),
    ("Inocyx", "Inocyx Technologies Private Limited", "India", "registered"),
    ("Fanztar", "Metatoken Technologies Private Limited", "India", "registered"),
    ("Delta Exchange", "Excelium Technologies Private Limited", "India", "registered"),
    ("—", "Rovi91 Innovations Private Limited", "India", "registered"),
    ("Bitbse.com", "Longreen India Private Limited", "India", "registered"),
    ("Flitpay", "Flitpay Private Limited", "India", "registered"),
    ("Stable Pay", "Fincrypt LLP", "India", "registered"),
    ("ArthBit", "Arthbit Private Limited", "India", "registered"),
    ("Density Exchange", "Pagarpay India Private Limited", "India", "registered"),
    ("pi42", "Lightningnodes Technologies Private Limited", "India", "registered"),
    ("KoinBX", "Kooz Advisors and Technologies Private Limited", "India", "registered"),
    ("—", "Mindless Pandora Tech Solutions Private Limited", "India", "registered"),
    ("—", "FanCraze Technologies Inc.", "Delaware, USA", "registered"),
    ("BIT24HR", "SUBHX INFOTECH (OPC) PRIVATE LIMITED", "India", "registered"),
    ("KuCoin", "Peken Global Limited", "Seychelles", "registered"),
    ("Alpyne", "ALSD Technologies Private Limited", "India", "registered"),
    ("Square", "Damsol Pvt Ltd", "India", "registered"),
    ("Liminal", "First Answer India Technologies Pvt Ltd", "India", "registered"),
    ("Eclipton", "Eclipton Technologies Private Limited", "India", "registered"),
    ("Blockoville", "Blockoville OU", "Estonia", "registered"),
    ("Binance", "Nest Services Limited (Earlier Binance International Limited)", "Seychelles", "registered"),
    ("Bybit", "Bybit Fintech Limited", "Seychelles", "registered"),
    ("Coinbase India", "Coinbase India Private Limited", "India", "registered"),
    ("eXchange1", 'UAB "Web 3 Utility Platform"', "Lithuania", "registered"),
    ("eXchange1.India", "UAB WEB 3 UTILITY IT SERVICES INDIA PRIVATE LIMITED", "India", "linked_offshore"),
    ("PLATINX", "Eopsin Tech Private Limited", "India", "conditional"),
    ("Parracrypto", "PARAACRYPTO TECHNOLOGY PRIVATE LIMITED", "India", "conditional"),
    ("BitDelta", "Durva Fintech Private Limited", "India", "conditional"),
)

# Public connectors that are both present in CCXT in typical installations
# and are present in the FIU registration snapshot.
PUBLIC_CONNECTOR_CANDIDATES = {
    "binance": "Binance",
    "bybit": "Bybit",
    "kucoin": "KuCoin",
    "coinbase": "Coinbase India",
    "coindcx": "Coin DCX",
    "wazirx": "WazirX",
    "bitbns": "Bitbns",
    "koinbx": "KoinBX",
    "flitpay": "Flitpay",
}

def public_connector_map() -> Dict[str, str]:
    try:
        ccxt = _ccxt()
    except RuntimeError:
        return {
            "binance": "Binance",
            "bybit": "Bybit",
            "kucoin": "KuCoin",
            "coinbase": "Coinbase India",
        }

    return {
        exchange_id: trade_name
        for exchange_id, trade_name in PUBLIC_CONNECTOR_CANDIDATES.items()
        if hasattr(ccxt, exchange_id)
    }

_CACHE: Dict[str, Any] = {}
_CACHE_LOCK = Lock()


def _ccxt():
    try:
        import ccxt
    except ImportError as exc:
        raise RuntimeError("CCXT is required for live crypto market scanning.") from exc
    return ccxt


def supported_connectors() -> List[Dict[str, str]]:
    connector_map = public_connector_map()
    return [
        {
            "exchange_id": exchange_id,
            "trade_name": trade_name,
            "regulatory_status": "FIU-IND reporting-entity snapshot",
            "snapshot_date": "2026-03-09",
            "source": REGULATORY_SOURCE,
        }
        for exchange_id, trade_name in connector_map.items()
    ]


def registered_vda_services() -> List[Dict[str, str]]:
    return [
        {
            "trade_name": trade_name,
            "registered_entity": entity,
            "country": country,
            "status": status,
            "snapshot_date": "2026-03-09",
            "source": REGULATORY_SOURCE_URL,
        }
        for trade_name, entity, country, status in FIU_REGISTERED_SNAPSHOT
    ]


def _exchange(exchange_id: str):
    assert_external_network_allowed("CCXT market request")
    ccxt = _ccxt()
    exchange_class = getattr(ccxt, exchange_id, None)
    if exchange_class is None:
        raise ValueError(f"CCXT connector not available: {exchange_id}")
    return exchange_class({"enableRateLimit": True, "timeout": 15000})


def _cache_get(key: str, ttl_seconds: int) -> Optional[Any]:
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        if (datetime.now(timezone.utc) - item["at"]).total_seconds() > ttl_seconds:
            return None
        return item["value"]


def _cache_set(key: str, value: Any) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = {"at": datetime.now(timezone.utc), "value": value}


def _normalize_ticker(symbol: str, ticker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    bid = ticker.get("bid")
    ask = ticker.get("ask")
    last = ticker.get("last")
    if bid is None and ask is None and last is None:
        return None
    return {
        "symbol": symbol,
        "last": float(last) if last is not None else None,
        "bid": float(bid) if bid is not None else None,
        "ask": float(ask) if ask is not None else None,
        "bid_volume": float(ticker["bidVolume"]) if ticker.get("bidVolume") is not None else None,
        "ask_volume": float(ticker["askVolume"]) if ticker.get("askVolume") is not None else None,
        "base_volume": float(ticker["baseVolume"]) if ticker.get("baseVolume") is not None else None,
        "quote_volume": float(ticker["quoteVolume"]) if ticker.get("quoteVolume") is not None else None,
        "timestamp": ticker.get("timestamp"),
    }


def market_universe(
    exchange_id: str,
    *,
    quote: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
) -> Dict[str, Any]:
    key = f"markets:{exchange_id}"
    cached = _cache_get(key, 300)
    if cached is None:
        exchange = _exchange(exchange_id)
        markets = exchange.load_markets()
        cached = []
        for symbol, market in markets.items():
            if not market.get("active", True):
                continue
            if not market.get("spot", False):
                continue
            cached.append({
                "symbol": symbol,
                "base": market.get("base"),
                "quote": market.get("quote"),
                "type": market.get("type"),
                "active": bool(market.get("active", True)),
            })
        _cache_set(key, cached)

    q = (quote or "").strip().upper()
    s = (search or "").strip().upper()
    filtered = [
        item for item in cached
        if (not q or str(item.get("quote") or "").upper() == q)
        and (not s or s in str(item.get("symbol") or "").upper())
    ]
    return {
        "exchange": exchange_id,
        "count": len(filtered),
        "offset": max(0, int(offset)),
        "limit": max(1, min(int(limit), 5000)),
        "pairs": filtered[max(0, int(offset)): max(0, int(offset)) + max(1, min(int(limit), 5000))],
        "regulatory_note": "FIU-IND reporting registration is not a government endorsement or securities-market licence.",
        "regulatory_source": REGULATORY_SOURCE_URL,
    }



def exchange_ohlcv(
    exchange_id: str,
    symbol: str,
    timeframe: str = "15m",
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Return live public OHLCV candles from a specific exchange connector."""
    if not symbol or not symbol.strip():
        raise ValueError("symbol is required.")
    limit_value = max(10, min(int(limit), 1000))
    key = f"ohlcv:{exchange_id}:{symbol}:{timeframe}:{limit_value}"
    cached = _cache_get(key, 10)
    if cached is not None:
        return cached

    exchange = _exchange(exchange_id)
    if not exchange.has.get("fetchOHLCV"):
        raise RuntimeError(f"{exchange_id} does not expose public OHLCV data.")

    rows = exchange.fetch_ohlcv(
        symbol.strip(),
        timeframe=timeframe,
        limit=limit_value,
    )
    result = [
        {
            "timestamp": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]) if len(row) > 5 and row[5] is not None else None,
        }
        for row in rows
        if len(row) >= 5
    ]
    _cache_set(key, result)
    return result

def all_exchange_tickers(
    exchange_id: str,
    *,
    quote: Optional[str] = None,
) -> List[Dict[str, Any]]:
    key = f"tickers:{exchange_id}:{(quote or '').upper()}"
    cached = _cache_get(key, 30)
    if cached is not None:
        return cached

    exchange = _exchange(exchange_id)
    if not exchange.has.get("fetchTickers"):
        raise RuntimeError(f"{exchange_id} does not expose a public fetchTickers capability.")

    raw = exchange.fetch_tickers()
    q = (quote or "").strip().upper()
    result = []
    for symbol, ticker in raw.items():
        if q and not symbol.upper().endswith("/" + q):
            continue
        normalized = _normalize_ticker(symbol, ticker)
        if normalized:
            result.append(normalized)

    _cache_set(key, result)
    return result


def scan_all_pairs(
    *,
    exchanges: Iterable[str] | None = None,
    quote: str = "USDT",
    capital_quote: float = 1000.0,
    buy_fee_percent: float = 0.1,
    sell_fee_percent: float = 0.1,
    buy_slippage_percent: float = 0.05,
    sell_slippage_percent: float = 0.05,
    transfer_cost_quote: float = 0.0,
    tax_rate_percent: float = 0.0,
    top_n: int = 25,
) -> Dict[str, Any]:
    from .arbitrage import estimate_arbitrage

    connector_map = public_connector_map()
    if exchanges is None:
        exchanges = tuple(connector_map)

    snapshots: Dict[str, List[Dict[str, Any]]] = {}
    errors: Dict[str, str] = {}
    requested = list(dict.fromkeys(
        str(item).strip().lower() for item in exchanges if str(item).strip()
    ))

    def load_exchange(exchange_id: str):
        if exchange_id not in connector_map:
            return exchange_id, None, "Exchange is not in the FIU-registered public-connector snapshot."
        try:
            return exchange_id, all_exchange_tickers(exchange_id, quote=quote), None
        except Exception as exc:
            return exchange_id, None, str(exc)

    with ThreadPoolExecutor(max_workers=min(6, max(1, len(requested)))) as executor:
        futures = [executor.submit(load_exchange, exchange_id) for exchange_id in requested]
        for future in as_completed(futures):
            exchange_id, tickers, error = future.result()
            if error:
                errors[exchange_id] = error
            else:
                snapshots[exchange_id] = tickers or []

    per_symbol: Dict[str, List[Dict[str, Any]]] = {}
    for exchange_id, tickers in snapshots.items():
        for ticker in tickers:
            per_symbol.setdefault(ticker["symbol"], []).append({
                **ticker,
                "exchange": exchange_id,
            })

    candidates = []
    for symbol, tickers in per_symbol.items():
        buys = [t for t in tickers if t.get("ask") and t["ask"] > 0]
        sells = [t for t in tickers if t.get("bid") and t["bid"] > 0]
        if len({t["exchange"] for t in tickers}) < 2 or not buys or not sells:
            continue
        buy = min(buys, key=lambda t: t["ask"])
        sell = max(sells, key=lambda t: t["bid"])
        if buy["exchange"] == sell["exchange"] or sell["bid"] <= buy["ask"]:
            continue
        max_quantity = None
        volumes = [v for v in (buy.get("ask_volume"), sell.get("bid_volume")) if v and v > 0]
        if volumes:
            max_quantity = min(volumes)
        try:
            estimate = estimate_arbitrage(
                asset=symbol,
                buy_venue=buy["exchange"],
                sell_venue=sell["exchange"],
                capital_quote=capital_quote,
                buy_price=buy["ask"],
                sell_price=sell["bid"],
                buy_fee_percent=buy_fee_percent,
                sell_fee_percent=sell_fee_percent,
                buy_slippage_percent=buy_slippage_percent,
                sell_slippage_percent=sell_slippage_percent,
                transfer_cost_quote=transfer_cost_quote,
                tax_rate_percent=tax_rate_percent,
                max_quantity=max_quantity,
            )
            estimate["snapshot_at"] = datetime.now(timezone.utc).isoformat()
            estimate["buy_ask_volume"] = buy.get("ask_volume")
            estimate["sell_bid_volume"] = sell.get("bid_volume")
            candidates.append(estimate)
        except ValueError:
            continue

    candidates.sort(key=lambda item: float(item.get("net_return_percent", 0.0)), reverse=True)

    # Validate only the leading candidates against live order books. Scanning
    # every order book would create substantial API load and rate-limit risk.
    from .scanner import fetch_orderbook_snapshot

    validated = []
    for candidate in candidates[: min(len(candidates), 10)]:
        try:
            buy_book = fetch_orderbook_snapshot(candidate["buy_venue"], candidate["asset"])
            sell_book = fetch_orderbook_snapshot(candidate["sell_venue"], candidate["asset"])
            validated_result = estimate_arbitrage(
                asset=candidate["asset"],
                buy_venue=candidate["buy_venue"],
                sell_venue=candidate["sell_venue"],
                capital_quote=capital_quote,
                buy_price=buy_book["best_ask"],
                sell_price=sell_book["best_bid"],
                buy_fee_percent=buy_fee_percent,
                sell_fee_percent=sell_fee_percent,
                buy_slippage_percent=buy_slippage_percent,
                sell_slippage_percent=sell_slippage_percent,
                transfer_cost_quote=transfer_cost_quote,
                fx_cost_percent=0.0,
                tax_rate_percent=tax_rate_percent,
                max_quantity=min(buy_book["best_ask_amount"], sell_book["best_bid_amount"]),
            )
            validated_result["snapshot_at"] = datetime.now(timezone.utc).isoformat()
            validated_result["execution_validated"] = True
            validated_result["validation_type"] = "top-of-book"
            validated.append(validated_result)
        except Exception as exc:
            candidate["execution_validated"] = False
            candidate["validation_type"] = "ticker-only"
            candidate["validation_error"] = str(exc)
            validated.append(candidate)

    candidates = sorted(
        validated + candidates[10:],
        key=lambda item: float(item.get("net_return_percent", 0.0)),
        reverse=True,
    )
    return {        "status": "LIVE_SNAPSHOT",
        "quote_currency": quote,
        "exchanges_requested": list(dict.fromkeys(str(item).strip().lower() for item in exchanges if str(item).strip())),
        "exchanges_scanned": sorted(snapshots),
        "pair_count": len(per_symbol),
        "opportunity_count": len(candidates),
        "opportunities": candidates[: max(1, min(int(top_n), 100))],
        "validation": "Top 10 ticker candidates attempt live top-of-book validation; remaining rows are ticker snapshots.",
        "errors": errors,
        "regulatory_source": REGULATORY_SOURCE_URL,
        "regulatory_snapshot_date": "2026-03-09",
        "note": (
            "This is a public ticker snapshot. FIU-IND reporting registration is AML/PMLA "
            "status, not blanket product approval. Public-ticker spreads are candidates; "
            "order-book depth, withdrawal availability, network fees, latency, tax and "
            "execution can make net realizable profit materially different."
        ),
    }
