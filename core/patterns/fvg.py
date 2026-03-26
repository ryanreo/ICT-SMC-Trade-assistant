import pandas as pd
import numpy as np

def detect_fvgs(df: pd.DataFrame, atr_threshold: float = 1.0) -> pd.DataFrame:
    """
    Detects Fair Value Gaps (Bullish and Bearish).
    Also utilizes stateful object tracking to evaluate Inversion FVGs (iVGs).
    """
    df['body_size'] = abs(df['close'] - df['open'])
    df['avg_body'] = df['body_size'].rolling(window=14).mean()
    
    high_prev = df['high'].shift(2)
    low_next = df['low']
    low_prev = df['low'].shift(2)
    high_next = df['high']
    
    # Strict FVG bounds + velocity checks
    bullish_gap = low_next > high_prev
    bullish_displacement = df['body_size'].shift(1) > (df['avg_body'].shift(2) * atr_threshold)
    df['bullish_fvg'] = bullish_gap & bullish_displacement
    df['bullish_fvg_top'] = np.where(df['bullish_fvg'], low_next, np.nan)
    df['bullish_fvg_bottom'] = np.where(df['bullish_fvg'], high_prev, np.nan)
    
    bearish_gap = high_next < low_prev
    bearish_displacement = df['body_size'].shift(1) > (df['avg_body'].shift(2) * atr_threshold)
    df['bearish_fvg'] = bearish_gap & bearish_displacement
    df['bearish_fvg_top'] = np.where(df['bearish_fvg'], low_prev, np.nan)
    df['bearish_fvg_bottom'] = np.where(df['bearish_fvg'], high_next, np.nan)
    
    # iVG Implementation tracking states dynamically
    df['bearish_ivg'] = False
    df['bullish_ivg'] = False
    
    active_bullish_fvgs = []
    active_bearish_fvgs = []
    
    bearish_ivgs = np.zeros(len(df), dtype=bool)
    bullish_ivgs = np.zeros(len(df), dtype=bool)
    
    for i in range(len(df)):
        c = df['close'].iloc[i]
        
        # Invalidate active bullish FVG to bearish iVG
        # FVG is breached completely downwards
        for f in active_bullish_fvgs[:]:
            if c < f['bottom']:
                bearish_ivgs[i] = True
                active_bullish_fvgs.remove(f)
                
        # Invalidate active bearish FVG to bullish iVG
        # FVG is breached completely upwards
        for f in active_bearish_fvgs[:]:
            if c > f['top']:
                bullish_ivgs[i] = True
                active_bearish_fvgs.remove(f)
                
        # Add new FVGs into tracking buffer
        if df['bullish_fvg'].iloc[i]:
            active_bullish_fvgs.append({'top': df['bullish_fvg_top'].iloc[i], 'bottom': df['bullish_fvg_bottom'].iloc[i]})
        if df['bearish_fvg'].iloc[i]:
            active_bearish_fvgs.append({'top': df['bearish_fvg_top'].iloc[i], 'bottom': df['bearish_fvg_bottom'].iloc[i]})
            
    df['bearish_ivg'] = bearish_ivgs
    df['bullish_ivg'] = bullish_ivgs
                
    return df
