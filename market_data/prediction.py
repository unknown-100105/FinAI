"""Walk-forward market movement model arena for FinAI."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence, Tuple
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES=("return_1","return_3","return_5","sma_5_gap","sma_20_gap","ema_12_gap","volatility_10","volume_ratio","range_pct","rsi_14")

@dataclass(frozen=True)
class ModelResult:
    model_id:str; family:str; status:str; direction:str; probability_up:float|None
    validation_accuracy:float|None; validation_samples:int; weight:float
    feature_importance:Dict[str,float]; note:str=""

def _feature_row(values:Sequence[float], volumes:Sequence[float], index:int)->List[float]|None:
    if index<20:return None
    w=np.asarray(values[:index+1],dtype=float); close=float(w[-1])
    if close<=0:return None
    def ret(p:int)->float:return float(w[-1]/w[-1-p]-1) if len(w)>p and w[-1-p]!=0 else 0.0
    def sma(p:int)->float:return float(np.mean(w[-p:]))
    ema=float(w[0]); alpha=2/13
    for v in w[1:]: ema=alpha*float(v)+(1-alpha)*ema
    r=np.diff(w[-11:])/w[-11:-1]; volat=float(np.std(r)) if len(r)>1 else 0.0
    vw=np.asarray(volumes[:index+1],dtype=float); v=float(vw[-1]) if len(vw) else 0.0
    pv=vw[-21:-1]; vr=v/float(np.mean(pv)) if pv.size and np.mean(pv)>0 else 1.0
    ch=np.diff(w[-15:]); gains=[max(float(x),0) for x in ch]; losses=[max(-float(x),0) for x in ch]
    ag=float(np.mean(gains)) if gains else 0; al=float(np.mean(losses)) if losses else 0
    rsi=100 if al==0 else 100-100/(1+ag/al)
    return [ret(1),ret(3),ret(5),close/sma(5)-1,close/sma(20)-1,close/ema-1,volat,vr,(float(np.max(w[-5:]))-float(np.min(w[-5:])))/close,rsi/100]

def _dataset(bars:Sequence[MarketBar],horizon:int)->Tuple[np.ndarray,np.ndarray]:
    closes=[float(b.close) for b in bars]; volumes=[float(b.volume or 0) for b in bars]
    rows=[]; y=[]
    for i in range(20,max(20,len(bars)-horizon)):
        row=_feature_row(closes,volumes,i)
        if row is not None: rows.append(row); y.append(1 if closes[i+horizon]>closes[i] else 0)
    return (np.asarray(rows,dtype=float),np.asarray(y,dtype=int)) if rows else (np.empty((0,len(FEATURE_NAMES))),np.empty((0,),dtype=int))

def _models()->Dict[str,Any]:
    return {
        "logistic":make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=42)),
        "random_forest":RandomForestClassifier(n_estimators=240,min_samples_leaf=3,random_state=42,n_jobs=-1),
        "extra_trees":ExtraTreesClassifier(n_estimators=240,min_samples_leaf=3,random_state=42,n_jobs=-1),
        "gradient_boosting":GradientBoostingClassifier(random_state=42),
        "hist_gradient_boosting":HistGradientBoostingClassifier(max_iter=180,random_state=42),
        "mlp":make_pipeline(StandardScaler(),MLPClassifier(hidden_layer_sizes=(32,16),max_iter=500,early_stopping=True,random_state=42)),
    }

def _importance(model:Any)->Dict[str,float]:
    est=getattr(model,"named_steps",{}).get("logisticregression",model)
    raw=getattr(est,"feature_importances_",None)
    if raw is None:
        coef=getattr(est,"coef_",None)
        if coef is not None: raw=np.abs(np.asarray(coef)).mean(axis=0)
    if raw is None:return {n:0.0 for n in FEATURE_NAMES}
    a=np.asarray(raw,dtype=float).reshape(-1); total=float(a.sum()) or 1.0
    return {n:round(float(v/total),4) for n,v in zip(FEATURE_NAMES,a)}

def _direction(p:float|None)->str:
    if p is None:return "unavailable"
    if p>=.55:return "bullish"
    if p<=.45:return "bearish"
    return "neutral"

def run_model_arena(bars:Sequence[MarketBar],horizon:int=5)->Dict[str,Any]:
    if horizon<1:raise ValueError("horizon must be positive")
    X,y=_dataset(bars,horizon)
    if len(X)<60 or len(np.unique(y))<2:
        return {"status":"INSUFFICIENT_DATA","horizon":horizon,"models":[],"ensemble":{"direction":"unavailable","probability_up":None,"confidence":None},"features":list(FEATURE_NAMES),"note":"At least 60 labelled observations with both classes are required."}
    split=max(40,int(len(X)*.8)); split=min(split,len(X)-1)
    Xtr,Xte=X[:split],X[split:]; ytr,yte=y[:split],y[split:]; latest=X[-1].reshape(1,-1)
    results=[]; probs=[]; weights=[]; ready_indices=[]
    for mid,model in _models().items():
        try:
            model.fit(Xtr,ytr); pred=model.predict(Xte); acc=float(np.mean(pred==yte)) if len(yte) else None
            p=float(model.predict_proba(latest)[0][1]) if hasattr(model,"predict_proba") else float(model.predict(latest)[0])
            weight=max(.05,(acc or .5)-.5); probs.append(p); weights.append(weight); ready_indices.append(len(results))
            family=type(model.steps[-1][1]).__name__ if hasattr(model,"steps") else type(model).__name__
            results.append(ModelResult(mid,family,"READY",_direction(p),None if acc is None else round(acc,4),len(yte),0.0,_importance(model),"Chronological holdout; no random shuffle."))
        except Exception as exc:
            results.append(ModelResult(mid,type(model).__name__,"ERROR","unavailable",None,0,0.0,{},str(exc)[:160]))
    total=sum(weights) or float(len(probs) or 1); ensemble_p=sum(p*w for p,w in zip(probs,weights))/total if probs else None
    for idx,w in zip(ready_indices,weights):
        r=results[idx]; results[idx]=ModelResult(r.model_id,r.family,r.status,r.direction,r.probability_up,r.validation_accuracy,r.validation_samples,round(w/total,4),r.feature_importance,r.note)
    usable=[r for r in results if r.status=="READY"]
    agreement=(max(sum(r.direction=="bullish" for r in usable),sum(r.direction=="bearish" for r in usable))/len(usable)) if usable else None
    return {"status":"READY","horizon":horizon,"models":[asdict(r) for r in results],"ensemble":{"direction":_direction(ensemble_p),"probability_up":None if ensemble_p is None else round(ensemble_p,4),"confidence":None if agreement is None else round(float(agreement),4),"model_count":len(usable)},"features":list(FEATURE_NAMES),"validation":{"method":"chronological holdout","train_samples":len(ytr),"test_samples":len(yte)}}
