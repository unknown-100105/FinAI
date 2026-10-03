import type { MarketNewsItem } from "./market";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type CandleAnalysis = {
  index: number; timestamp: string; open:number; high:number; low:number; close:number; volume:number;
  direction:string; return_percent:number|null; range_percent:number|null;
  body_percent_of_range:number; upper_wick_percent_of_range:number; lower_wick_percent_of_range:number;
  relative_volume:number|null; trend_last_5:string; observed_features:string[];
  possible_drivers_to_investigate:string[]; news_candidates:MarketNewsItem[]; causality_note:string;
};

export async function getMarketAnalyst(instrument:string,start:string,end:string,interval:string){
  const params = new URLSearchParams({instrument,start,end,interval,news_count:"10"});
  const response = await fetch(API_BASE_URL + "/api/v1/market/analyst?" + params);
  if(!response.ok) throw new Error("Market analyst API error " + response.status + ": " + await response.text());
  return response.json() as Promise<{
    instrument:any; range:any; interval:string; analysis:{count:number;candles:CandleAnalysis[];summary:any;scenario?:{scenarios:Array<{name:string;conditions_to_watch:string[];not_a_prediction:boolean}>;selection_basis:string;forecast_note:string}};
    news:MarketNewsItem[]; source:string; causality_note:string;
  }>;
}

export function explainCandle(payload: {
  instrument: string;
  candle: CandleAnalysis;
  context_news?: unknown[];
  model_id?: string;
}) {
  const response = fetch(
    API_BASE_URL + "/api/v1/market/analyst/explain",
    {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload),
    },
  );
  return response.then(async (result) => {
    if (!result.ok) throw new Error("Candle explanation API error " + result.status + ": " + await result.text());
    return result.json() as Promise<{status:string;response:string;model_id?:string;verification?:unknown}>;
  });
}
