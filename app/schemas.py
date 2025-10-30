from __future__ import annotations
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

class Event(BaseModel):
    """Message published by MonitorAgent when something suspicious occurs."""
    type: str = Field(default="ANOMALY_DETECTED")
    ts: str
    flow_id: str
    features: Dict[str, float]
    # Either numeric sores or a dict with rule hits; keep it flexible for later
    score: Dict[str, Union[float, List[str]]]
    
class Verdict(BaseModel):
    type: str = "VERDICT"
    flow_id: str
    classification: str
    confidence: float
    citations: List[str] = []
    explanation: str
    
class Action(BaseModel):
    type: str = "ACTION_RECOMMENDATION"
    flow_id: str
    action: str # e.g., BLOCK_IP | THROTTLE | ALERT | NOOP
    params: Dict[str, Union[str, int, float]]
    policy: str # e.g., heuristic_v1 or rl_policy_v1
    reward: Optional[float] = None # filled in during RL training/eval