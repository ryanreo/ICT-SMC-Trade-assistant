import MetaTrader5 as mt5
import os
import asyncio
import logging
from ai.schemas import AITradeDecision

logger = logging.getLogger(__name__)

class OrderRouter:
    """
    Generates and executes broker-specific trading commands based on validated AI data 
    with robust error resilience, exponential backoffs, and disconnection recovery.
    """
    def __init__(self):
        self.environment = os.getenv("TRADE_ENVIRONMENT", "paper_trading")

    async def execute_trade_with_retry(self, symbol: str, decision: AITradeDecision, lot_size: float, max_retries: int = 3) -> bool:
        """
        Translates internal structures into direct market interaction rules with async delay retries.
        """
        for attempt in range(1, max_retries + 1):
            try:
                if self.environment == "paper_trading":
                    logger.info(f"[PAPER] Setup Executed: {decision.action} {lot_size} lots on {symbol} @ {decision.entry_price}")
                    logger.info(f"[PAPER] SL: {decision.invalidation_level} | TP: {decision.liquidity_target}")
                    return True
                
                # LIVE EXECUTION LOGIC
                action_type = mt5.ORDER_TYPE_BUY if decision.action == 'BUY' else mt5.ORDER_TYPE_SELL
                
                request = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": float(lot_size),
                    "type": action_type,
                    "price": float(decision.entry_price),
                    "sl": float(decision.invalidation_level),
                    "tp": float(decision.liquidity_target),
                    "magic": 234000,
                    "comment": "ICT-SMC-AI Exec",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                logger.info(f"Attempting Live Execution (Attempt {attempt}/{max_retries})")
                result = mt5.order_send(request)
                
                if result is None:
                    error_code = mt5.last_error()
                    logger.warning(f"MT5 server disconnected or unresponsive. Code: {error_code}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    logger.warning(f"Order Send failed with code: {result.retcode}. Retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
                logger.info(f"✅ Live Execution Verified for {symbol}: {decision.action}")
                return True
                
            except Exception as e:
                logger.error(f"Router Exception: {e}")
                await asyncio.sleep(2 ** attempt)
                
        logger.error(f"❌ Failed to execute trade after {max_retries} attempts.")
        return False
