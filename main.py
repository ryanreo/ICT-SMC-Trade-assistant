import os
import asyncio
import logging
from datetime import datetime, timezone
import pandas as pd
import MetaTrader5 as mt5

from core.data.data_ingestion import MT5DataFetcher
from core.structure.swing_points import detect_swing_points
from core.structure.market_structure import identify_market_structure
from core.patterns.fvg import detect_fvgs
from core.patterns.liquidity import map_liquidity_pools
from core.patterns.order_blocks import identify_order_blocks, apply_discount_premium

from ai.llm_client import LLMConfirmationArbiter
from execution.killzones import confirm_session_execution
from execution.risk_manager import calculate_position_size, pad_stop_loss_with_atr
from execution.router import OrderRouter
from execution.notifier import DiscordNotifier
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ICTTradingBot:
    def __init__(self, symbol="XAUUSD.m", timeframe=mt5.TIMEFRAME_M15):
        self.symbol = symbol
        self.timeframe = timeframe
        self.fetcher = MT5DataFetcher()
        self.arbiter = LLMConfirmationArbiter()
        self.router = OrderRouter()
        self.notifier = DiscordNotifier()
        
    def start(self):
        logger.info(f"Initializing Multi-Timeframe institutional logic on {self.symbol}...")
        self.notifier.send_message(f"🚀 **ICT-SMC Trading Bot Initialized**\nSuccessfully tethered to MT5. Actively mapping multi-timeframe arrays on {self.symbol} targeting extreme premium/discount nodes 24/7.", 3447003, "System Boot")
        
        if not self.fetcher.connect():
            logger.error("Data connection failed. Cannot proceed.")
            self.notifier.send_message("❌ **Fatal Error:** MT5 connection severed. Shutting down.", 15158332, "Terminal Disconnect")
            return

        try:
            asyncio.run(self.trading_loop())
        except KeyboardInterrupt:
            logger.info("Bot execution halt requested.")
            self.notifier.send_message("🛑 **Graceful Shutdown**: The user manually terminated the live scanning protocol via the terminal.", 15158332, "Halt Requested")
        finally:
            self.fetcher.disconnect()

    async def trading_loop(self):
        logger.info("Macro structure arrays initialized. Awaiting market synchronization...")
        
        while True:
            # 1. HIGHER TIME FRAME (Daily) extraction for macro bias
            df_daily = self.fetcher.fetch_historical_candles(self.symbol, mt5.TIMEFRAME_D1, 300)
            htf_payload = {}
            if not df_daily.empty:
                df_daily = detect_swing_points(df_daily, n=3)
                df_daily = identify_market_structure(df_daily)
                df_daily = detect_fvgs(df_daily, atr_threshold=0.5)
                df_daily = map_liquidity_pools(df_daily)
                df_daily = identify_order_blocks(df_daily)
                df_daily = apply_discount_premium(df_daily)
                daily_bar = df_daily.iloc[-1]
                
                htf_bias = daily_bar.get('trend', 'Neutral')
                
                # Recent D1 BOS/CHoCH events (last 5 daily bars)
                recent_daily = df_daily.tail(5)
                d1_bos_bull = bool(recent_daily['is_bullish_break'].any())
                d1_bos_bear = bool(recent_daily['is_bearish_break'].any())
                d1_choch_bull = bool(recent_daily['is_bullish_choch'].any())
                d1_choch_bear = bool(recent_daily['is_bearish_choch'].any())
                
                htf_payload = {
                    "D1_Trend": htf_bias,
                    "D1_Recent_Bullish_BOS": d1_bos_bull,
                    "D1_Recent_Bearish_BOS": d1_bos_bear,
                    "D1_Recent_Bullish_CHoCH": d1_choch_bull,
                    "D1_Recent_Bearish_CHoCH": d1_choch_bear,
                    "D1_In_Premium": bool(daily_bar.get('in_premium', False)),
                    "D1_In_Discount": bool(daily_bar.get('in_discount', False)),
                    "D1_Equilibrium": float(daily_bar.get('equilibrium', 0)),
                    "D1_Bullish_FVG_Active": bool(daily_bar.get('bullish_fvg', False)),
                    "D1_Bearish_FVG_Active": bool(daily_bar.get('bearish_fvg', False)),
                    "D1_Bullish_FVG_Top": float(daily_bar.get('bullish_fvg_top', 0)) if not pd.isna(daily_bar.get('bullish_fvg_top', float('nan'))) else None,
                    "D1_Bullish_FVG_Bottom": float(daily_bar.get('bullish_fvg_bottom', 0)) if not pd.isna(daily_bar.get('bullish_fvg_bottom', float('nan'))) else None,
                    "D1_Bearish_FVG_Top": float(daily_bar.get('bearish_fvg_top', 0)) if not pd.isna(daily_bar.get('bearish_fvg_top', float('nan'))) else None,
                    "D1_Bearish_FVG_Bottom": float(daily_bar.get('bearish_fvg_bottom', 0)) if not pd.isna(daily_bar.get('bearish_fvg_bottom', float('nan'))) else None,
                    "D1_Bullish_iVG": bool(daily_bar.get('bullish_ivg', False)),
                    "D1_Bearish_iVG": bool(daily_bar.get('bearish_ivg', False)),
                    "D1_Bullish_OB_Active": bool(daily_bar.get('is_bullish_ob', False)),
                    "D1_Bearish_OB_Active": bool(daily_bar.get('is_bearish_ob', False)),
                    "D1_Sweep_PDH": bool(daily_bar.get('sweep_pdh', False)),
                    "D1_Sweep_PDL": bool(daily_bar.get('sweep_pdl', False)),
                    "D1_Last_Swing_High": float(daily_bar.get('last_swing_high', 0)),
                    "D1_Last_Swing_Low": float(daily_bar.get('last_swing_low', 0)),
                }
            else:
                htf_bias = "Unknown"
                htf_payload = {"D1_Trend": "Unknown"}

            # 2. LOWER TIME FRAME (M15) execution arrays
            df = self.fetcher.fetch_historical_candles(self.symbol, self.timeframe, 1000)
            
            if df.empty:
                await asyncio.sleep(60)
                continue
                
            # Programmatic Market Structure Analysis (LTF)
            df = detect_swing_points(df, n=5)
            df = identify_market_structure(df)
            df = detect_fvgs(df, atr_threshold=0.5)
            df = map_liquidity_pools(df)
            df = apply_discount_premium(df)

            current_bar = df.iloc[-1]
            
            setup_found = False
            action = None
            
            # FVG Trigger Logic mapping 
            if current_bar.get('bullish_fvg', False):
                setup_found = True
                action = 'BUY'
            elif current_bar.get('bearish_fvg', False):
                setup_found = True
                action = 'SELL'
                
            if setup_found:
                current_time = datetime.now(timezone.utc)
                if not confirm_session_execution(current_time):
                    logger.info("Setup detected outside Killzone. 24/7 overriding time constraints.")
                    
                logger.info(f"LTF {action} structure validated. Passing to Arbiter against Daily Bias ({htf_bias})...")
                
                # Build enriched LTF (M15) context
                ltf_payload = {
                    "LTF_Trend": current_bar.get('trend', 'Neutral'),
                    "LTF_Bullish_FVG": bool(current_bar.get('bullish_fvg', False)),
                    "LTF_Bearish_FVG": bool(current_bar.get('bearish_fvg', False)),
                    "LTF_Bullish_iVG": bool(current_bar.get('bullish_ivg', False)),
                    "LTF_Bearish_iVG": bool(current_bar.get('bearish_ivg', False)),
                    "LTF_In_Premium": bool(current_bar.get('in_premium', False)),
                    "LTF_In_Discount": bool(current_bar.get('in_discount', False)),
                    "LTF_Equilibrium": float(current_bar.get('equilibrium', 0)),
                    "LTF_Sweep_PDH": bool(current_bar.get('sweep_pdh', False)),
                    "LTF_Sweep_PDL": bool(current_bar.get('sweep_pdl', False)),
                    "LTF_Close": float(current_bar.get('close', 0)),
                    "Distance_to_PDH": abs(current_bar.get('close', 0) - current_bar.get('PDH', 0)),
                    "Distance_to_PDL": abs(current_bar.get('close', 0) - current_bar.get('PDL', 0)),
                }
                
                payload = {
                    "time": str(current_time),
                    "Action": action,
                    **htf_payload,
                    **ltf_payload,
                }
                
                decision = self.arbiter.evaluate_setup(payload)
                
                if decision.signal_validity:
                    self.notifier.send_message(f"**✅ Gemini AI Overwhelmingly Approved {action} on {self.symbol}**\n\n**Entry:** {decision.entry_price}\n**Invalidation:** {decision.invalidation_level}\n**Take Profit:** {decision.liquidity_target}\n\n**AI Rationale:**\n*{decision.rationale}*", 3066993, "High-Probability Execution Dispatched")
                    
                    account_balance = 10000.0 
                    asset_point_value = 10.0 
                    current_atr = current_bar.get('high', 0) - current_bar.get('low', 0)
                    
                    sl_padded = pad_stop_loss_with_atr(
                        decision.action, decision.invalidation_level, current_atr, multiplier=1.5
                    )
                    
                    lot_size = calculate_position_size(
                        account_balance, decision.entry_price, sl_padded, asset_point_value, risk_percent=1.0
                    )
                    
                    await self.router.execute_trade_with_retry(self.symbol, decision, lot_size)
                    await asyncio.sleep(300) 
                else:
                    self.notifier.send_message(
                        f"**❌ Gemini AI Rejected M15 {action} on {self.symbol}**\n\n"
                        f"**LTF Trend:** {current_bar.get('trend', 'Neutral')}\n"
                        f"**HTF Daily Bias:** {htf_bias}\n"
                        f"**AI Confidence Score:** {decision.confidence_score}/100\n\n"
                        f"**AI Rationale:**\n*{decision.rationale}*",
                        15158332, 
                        "Setup Rejected"
                    )
            
            logger.info(f"Heartbeat -> Cycle Complete for {current_bar['time']} (D1 Bias: {htf_bias}). Waiting for new M15 setups...")
            await asyncio.sleep(60)

if __name__ == "__main__":
    load_dotenv()
    bot = ICTTradingBot()
    bot.start()
