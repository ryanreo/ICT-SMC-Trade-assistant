from pydantic import BaseModel, Field
from typing import Literal

class AITradeDecision(BaseModel):
    """
    JSON Schema rigidly enforcing the LLM arbiter's output payload to the Python execution module.
    """
    signal_validity: bool = Field(..., description="Returns True to proceed with trade execution routing, or False to abort.")
    action: Literal['BUY', 'SELL'] = Field(..., description="Constrained strictly to Enum values: BUY or SELL.")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence metric assessing the confluence of the data (0-100). The bot executes if score >= 80.")
    entry_price: float = Field(..., description="Precise price coordinate to anchor the limit order (e.g., FVG boundary or OTE).")
    invalidation_level: float = Field(..., description="Hard stop-loss coordinate structurally placed beyond OB or sweep extreme.")
    liquidity_target: float = Field(..., description="Take-profit coordinate aimed at opposing external liquidity pool (e.g. PDH/PDL).")
    rationale: str = Field(..., description="Chain-of-thought justification logging for post-trade analysis and tuning.")
