const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type ArbitrageEstimateRequest = {
  asset: string;
  buy_venue: string;
  sell_venue: string;
  capital_quote: number;
  buy_price: number;
  sell_price: number;
  buy_fee_percent?: number;
  sell_fee_percent?: number;
  buy_slippage_percent?: number;
  sell_slippage_percent?: number;
  transfer_cost_quote?: number;
  fx_cost_percent?: number;
  tax_rate_percent?: number;
  max_quantity?: number;
};

export async function estimateCryptoArbitrage(
  request: ArbitrageEstimateRequest,
) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/crypto/arbitrage/estimate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Arbitrage estimator error ${response.status}: ${await response.text()}`,
    );
  }

  return response.json();
}

export type ArbitrageScanRequest = {
  symbol: string;
  exchanges: string[];
  capital_quote: number;
  buy_fee_percent?: number;
  sell_fee_percent?: number;
  buy_slippage_percent?: number;
  sell_slippage_percent?: number;
  transfer_cost_quote?: number;
  fx_cost_percent?: number;
  tax_rate_percent?: number;
};

export async function scanCryptoArbitrage(
  request: ArbitrageScanRequest,
) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/crypto/arbitrage/scan`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Arbitrage scan error ${response.status}: ${await response.text()}`,
    );
  }

  return response.json();
}

export function getCryptoConnectors() {
  return fetch(API_BASE_URL + "/api/v1/crypto/connectors").then(async (response) => {
    if (!response.ok) throw new Error("Crypto connector error " + response.status + ": " + await response.text());
    return response.json();
  });
}

export function getCryptoMarkets(exchange: string, quote = "USDT", search = "", limit = 500, offset = 0) {
  const params = new URLSearchParams({
    exchange,
    quote,
    limit: String(limit),
    offset: String(offset),
  });
  if (search) params.set("search", search);
  return fetch(API_BASE_URL + "/api/v1/crypto/markets?" + params.toString()).then(async (response) => {
    if (!response.ok) throw new Error("Crypto market universe error " + response.status + ": " + await response.text());
    return response.json();
  });
}

export function scanAllCryptoPairs(request: {
  exchanges: string[];
  quote: string;
  capital_quote: number;
  buy_fee_percent?: number;
  sell_fee_percent?: number;
  buy_slippage_percent?: number;
  sell_slippage_percent?: number;
  transfer_cost_quote?: number;
  tax_rate_percent?: number;
  top_n?: number;
}) {
  return fetch(API_BASE_URL + "/api/v1/crypto/arbitrage/scan-all", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  }).then(async (response) => {
    if (!response.ok) throw new Error("All-pairs arbitrage error " + response.status + ": " + await response.text());
    return response.json();
  });
}
