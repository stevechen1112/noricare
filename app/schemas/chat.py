from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: Optional[Dict[str, Any]] = None  # Previous report data
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list) # Chat history [{"role": "user", "content": "..."}]

class ChatResponse(BaseModel):
    reply: str
