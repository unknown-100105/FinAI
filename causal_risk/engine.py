from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class CausalNode:
    node_id: str
    label: str
    kind: str

NODES=[
 CausalNode("rates","Central-bank rates","macro"),CausalNode("usd","USD / INR","macro"),
 CausalNode("oil","Energy prices","commodity"),CausalNode("supply","East Asia supply","supply"),
 CausalNode("credit","Credit spreads","funding"),CausalNode("liquidity","Market liquidity","market"),
 CausalNode("equity","Equity risk","market"),CausalNode("portfolio","Portfolio drawdown","outcome"),
]
EDGES=[("rates","credit",.72),("rates","equity",.64),("usd","oil",.35),("usd","equity",.41),("oil","credit",.28),("oil","equity",.52),("supply","oil",.23),("supply","liquidity",.61),("credit","liquidity",.68),("credit","equity",.57),("liquidity","equity",.74),("equity","portfolio",.83)]

def _clamp(x:float,lo=-100.0,hi=100.0)->float:
 return max(lo,min(hi,x))

def run_counterfactual(shock:Dict[str,float], allocation:Dict[str,float])->Dict:
 rates=shock.get("rates",0)/100; supply=shock.get("supply",0)/100; oil=shock.get("oil",0)/100; credit=shock.get("credit",0)/100; usd=shock.get("usd",0)/100
 liquidity=_clamp(-(rates*18+supply*22+credit*24+oil*8+usd*7))
 equity=_clamp(-(rates*13+supply*17+oil*11+credit*21+usd*8)+liquidity*.24)
 debt=_clamp(-(rates*5+credit*16)+oil*2-liquidity*.08)
 drawdown=(allocation.get("equity",0)*equity+allocation.get("debt",0)*debt+allocation.get("gold",0)*(-usd*3-rates*2+oil*2))/100
 systemic=_clamp(abs(liquidity)*.34+abs(equity)*.32+abs(debt)*.18+abs(drawdown)*.16,0,100)
 return {"systemic_stress":round(systemic,3),"channels":{"liquidity":round(liquidity,3),"equity":round(equity,3),"debt":round(debt,3),"portfolio":round(drawdown,3)},"assumptions":"Transparent structural coefficients; research scenario, not a forecast."}

def graph_snapshot()->Dict:
 return {"nodes":[n.__dict__ for n in NODES],"edges":[{"source":a,"target":b,"weight":w} for a,b,w in EDGES],"engine":"structural-causal-propagation-v0.1","learned_components_status":"not_production_validated"}
