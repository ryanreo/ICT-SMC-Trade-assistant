import os
import json
import urllib.request
import logging

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """
    Natively dispatches formatted JSON embed messages to the user's Discord server 
    using standard Python URLlib to bypass heavy third-party dependencies.
    """
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    def send_message(self, message: str, embed_color: int = 3447003, title: str = "ICT-SMC AI System Update"):
        if not self.webhook_url:
            return
            
        payload = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": embed_color
            }]
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.webhook_url, 
            data=data, 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        except Exception as e:
            logger.error(f"Failed to push Discord notification natively: {e}")
