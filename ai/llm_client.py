import os
import json
from google import genai
from google.genai import types
from .schemas import AITradeDecision
from .prompts import SYSTEM_PERSONA, build_market_context_prompt

class LLMConfirmationArbiter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.confidence_threshold = int(os.getenv("CONFIDENCE_THRESHOLD", 80))

    def evaluate_setup(self, compiled_market_state: dict) -> AITradeDecision:
        user_prompt = build_market_context_prompt(compiled_market_state)
        
        try:
            print("   [GenAI Engine] Executing zero-shot inference...", flush=True)
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PERSONA,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"): raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"): raw_text = raw_text[3:-3].strip()
                
            decision_data = json.loads(raw_text)
            decision = AITradeDecision(**decision_data)
            
            if decision.confidence_score < self.confidence_threshold:
                decision.signal_validity = False
            return decision

        except Exception as e:
            print(f"   [GenAI Warning] Validation Exception: {e}", flush=True)
            return AITradeDecision(
                signal_validity=False, action='BUY', confidence_score=0,
                entry_price=0.0, invalidation_level=0.0, liquidity_target=0.0, rationale=str(e)
            )
