from app.data.demo_suite import DEMO_TIER_PRODUCTS

# Professional, highly detailed preset products representing actual commercial items across the 5 health tiers
PRESET_PRODUCTS = [
    {
        "id": "chips-18",
        "title": "Lay's India's Magic Masala Chips",
        "subtitle": "Score 18/100 · Tier: Very Low",
        "description": "Ultra-processed fried potato snack formulated with 38% refined industrial palmolein oil, excessive sodium (750mg), and synthetic MSG (INS 621).",
        "sample_result": DEMO_TIER_PRODUCTS["very_low"]
    },
    {
        "id": "bread-38",
        "title": "English Oven Brown Bread",
        "subtitle": "Score 38/100 · Tier: Low",
        "description": "Marketed as wholesome brown bread, but formulated with 58% refined maida and dyed dark with INS 150d Caramel Colour IV to simulate bran.",
        "sample_result": DEMO_TIER_PRODUCTS["low"]
    },
    {
        "id": "cheese-58",
        "title": "D'lecta Mozzarella Processed Cheese",
        "subtitle": "Score 58/100 · Tier: Moderate",
        "description": "Commercial processed cheese block carrying 18g saturated fat per 100g and synthetic phosphate emulsifying salts (INS 331, INS 452).",
        "sample_result": DEMO_TIER_PRODUCTS["moderate"]
    },
    {
        "id": "yogurt-78",
        "title": "Epigamia Natural Greek Yogurt",
        "subtitle": "Score 78/100 · Tier: High",
        "description": "High-protein unsweetened dairy with 8g bioavailable protein (PDCAAS 1.0), live active probiotic cultures, and zero added cane sugar.",
        "sample_result": DEMO_TIER_PRODUCTS["high"]
    },
    {
        "id": "oats-95",
        "title": "Organic Whole Rolled Oats",
        "subtitle": "Score 95/100 · Tier: Very High",
        "description": "100% certified whole grain unrefined rolled oats with 11g soluble beta-glucan fiber, zero added sugar, zero sodium, and zero preservatives.",
        "sample_result": DEMO_TIER_PRODUCTS["very_high"]
    }
]
