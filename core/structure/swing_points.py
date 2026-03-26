import pandas as pd
import numpy as np

def detect_swing_points(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Identifies localized Swing Highs and Swing Lows based on an n-period window.
    
    A point is a Swing High if its high is strictly greater than the highs
    of the n preceding and n succeeding periods.
    A point is a Swing Low if its low is strictly lower than the lows
    of the n preceding and n succeeding periods.
    """
    # Create leading and lagging windows using rolling
    
    # Forward and backward rolling max for high
    rolling_max_past = df['high'].rolling(window=n, min_periods=n).max().shift(1)
    # Using iloc[::-1] to do forward rolling max
    rolling_max_future = df['high'].iloc[::-1].rolling(window=n, min_periods=n).max().shift(1).iloc[::-1]
    
    # Swing High condition: High is greater than both the past max and future max
    df['is_swing_high'] = (df['high'] > rolling_max_past) & (df['high'] > rolling_max_future)
    
    # Forward and backward rolling min for low
    rolling_min_past = df['low'].rolling(window=n, min_periods=n).min().shift(1)
    rolling_min_future = df['low'].iloc[::-1].rolling(window=n, min_periods=n).min().shift(1).iloc[::-1]
    
    # Swing Low condition: Low is less than both the past min and future min
    df['is_swing_low'] = (df['low'] < rolling_min_past) & (df['low'] < rolling_min_future)
    
    # Retain the literal price values for these structural points
    df['swing_high_price'] = np.where(df['is_swing_high'], df['high'], np.nan)
    df['swing_low_price'] = np.where(df['is_swing_low'], df['low'], np.nan)
    
    return df
