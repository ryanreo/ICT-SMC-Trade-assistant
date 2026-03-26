import os
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import asyncio
from dotenv import load_dotenv

from core.data.data_ingestion import MT5DataFetcher
from core.structure.swing_points import detect_swing_points
from core.structure.market_structure import identify_market_structure
from core.patterns.fvg import detect_fvgs
from core.patterns.liquidity import map_liquidity_pools
from core.patterns.order_blocks import identify_order_blocks, apply_discount_premium
from ai.llm_client import LLMConfirmationArbiter

load_dotenv()

def simulate_historical_period(symbol="XAUUSD.m", timeframe=mt5.TIMEFRAME_M15):
    print(f"Initializing Historical Backtest Protocol for {symbol}...")
    
    fetcher = MT5DataFetcher()
    if not fetcher.connect(): 
        print("Data ingestion failed.")
        return
        
    mt5.symbol_select(symbol, True)
    
    # Grab 3000 historical bars
    df = fetcher.fetch_historical_candles(symbol, timeframe, 3000)
    fetcher.disconnect()
    
    if df.empty: 
        print("Empty DataFrame. Check Symbol/Broker connection.")
        return
    
    print("Aggregating Vector arrays natively...")
    # Pre-process math arrays 
    df = detect_swing_points(df, n=5)
    df = identify_market_structure(df)
    df = detect_fvgs(df, atr_threshold=0.5)
    df = map_liquidity_pools(df)
    df = apply_discount_premium(df)
    df = identify_order_blocks(df, volume_percentile=0.5)
    
    arbiter = LLMConfirmationArbiter()
    
    trades_taken = 0
    wins = 0
    losses = 0
    
    print("\nStarting chronological search for optimal SMC alignments...")
    
    # We slice out the oldest 1000 bars for context, testing sequentially.
    for i in range(1000, len(df)-50): 
        row = df.iloc[i]
        
        setup = False
        action = None
        # Broadened testing criteria to pass standard FVGs to the LLM arbiter for prediction evaluation
        if getattr(row, 'bullish_fvg', False):
            setup, action = True, "BUY"
        elif getattr(row, 'bearish_fvg', False):
            setup, action = True, "SELL"
            
        if setup:
            print(f"\n======================================")
            print(f"[Event] Found {action} setup at {row['time']}")
            
            payload = {
                "time": str(row['time']), 
                "trend": row.get('trend', 'Neutral'),
                "Distance_to_PDH": abs(row.get('close',0) - row.get('PDH', 0)),
                "Distance_to_PDL": abs(row.get('close',0) - row.get('PDL', 0)),
                "Action": action
            }
            
            print("Payload drafted. Sending to Gemini AI for strict validation...")
            decision = arbiter.evaluate_setup(payload)
            
            if decision.signal_validity:
                trades_taken += 1
                entry = decision.entry_price
                sl = decision.invalidation_level
                tp = decision.liquidity_target
                
                print(f"✅ AI Approved {action} | Entry Expected: {entry}")
                print(f"   AI Rationale: {decision.rationale}")
                
                # Check next 50 candles (Future Price Action) to map the outcome visually
                future_bars = df.iloc[i+1 : i+51]
                outcome = "TIMEOUT"
                
                for _, f_row in future_bars.iterrows():
                    high = f_row['high']
                    low = f_row['low']
                    
                    if action == "BUY":
                        if low <= sl: 
                            outcome = "LOSS"
                            break
                        if high >= tp: 
                            outcome = "WIN"
                            break
                    else: # SELL
                        if high >= sl: 
                            outcome = "LOSS"
                            break
                        if low <= tp: 
                            outcome = "WIN"
                            break
                            
                print(f"--> OUTCOME AFTER EXECUTION: {outcome}")
                
                if outcome == "WIN": wins += 1
                elif outcome == "LOSS": losses += 1
                
                # Cap testing to save Gemini API rate limits immediately
                if trades_taken >= 10: 
                    print("\nTest Cap reached (10 live validations complete).")
                    break
            else:
                print(f"❌ AI Rejected Setup. Score: {decision.confidence_score}. Continuing search...")
                
    print(f"\n======================================")
    print(f"Historical Simulation Complete.")
    print(f"Total AI Approvals Executed: {trades_taken} | Wins: {wins} | Losses: {losses}")

if __name__ == '__main__':
    simulate_historical_period()
