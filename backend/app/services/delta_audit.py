"""
Relative Delta Auditing & Category Sanity Swap Engine.
Enforces:
1. S_alternative >= 70 AND S_alternative >= S_scanned + 15 (Clean Commercial Upgrade)
2. BRAND-SWAP BAN: Reject swapping one ultra-processed brand for another similar item
3. Tier 2: Best Commercial Available + Warning Tag if no product reaches 70
4. Tier 3: Whole-Food Recipe Swap + verified YouTube search link
"""

import urllib.parse
from typing import List, Dict, Any, Optional
from app.schemas.analysis import HealthierAlternative

def apply_delta_audit_hierarchy(
    scanned_product_name: str,
    scanned_health_score: int,
    candidate_alternatives: List[Dict[str, Any]],
    category_hint: str = ""
) -> List[HealthierAlternative]:
    """
    Applies the 3-tier hierarchy:
    - Best in market: If scanned_health_score >= 85, declare product best available in market
    - Tier 1: Clean Commercial Upgrade (Score >= 70 AND Score >= Scanned + 15)
    - Tier 2: Best Commercial Option with nutrition warning tag if no commercial hits 70
    - Tier 3: Whole-Food Recipe Swap with YouTube search link
    """
    # If the scanned product is already exceptionally clean (Score >= 85), do not force commercial alternatives
    if scanned_health_score >= 85:
        return [
            HealthierAlternative(
                name=f"{scanned_product_name} (Top Tier Choice)",
                product_name=scanned_product_name,
                health_score=scanned_health_score,
                type="CLEAN_COMMERCIAL",
                delta_vs_scanned="Current Product",
                warning_tag="",
                is_direct_pdp=False,
                pincode_available=True,
                reason="🏆 This product already demonstrates peak nutritional integrity with clean ingredients and no harmful additives. It is among the best available products in the market.",
                key_benefit="No cleaner commercial alternative is necessary.",
                price_comparison="Current Product",
                personalized_fit="Optimal whole-food alignment."
            )
        ]

    scanned_lower = scanned_product_name.lower()
    clean_tier1 = []
    best_commercial = None
    highest_commercial_score = -1

    for cand in candidate_alternatives:
        name = cand.get("name") or cand.get("product_name") or "Alternative"
        c_score = int(cand.get("health_score", 80))
        cand_lower = name.lower()

        # BRAND-SWAP BAN: Check if this is just another similar processed brand
        is_same_brand_processed = False
        forbidden_brand_swaps = [
            ("d'lecta", "amul"),
            ("britannia", "parle"),
            ("lays", "bingo"),
            ("bournvita", "horlicks")
        ]
        for b1, b2 in forbidden_brand_swaps:
            if (b1 in scanned_lower and b2 in cand_lower) or (b2 in scanned_lower and b1 in cand_lower):
                # If neither achieves >= 70, reject brand swapping
                if c_score < 70:
                    is_same_brand_processed = True

        if is_same_brand_processed:
            continue

        # Check Tier 1 condition
        delta = c_score - scanned_health_score
        if c_score >= 70 and delta >= 15:
            clean_tier1.append(HealthierAlternative(
                name=name,
                product_name=name,
                health_score=c_score,
                type="CLEAN_COMMERCIAL",
                delta_vs_scanned=f"+{delta} pts",
                direct_pdp_url=cand.get("direct_pdp_url"),
                is_direct_pdp=bool(cand.get("is_direct_pdp", False)),
                store_url=cand.get("direct_pdp_url"),
                pincode_available=cand.get("pincode_available", True),
                reason=cand.get("reason", "Verified clean whole-food upgrade."),
                key_benefit=cand.get("key_benefit") or cand.get("reason", "Clean whole food alternative"),
                price_comparison=cand.get("price_comparison", "Comparable"),
                personalized_fit=cand.get("personalized_fit", "Meets strict nutrient threshold standards.")
            ))

        # Track best commercial option
        if c_score > highest_commercial_score:
            highest_commercial_score = c_score
            best_commercial = cand

    # Tier 2: If no commercial option achieved >= 70, return best available with explicit warning
    tier2_alts = []
    if not clean_tier1 and best_commercial:
        delta = highest_commercial_score - scanned_health_score
        tier2_alts.append(HealthierAlternative(
            name=best_commercial.get("name") or best_commercial.get("product_name"),
            product_name=best_commercial.get("product_name") or best_commercial.get("name"),
            health_score=highest_commercial_score,
            type="BEST_COMMERCIAL_AVAILABLE",
            delta_vs_scanned=f"+{delta} pts" if delta > 0 else f"{delta} pts",
            warning_tag=f"⚠️ Best packaged option in this store category, but scored {highest_commercial_score}/100 and may still contain high sodium or saturated fat.",
            direct_pdp_url=best_commercial.get("direct_pdp_url"),
            is_direct_pdp=bool(best_commercial.get("is_direct_pdp", False)),
            store_url=best_commercial.get("direct_pdp_url"),
            pincode_available=best_commercial.get("pincode_available", True),
            reason=best_commercial.get("reason", "Highest scoring packaged alternative in category."),
            key_benefit=best_commercial.get("key_benefit", "Better than scanned product"),
            price_comparison="Comparable",
            personalized_fit="Use in moderation."
        ))

    # Tier 3: Whole-Food Recipe Swap + verified YouTube search link
    query_topic = category_hint or scanned_product_name
    encoded_query = urllib.parse.quote_plus(f"how to make fresh {query_topic} at home healthy unprocessed")
    youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    recipe_title = f"Homemade Unprocessed Fresh {query_topic.title()} Recipe"
    tier3_recipe = HealthierAlternative(
        name=recipe_title,
        product_name=recipe_title,
        health_score=92,
        type="HOMEMADE_RECIPE",
        delta_vs_scanned=f"+{92 - scanned_health_score} pts",
        recipe_url=youtube_url,
        is_direct_pdp=False,
        pincode_available=True,
        reason="100% natural whole ingredients, zero emulsifiers (INS 331/452), zero synthetic preservatives.",
        key_benefit="Zero industrial additives, complete ingredient transparency.",
        price_comparison="Inexpensive",
        personalized_fit="Eliminates all industrial seed oils and synthetic additives."
    )

    final_list = clean_tier1 if clean_tier1 else tier2_alts
    # Always include Tier 3 recipe swap for comprehensive consumer empowerment
    final_list.append(tier3_recipe)
    return final_list
