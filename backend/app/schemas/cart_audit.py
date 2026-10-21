from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.analysis import HealthierAlternative

class CartItemAudit(BaseModel):
    product_name: str = Field(description="Name of item in cart")
    quantity: int = Field(default=1, description="Quantity in cart")
    health_score: int = Field(description="Nutritional health score 0-100")
    personalized_verdict: str = Field(description="SAFE FOR YOU, CAUTION, or AVOID (VIOLATES PROFILE)")
    key_concerns: List[str] = Field(default_factory=list, description="Primary clinical or additive concerns")
    cleaner_alternative: Optional[HealthierAlternative] = Field(default=None, description="Cleaner alternative available at same pincode on same app")

class CartAuditResponse(BaseModel):
    store_name: str = Field(default="Quick-Commerce", description="Detected quick-commerce platform e.g. Zepto, Blinkit")
    pincode: str = Field(description="Delivery pincode audited against")
    original_cart_score: int = Field(description="Current average health score of all items in cart")
    swapped_cart_score: int = Field(description="Potential average health score if clean swaps are accepted")
    score_improvement: int = Field(description="Score difference between swapped and original cart")
    total_items: int = Field(description="Total products audited in cart")
    clean_items_count: int = Field(description="Number of already-clean products in cart")
    red_flags_prevented_count: int = Field(description="Number of toxic additives or harmful factors eliminated")
    summary: str = Field(description="Clinical summary of cart nutritional quality")
    items: List[CartItemAudit] = Field(default_factory=list, description="Audited cart items with clean swaps")
