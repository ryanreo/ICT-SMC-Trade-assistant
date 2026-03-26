import os

def calculate_position_size(
    account_balance: float,
    entry_price: float,
    invalidation_level: float,
    asset_point_value: float,
    risk_percent: float = None
) -> float:
    """
    Calculates dynamic lot sizing based purely on distance from entry to invalidation
    guaranteeing only exactly `risk_percent` equity loss if stopped out.
    """
    if risk_percent is None:
        risk_percent = float(os.getenv("RISK_PER_TRADE_PERCENT", 1.0))
        
    risk_amount = account_balance * (risk_percent / 100.0)
    
    stop_distance_points = abs(entry_price - invalidation_level)
    if stop_distance_points == 0:
        return 0.0 # Prevent division by zero mathematically
        
    monetary_risk_per_unit = stop_distance_points * asset_point_value
    
    if monetary_risk_per_unit == 0:
        return 0.0
        
    ideal_position_size = risk_amount / monetary_risk_per_unit
    
    # Typically broker APIs require rounding to 2 decimal places for standard lots
    return round(ideal_position_size, 2)

def pad_stop_loss_with_atr(
    action: str, 
    structural_invalidation: float, 
    current_atr: float, 
    multiplier: float = None
) -> float:
    """
    Applies an ATR-based buffer to structural stops to survive broker spread 
    widening and localized noise near liquidity levels.
    """
    if multiplier is None:
        multiplier = float(os.getenv("ATR_STOP_PADDING_MULTIPLIER", 1.5))
        
    buffer = current_atr * multiplier
    
    if action.upper() == "BUY":
        return structural_invalidation - buffer
    else: # SELL
        return structural_invalidation + buffer
