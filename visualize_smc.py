import os
import pandas as pd
import plotly.graph_objects as go
import MetaTrader5 as mt5
from dotenv import load_dotenv

from core.data.data_ingestion import MT5DataFetcher
from core.structure.swing_points import detect_swing_points
from core.structure.market_structure import identify_market_structure
from core.patterns.fvg import detect_fvgs

load_dotenv()

def plot_timeframe(fetcher, symbol, tf_name, tf_code, num_candles=200):
    print(f"Generating chart for {symbol} on {tf_name} timeframe...")
    df = fetcher.fetch_historical_candles(symbol, tf_code, num_candles)

    if df.empty:
        print(f"No data found for {tf_name}.")
        return

    # Apply core computational math
    df = detect_swing_points(df, n=5)
    df = identify_market_structure(df)
    df = detect_fvgs(df, atr_threshold=0.3) # lowered threshold for visualization density on low TF
    
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="Price"
    )])
    
    # Plot Localized Swings
    sh = df.dropna(subset=['swing_high_price'])
    fig.add_trace(go.Scatter(
        x=sh['time'], y=sh['swing_high_price'], 
        mode='markers', marker=dict(color='blue', symbol='triangle-down', size=12), 
        name='Swing Highs'
    ))
    
    sl = df.dropna(subset=['swing_low_price'])
    fig.add_trace(go.Scatter(
        x=sl['time'], y=sl['swing_low_price'], 
        mode='markers', marker=dict(color='orange', symbol='triangle-up', size=12), 
        name='Swing Lows'
    ))
    
    shapes = []
    bullish_fvgs = df[df['bullish_fvg'] == True]
    for _, row in bullish_fvgs.iterrows():
        shapes.append(dict(
            type="rect", x0=row['time'], y0=row['bullish_fvg_bottom'],
            x1=df['time'].iloc[-1], y1=row['bullish_fvg_top'],  
            fillcolor="rgba(0, 255, 0, 0.2)", line=dict(width=0), layer="below"
        ))
        
    bearish_fvgs = df[df['bearish_fvg'] == True]
    for _, row in bearish_fvgs.iterrows():
        shapes.append(dict(
            type="rect", x0=row['time'], y0=row['bearish_fvg_bottom'],
            x1=df['time'].iloc[-1], y1=row['bearish_fvg_top'], 
            fillcolor="rgba(255, 0, 0, 0.2)", line=dict(width=0), layer="below"
        ))
        
    fig.update_layout(
        title=f"Institutional Order Flow: {symbol} ({tf_name}) - Swing Nodes & FVGs",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        shapes=shapes,
        template='plotly_dark'
    )
    
    filename = f"smc_chart_{tf_name}.html"
    fig.write_html(filename, auto_open=True)
    print(f"✅ Saved and launched {filename}")

def plot_all_scales():
    fetcher = MT5DataFetcher()
    if not fetcher.connect():
        print("Failed to connect to MT5.")
        return
        
    symbol = "XAUUSD.m"
    mt5.symbol_select(symbol, True)
    
    timeframes = [
        ("1_Day", mt5.TIMEFRAME_D1),
        ("1_Hour", mt5.TIMEFRAME_H1),
        ("5_Minute", mt5.TIMEFRAME_M5),
        ("1_Minute", mt5.TIMEFRAME_M1)
    ]
    
    for tf_name, tf_code in timeframes:
        plot_timeframe(fetcher, symbol, tf_name, tf_code, num_candles=250)
        
    fetcher.disconnect()
    print("\nAll interactive timeframe charts generated successfully!")

if __name__ == '__main__':
    plot_all_scales()
