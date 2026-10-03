const API_BASE_URL=import.meta.env.VITE_API_BASE_URL||"http://localhost:8000";
export type GlobalCountry={country:string;country_code:string;currency:string;primary_market:string;region:string;asset_classes:string[]};
export type GlobalAssetClass={id:string;label:string;description:string};
export type Eligibility={country:string;country_code:string;asset_class:string;investor:string;status:string;summary:string;checks:string[];verification_sources:string[]};
async function getJson<T>(path:string):Promise<T>{const r=await fetch(API_BASE_URL+path);if(!r.ok)throw new Error("FinAI intelligence API error "+r.status+": "+await r.text());return r.json() as Promise<T>}
export function getGlobalCatalog(){return getJson<{countries:GlobalCountry[];asset_classes:GlobalAssetClass[];investor_profile:string;scope_note:string}>("/api/v1/intelligence/global-assets")}
export function getEligibility(country_code:string,asset_class:string){return getJson<Eligibility>("/api/v1/intelligence/eligibility?country_code="+encodeURIComponent(country_code)+"&asset_class="+encodeURIComponent(asset_class))}
export type ModelResult={model_id:string;family:string;status:string;direction:string;probability_up:number|null;validation_accuracy:number|null;validation_samples:number;weight:number;feature_importance:Record<string,number>;note:string};
export type Prediction={status:string;horizon:number;models:ModelResult[];ensemble:{direction:string;probability_up:number|null;confidence:number|null;model_count:number};features:string[];validation?:{method:string;train_samples:number;test_samples:number};note?:string};
export function getPrediction(instrument:string,horizon=5){return getJson<{instrument:any}&Prediction>("/api/v1/intelligence/prediction?instrument="+encodeURIComponent(instrument)+"&horizon="+horizon)}
