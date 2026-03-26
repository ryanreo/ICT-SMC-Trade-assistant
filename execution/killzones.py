from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)

# Standard ICT Killzones mapped to UTC times natively to avoid timezone shifts during processing.
KILLZONES_UTC = {
    "LONDON_OPEN": (time(7, 0), time(10, 0)),  # Approx 02:00 - 05:00 EST in UTC
    "NEW_YORK_OPEN": (time(12, 0), time(15, 0)) # Approx 07:00 - 10:00 EST in UTC
}

def is_within_killzone(current_time_utc: datetime) -> bool:
    """
    Determines if the current timestamp resides inside an institutional volume window.
    """
    t = current_time_utc.time()
    
    for zone, (start, end) in KILLZONES_UTC.items():
        if start <= t <= end:
            logger.debug(f"Time {t} matches active Killzone: {zone}")
            return True
            
    logger.debug(f"Time {t} is outside all approved killzones.")
    return False

def confirm_session_execution(current_time_utc: datetime) -> bool:
    """
    Enforces the chronological filtering matrix. Trades originating outside
    of high-volume session overlaps are systematically stripped of execution rights.
    """
    return is_within_killzone(current_time_utc)
