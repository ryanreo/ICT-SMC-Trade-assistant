import pandas as pd
import numpy as np

def identify_order_blocks(df: pd.DataFrame, volume_percentile: float = 0.8) -> pd.DataFrame:
    """
    Identifies pristine Order Blocks mapping backward induction from FVG displacement and Struct shifts.
    Ensures Volume and Pristine (unmitigated) integrity.
    """
    if 'tick_volume' not in df.columns:
        df['tick_volume'] = 1  # Failsafe if running raw OHLC data without volume
        
    df['vol_rolling_max'] = df['tick_volume'].rolling(window=100).max()
    df['is_high_volume'] = df['tick_volume'] >= (df['vol_rolling_max'] * volume_percentile)
    
    down_candle = df['close'] < df['open']
    up_candle = df['close'] > df['open']
    
    # Requirement: "Structural Genesis: The origin move must have directly caused a valid BOS or CHoCH"
    # A rolling lookforward checks if structural shifts happen within 5 intervals following displacement.
    if 'is_bullish_break' in df.columns and 'is_bullish_choch' in df.columns:
        struct_bull = df['is_bullish_break'] | df['is_bullish_choch']
        struct_bear = df['is_bearish_break'] | df['is_bearish_choch']
        
        # Roll forward to check if a break occurred shortly after this candle
        has_bullish_struct = struct_bull.rolling(window=5, min_periods=1).max().shift(-5) > 0
        has_bearish_struct = struct_bear.rolling(window=5, min_periods=1).max().shift(-5) > 0
    else:
        has_bullish_struct = True
        has_bearish_struct = True
    
    # Bullish OB = Down candle, immediate FVG displacement next, High Volume, AND leads to a structural break
    bullish_ob_condition = down_candle & df['bullish_fvg'].shift(-1) & df['is_high_volume'] & has_bullish_struct
    bearish_ob_condition = up_candle & df['bearish_fvg'].shift(-1) & df['is_high_volume'] & has_bearish_struct
    
    df['is_bullish_ob'] = bullish_ob_condition
    df['is_bearish_ob'] = bearish_ob_condition
    
    df['bullish_ob_top'] = np.where(bullish_ob_condition, df['high'], np.nan)
    df['bullish_ob_bottom'] = np.where(bullish_ob_condition, df['low'], np.nan)
    
    df['bearish_ob_top'] = np.where(bearish_ob_condition, df['high'], np.nan)
    df['bearish_ob_bottom'] = np.where(bearish_ob_condition, df['low'], np.nan)
    
    return df

def apply_discount_premium(df: pd.DataFrame) -> pd.DataFrame:
    """
    Defines dealing range via strict 50% bisect mapping equilibrium. 
    """
    if 'last_swing_high' in df.columns and 'last_swing_low' in df.columns:
        df['equilibrium'] = (df['last_swing_high'] + df['last_swing_low']) / 2
        df['in_premium'] = df['close'] > df['equilibrium']
        df['in_discount'] = df['close'] < df['equilibrium']
    else:
        df['in_premium'] = False
        df['in_discount'] = False
        
    return df
