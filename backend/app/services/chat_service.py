import json
import logging
from typing import Optional, List
from google import genai

from app.config import GEMINI_API_KEY
from app.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are 'LabelTruth' Clinical Nutrition and FSSAI Advisory Assistant.
You speak with the calm, evidence-based authority of a preventive health physician and food regulatory auditor.

CRITICAL PRODUCT GROUNDING RULE:
- CURRENT PRODUCT CONTEXT IS PROVIDED BELOW. You MUST ALWAYS prioritize and explicitly reference this specific product, brand name, its actual scanned ingredients, health score, deceptive claims, and FSSAI violations when answering the user.
- NEVER speak generally or in vague categories when a scanned product is in context. Specifically cite the product name (e.g., "In this Nutella Hazelnut Spread..."), its exact ingredient order (e.g. Sugar and Palm oil being 1st and 2nd), and whether it triggered a profile violation.
- If no product context is available, only then answer generally regarding ingredients, clinical nutrition, and FSSAI regulations.

STRICT SCOPE LOCK:
- You are ONLY permitted to answer questions regarding:
  1. Food ingredients, additives, INS codes, and ultra-processed food health impacts.
  2. The scanned product label, deceptive marketing, or healthier Indian alternatives.
  3. FSSAI regulations (e.g. descending weight rule, front-of-pack claims, ice cream vs frozen dessert).
  4. The user's specific health profile (allergies, diabetes, hypertension, celiac, vegan, jain).
- If the user asks ANY question outside of food, nutrition, ingredients, or FSSAI regulations (e.g., general chit-chat, coding, politics, weather, math, philosophy), you MUST REFUSE politely and immediately redirect:
  "I am strictly configured to assist with food labels, nutrition analysis, and FSSAI regulatory compliance. Please ask a question related to your dietary profile or scanned products."

FORMATTING RULES (MANDATORY TO SAVE TOKENS AND PREVENT RUN-ON PARAGRAPHS):
- NEVER output raw unformatted walls of text.
- Use clear markdown headers and bullet points.
- Structure your answer as:
  **Direct Clinical Takeaway**: 1-2 sentence core verdict referencing the scanned product.
  **Key Facts & Regulatory Reality**:
  • Bullet 1 with specific ingredient reality from this product's label (e.g., % composition, descending rank).
  • Bullet 2 with specific health impact for the user's health profile.
  **Actionable Recommendation**: 1 sentence concrete recommendation or alternative.
USER HEALTH PROFILE:
{user_profile_json}

CURRENT PRODUCT AUDIT CONTEXT (CURRENT SCANNED FOOD LABEL):
{product_context_json}
"""

class ChatService:
    def __init__(self):
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
        else:
            self.client = None

    async def chat(
        self,
        message: str,
        history: List[ChatMessage],
        user_profile: Optional[dict] = None,
        product_context: Optional[dict] = None
    ) -> str:
        if not self.client:
            msg_lower = message.lower()
            profile_info = user_profile or {}
            meds = profile_info.get('medical_conditions', [])
            allergies = profile_info.get('allergies', [])
            diets = profile_info.get('dietary_preferences', [])

            prefix_parts = []
            if meds:
                prefix_parts.append(f"Regarding your {', '.join(meds)}")
            if allergies:
                prefix_parts.append(f"and {', '.join(allergies)} allergy")
            prefix = " ".join(prefix_parts) + ": " if prefix_parts else ""

            if "palm oil" in msg_lower or "fat" in msg_lower:
                return (
                    f"{prefix}Palm oil contains over 50% saturated palmitic acid, which promotes arterial stiffness, "
                    "elevates LDL cholesterol, and worsens hepatic lipid accumulation. Under FSSAI standards, it is frequently "
                    "used to cut costs in place of milk fat in Frozen Desserts and biscuit 'cremes'."
                )
            elif "maltodextrin" in msg_lower or "sugar" in msg_lower:
                return (
                    f"{prefix}Maltodextrin has a high Glycemic Index of 105 to 110, exceeding pure glucose and table sugar (65). "
                    "It induces rapid postprandial blood sugar surges and triggers strong insulin responses, making it "
                    "especially hazardous for diabetes management."
                )
            elif "bread" in msg_lower or "maida" in msg_lower or "atta" in msg_lower:
                return (
                    f"{prefix}Under FSSAI rules, bread only requires 50% whole wheat to be labeled as 'Brown Bread'. "
                    "Many commercial brands use Refined Flour (Maida) as ingredient #1 and dye it with Caramel Colour (INS 150d)."
                )
            elif "safe" in msg_lower or "can i eat" in msg_lower:
                return (
                    f"{prefix}Please audit the first 3 ingredients under FSSAI Regulation 5(2)(b). If refined sugars, "
                    "palm fractions, or high-concern INS additives appear at the top, choose a clean whole-food alternative."
                )
            else:
                return (
                    f"{prefix}LabelTruth clinical advisory: In accordance with FSSAI regulations, always verify the descending "
                    "weight ingredient list. Watch for disguised sugars (maltodextrin, liquid glucose) and synthetic colorants like INS 150d."
                )

        system = CHAT_SYSTEM_PROMPT.replace(
            "{user_profile_json}", json.dumps(user_profile or {}, indent=2)
        ).replace(
            "{product_context_json}", json.dumps(product_context or {}, indent=2)
        )

        full_prompt = f"{system}\n\n"
        for msg in history[-6:]:
            full_prompt += f"{msg.role.upper()}: {msg.content}\n"
        full_prompt += f"USER: {message}\nASSISTANT:"

        try:
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Chat generation error: {e}")
            return "Unable to consult the clinical AI model at this moment. Please check your product label breakdown directly."

chat_service = ChatService()
