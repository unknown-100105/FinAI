const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type XAITraceSummary = {
  trace_id:string; session_id?:string; started_at?:string; completed_at?:string;
  intent?:string; risk_level?:string; final_status?:string;
};

export function listXAITraces(){
  return fetch(API_BASE_URL + "/api/v1/xai/traces").then(async r=>{
    if(!r.ok) throw new Error("XAI API error " + r.status + ": " + await r.text());
    return r.json() as Promise<{count:number;traces:XAITraceSummary[]}>;
  });
}

export function getXAITrace(traceId:string){
  return fetch(API_BASE_URL + "/api/v1/xai/traces/" + encodeURIComponent(traceId)).then(async r=>{
    if(!r.ok) throw new Error("XAI trace error " + r.status + ": " + await r.text());
    return r.json();
  });
}
