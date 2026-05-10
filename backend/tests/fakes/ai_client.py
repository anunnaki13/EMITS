"""FakeAIClient — canned responses for Phase 4 (D-05).

Routes by system_prompt keyword (case-insensitive substring match):
'blend' -> valid JSON per CONS-blending-ai-output;
any other prompt -> plain Indonesian string for /api/ai/query.

Zero outbound HTTP. Zero LLM budget consumed.
"""

BLENDING_JSON = (
    '{"recommendation":[{"supplier":"PT TEST SUPPLIER","source":"Vessel",'
    '"type":"LRC","percentage":100.0,"tonnage":10000.0,"gcv":4200,'
    '"ash":5.0,"sulphur":0.3,"total_moisture":30.5,'
    '"inherent_moisture":15.0,"volatile_matter":35.0,"fixed_carbon":25.0}],'
    '"predicted_quality":{"gcv":4200,"ash":5.0,"sulphur":0.3,'
    '"total_moisture":30.5,"inherent_moisture":15.0,'
    '"volatile_matter":35.0,"fixed_carbon":25.0},'
    '"meets_target":true,'
    '"reasoning":"Fake blending response for Phase 4 testing."}'
)

GENERAL_RESPONSE = "Analisis umum: data tersedia di sistem (Phase 4 fake)."


class FakeAIClient:
    async def send_message(
        self, session_id: str, system_prompt: str, user_message: str
    ) -> str:
        if "blend" in (system_prompt or "").lower() or "blend" in (session_id or "").lower():
            return BLENDING_JSON
        return GENERAL_RESPONSE
