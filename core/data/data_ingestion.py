import os
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class MT5DataFetcher:
    """Handles connection to MT5 and fetching historical OHLCV data."""
    def __init__(self):
        self.connected = False

    def connect(self):
        """Initialize connection to MetaTrader 5 Terminal."""
        login = os.getenv("MT5_LOGIN")
        password = os.getenv("MT5_PASSWORD")
        server = os.getenv("MT5_SERVER")
        
        # If login details are not provided in env, it connects to the currently open terminal
        if login and password and server:
            self.connected = mt5.initialize(login=int(login), server=server, password=password)
        else:
            self.connected = mt5.initialize()
            
        if self.connected:
            logger.info("Successfully connected to MetaTrader 5.")
        else:
            logger.error(f"Failed to connect to MetaTrader 5: {mt5.last_error()}")
        return self.connected

    def disconnect(self):
        """Shut down MT5 connection."""
        if self.connected:
            mt5.shutdown()
            self.connected = False

    def fetch_historical_candles(self, symbol: str, timeframe: int, num_candles: int = 1000) -> pd.DataFrame:
        """Fetch historical candle rates from MT5."""
        if not self.connected:
            raise ConnectionError("MT5 is not connected.")
            
        mt5.symbol_select(symbol, True)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
        if rates is None or len(rates) == 0:
            logger.warning(f"No rates found for {symbol}")
            return pd.DataFrame()
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        return df

    def fetch_ticks(self, symbol: str, start_time: datetime, count: int = 10000) -> pd.DataFrame:
        """Fetch historical ticks, useful for simulating WebSockets or high-freq backfills."""
        if not self.connected:
            raise ConnectionError("MT5 is not connected.")
            
        ticks = mt5.copy_ticks_from(symbol, start_time, count, mt5.COPY_TICKS_ALL)
        if ticks is None or len(ticks) == 0:
            return pd.DataFrame()
            
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        return df
