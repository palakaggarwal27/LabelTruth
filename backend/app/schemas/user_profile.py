from typing import List, Optional
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    dietary_preferences: List[str] = Field(default_factory=list, description='e.g., Vegan, Vegetarian, Jain, Gluten-Free')
    medical_conditions: List[str] = Field(default_factory=list, description='e.g., Type 2 Diabetes, Hypertension, Celiac')
    allergies: List[str] = Field(default_factory=list, description='e.g., Peanuts, Tree Nuts, Soy, Dairy, Gluten')
    custom_avoid_list: List[str] = Field(default_factory=list, description='Specific ingredients to flag, e.g., Palm Oil, Maltodextrin, INS 150d')
