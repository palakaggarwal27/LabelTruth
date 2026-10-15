from pydantic import BaseModel, Field

class ValidateConditionRequest(BaseModel):
    condition: str = Field(..., description="User entered condition or ingredient to avoid")

class ValidateConditionResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the term is a recognized health condition, allergy, or food additive")
    standardized_name: str = Field(..., description="Clinically recognized or standard regulatory name")
    reason: str = Field(..., description="Brief explanation of the condition, allergy, or ingredient")
