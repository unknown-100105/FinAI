from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from causal_risk.engine import graph_snapshot, run_counterfactual

router=APIRouter(prefix="/api/v1/causal-risk",tags=["causal-risk"])

class CounterfactualRequest(BaseModel):
 shock: Dict[str,float]=Field(default_factory=dict)
 allocation: Dict[str,float]=Field(default_factory=lambda:{"equity":55,"debt":30,"gold":10,"cash":5})

@router.get("/graph")
def graph(): return graph_snapshot()

@router.post("/counterfactual")
def counterfactual(request:CounterfactualRequest):
 if any(not isinstance(v,(int,float)) for v in request.shock.values()):
  raise HTTPException(status_code=422,detail="Shock values must be numeric.")
 return run_counterfactual(request.shock,request.allocation)
