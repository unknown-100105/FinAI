
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type MarketInstrument = {
  instrument_id: string;
  display_name: string;
  asset_type: string;
  exchange?: string | null;
  currency?: string | null;
};

export type MarketQuote = {
  price?: number | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  close?: number | null;
  volume?: number | null;
  currency?: string | null;
  timestamp?: string | null;
  source?: string;
};

export type MarketBar = {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
  source: string;
};

export type MarketOverviewItem = {
  instrument: MarketInstrument;
  price?: number | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  close?: number | null;
  volume?: number | null;
  change?: number | null;
  change_percent?: number | null;
  timestamp?: string | null;
  source?: string;
  error?: string;
};

export type MarketNewsItem = {
  title: string;
  publisher?: string | null;
  link?: string | null;
  published_at?: string | null;
  type?: string;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(API_BASE_URL + path);

  if (!response.ok) {
    throw new Error(`FinAI market API error ${response.status}: ${await response.text()}`);
  }

  return response.json() as Promise<T>;
}

export function getMarketQuote(instrument: string) {
  return getJson<{ instrument: MarketInstrument; quote: MarketQuote }>(
    `/api/v1/market/quote?instrument=${encodeURIComponent(instrument)}`,
  );
}

export function getMarketHistory(
  instrument: string,
  start: string,
  end: string,
  interval = "1d",
) {
  return getJson<{
    instrument: MarketInstrument;
    range: { start: string; end: string };
    count: number;
    bars: MarketBar[];
  }>(
    `/api/v1/market/history?instrument=${encodeURIComponent(instrument)}&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&interval=${encodeURIComponent(interval)}`,
  );
}

export function getMarketOverview() {
  return getJson<{
    source: string;
    instruments: MarketOverviewItem[];
    gainers: MarketOverviewItem[];
    losers: MarketOverviewItem[];
  }>("/api/v1/market/overview");
}

export function getMarketNews(query = "Indian stock market", count = 8) {
  return getJson<{
    query: string;
    count: number;
    source: string;
    articles: MarketNewsItem[];
  }>(
    `/api/v1/market/news?query=${encodeURIComponent(query)}&count=${count}`,
  );
}


export type InstrumentSearchResult = {
  symbol: string;
  name: string;
  asset_type: string;
  quote_type?: string | null;
  exchange?: string | null;
  exchange_full_name?: string | null;
  currency?: string | null;
  score?: number | null;
  provider: string;
};

export function searchMarketInstruments(query: string, count = 10) {
  return getJson<{
    query: string;
    count: number;
    source: string;
    results: InstrumentSearchResult[];
  }>(
    `/api/v1/market/search?query=${encodeURIComponent(query)}&count=${count}`,
  );
}


export function getMarketAnalytics(
  instrument: string,
  start: string,
  end: string,
  interval = "1d",
) {
  return getJson<{
    instrument: MarketInstrument;
    range: { start: string; end: string };
    analytics: Record<string, number | null>;
    data_points: number;
  }>(
    `/api/v1/market/analytics?instrument=${encodeURIComponent(instrument)}&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&interval=${encodeURIComponent(interval)}`,
  );
}
