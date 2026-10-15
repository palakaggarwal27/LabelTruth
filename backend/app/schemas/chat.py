from typing import List, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str # user or assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    user_profile: Optional[dict] = None
    product_context: Optional[dict] = None

class ChatResponse(BaseModel):
    reply: str
