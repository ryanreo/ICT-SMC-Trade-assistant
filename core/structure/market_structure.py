import pandas as pd
import numpy as np
from numba import njit

@njit
def map_trend_and_shifts(close_prices, swing_highs, swing_lows):
    n = len(close_prices)
    trend = np.zeros(n, dtype=np.int32) # 1 Bullish, -1 Bearish, 0 Neutral
    bos = np.zeros(n, dtype=np.int32) 
    choch = np.zeros(n, dtype=np.int32)
    
    current_trend = 0
    last_sh = np.nan
    last_sl = np.nan
    
    for i in range(n):
        # Update last known swings
        if not np.isnan(swing_highs[i]):
            last_sh = swing_highs[i]
        if not np.isnan(swing_lows[i]):
            last_sl = swing_lows[i]
            
        c = close_prices[i]
        
        # Bullish rules (Close > Previous Swing High)
        if current_trend >= 0 and not np.isnan(last_sh) and c > last_sh:
            bos[i] = 1 # Bullish BOS
            current_trend = 1
            last_sh = np.nan # Consume
            
        # Bearish rules (Close < Previous Swing Low)
        elif current_trend <= 0 and not np.isnan(last_sl) and c < last_sl:
            bos[i] = -1 # Bearish BOS
            current_trend = -1
            last_sl = np.nan # Consume
            
        # CHoCH (Trend Reversals)
        if current_trend == 1 and not np.isnan(last_sl) and c < last_sl:
            choch[i] = -1 # Bearish CHoCH
            current_trend = -1
            last_sl = np.nan
        elif current_trend == -1 and not np.isnan(last_sh) and c > last_sh:
            choch[i] = 1 # Bullish CHoCH
            current_trend = 1
            last_sh = np.nan
            
        trend[i] = current_trend
        
    return trend, bos, choch

def identify_market_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Programmatic evaluation of Trend, BOS, and CHoCH over a dataframe
    implementing the strict closing price validations from the initial manifesto logic.
    """
    trend, bos, choch = map_trend_and_shifts(
        df['close'].values, 
        df['swing_high_price'].fillna(np.nan).values, 
        df['swing_low_price'].fillna(np.nan).values
    )
    
    df['trend_num'] = trend
    df['trend'] = np.where(df['trend_num'] == 1, 'Bullish', np.where(df['trend_num'] == -1, 'Bearish', 'Neutral'))
    df['is_bullish_break'] = bos == 1
    df['is_bearish_break'] = bos == -1
    df['is_bullish_choch'] = choch == 1
    df['is_bearish_choch'] = choch == -1
    
    # Store persistent last swings for premium/discount matrices
    df['last_swing_high'] = df['swing_high_price'].ffill()
    df['last_swing_low'] = df['swing_low_price'].ffill()
    
    return df
