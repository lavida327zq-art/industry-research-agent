from typing import Dict, List
from pydantic import BaseModel, Field

class ResearchState(BaseModel):
    topic: str = Field(default="")
    raw_data: List[str] = Field(default_factory=list)
    analysis: Dict = Field(default_factory=dict)
    final_report: str = Field(default="")
    next_agent: str = Field(default="")
