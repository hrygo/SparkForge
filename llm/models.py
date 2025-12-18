from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class LLMRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: Optional[Usage] = None
    finish_reason: Optional[str] = None
    raw: Optional[Any] = None
