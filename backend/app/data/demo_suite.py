"""
Demo Mode Dataset representing 5 deterministic product tiers across the health spectrum.
Instant (<100ms) execution without consuming external API credits.
"""

DEMO_TIER_PRODUCTS = {
    # 1. Very Low Score: 18/100
    "very_low": {
        "product_name": "Crunchy Masala Potato Chips",
        "health_score": 18,
        "personalized_verdict": "AVOID (VIOLATES PROFILE)",
        "simple_summary": "Ultra-processed deep-fried snack with 38% refined palm oil, intense sodium (750mg), and synthetic MSG (INS 621).",
        "deceptive_claims_flagged": [
            "Made with Real Potatoes (Masks 38% Palm Olein)",
            "0% Cholesterol (Disguises 16g Saturated Fat)"
        ],
        "fssai_violations": [
            "Regulation 5(2)(b): Palm oil is 2nd heaviest ingredient, dominating nutritional profile.",
            "Excessive High Sodium threshold under FSSAI HFSS warning guidelines."
        ],
        "ingredient_breakdown": [
            {"ingredient": "Potatoes (52%)", "purpose": "Primary vegetable", "concern_level": "LOW", "personalized_warning": ""},
            {"ingredient": "Palmolein Oil (38%)", "purpose": "Frying fat", "concern_level": "HIGH", "personalized_warning": "High saturated palmitic acid, worsens cardiovascular risks."},
            {"ingredient": "Iodized Salt (Sodium 750mg)", "purpose": "Seasoning", "concern_level": "HIGH", "personalized_warning": "Exceeds safe limits for hypertension and kidney function."},
            {"ingredient": "INS 621 (MSG)", "purpose": "Flavour Enhancer", "concern_level": "MEDIUM", "personalized_warning": "Synthetic umami booster driving overconsumption."},
            {"ingredient": "Maltodextrin", "purpose": "Flavor carrier", "concern_level": "HIGH", "personalized_warning": "GI 105-110, causes rapid glucose surges."}
        ],
        "nutrition_card": {
            "serving_size": "100g",
            "calories_kcal": 545.0,
            "total_fat_g": 36.0,
            "saturated_fat_g": 16.5,
            "trans_fat_g": 0.4,
            "total_carbs_g": 52.0,
            "added_sugars_g": 4.0,
            "sodium_mg": 750.0,
            "breakdown": [
                {"nutrient": "Calories", "amount_per_100g": "545 kcal", "clinical_evaluation": "High energy density"},
                {"nutrient": "Saturated Fat", "amount_per_100g": "16.5g", "clinical_evaluation": "Exceeds daily healthy allowance"},
                {"nutrient": "Sodium", "amount_per_100g": "750mg", "clinical_evaluation": "Severe hypertensive risk"}
            ]
        },
        "nutrient_integrity": {
            "fiber_type": "Negligible",
            "palm_oil_present": True,
            "hidden_sugars_flagged": ["Maltodextrin"],
            "sodium_and_preservatives_risk": "High"
        },
        "healthier_alternative": {
            "name": "Slow-Roasted Salt & Pepper Makhana (Foxnuts)",
            "product_name": "Slow-Roasted Salt & Pepper Makhana",
            "health_score": 88,
            "key_benefit": "Zero palm oil, roasted in olive oil, 8g natural fiber",
            "price_comparison": "Comparable",
            "personalized_fit": "Low glycemic load, heart safe",
            "type": "CLEAN_COMMERCIAL",
            "delta_vs_scanned": "+70 pts",
            "direct_pdp_url": "https://www.zepto.com/pn/farmley-roasted-makhana/pvid/11223344",
            "is_direct_pdp": True,
            "pincode_available": True,
            "reason": "100% whole food, zero palm oil, zero chemical additives."
        },
        "clean_alternatives": [
            {
                "name": "Slow-Roasted Salt & Pepper Makhana (Foxnuts)",
                "product_name": "Slow-Roasted Salt & Pepper Makhana",
                "health_score": 88,
                "key_benefit": "Zero palm oil, roasted in olive oil",
                "price_comparison": "Comparable",
                "personalized_fit": "Heart safe and diabetic friendly",
                "type": "CLEAN_COMMERCIAL",
                "delta_vs_scanned": "+70 pts",
                "direct_pdp_url": "https://www.zepto.com/pn/farmley-roasted-makhana/pvid/11223344",
                "is_direct_pdp": True,
                "pincode_available": True,
                "reason": "100% whole food, zero palm oil."
            },
            {
                "name": "Homemade Air-Fried Sweet Potato Chips",
                "product_name": "Air-Fried Sweet Potato Chips",
                "health_score": 94,
                "key_benefit": "Zero industrial seed oils, high beta-carotene",
                "price_comparison": "Inexpensive",
                "personalized_fit": "Zero additives, whole food fiber",
                "type": "HOMEMADE_RECIPE",
                "delta_vs_scanned": "+76 pts",
                "recipe_url": "https://www.youtube.com/results?search_query=how+to+make+crispy+air+fryer+sweet+potato+chips+healthy",
                "is_direct_pdp": False,
                "pincode_available": True,
                "reason": "100% whole food, zero emulsifiers, zero preservatives."
            }
        ],
        "is_food_label": True,
        "label_type": "FULL_PANEL"
    },

    # 2. Low Score: 38/100
    "low": {
        "product_name": "Commercial Whole Wheat 'Brown Bread'",
        "health_score": 38,
        "personalized_verdict": "CAUTION",
        "simple_summary": "Dyed refined flour masquerading as healthy whole wheat. Uses Maida as primary grain and INS 150d Caramel Colour IV for dark appearance.",
        "deceptive_claims_flagged": [
            "100% Whole Wheat Claim on front (Ingredients state Refined Wheat Flour 60%)",
            "Zero Trans Fat (Hides 8g added sugar)"
        ],
        "fssai_violations": [
            "FSSAI 2023 Bread Amendment: Product fails the 75% whole wheat threshold for Atta Bread.",
            "Regulation 5(2)(b): Maida listed ahead of Whole Wheat."
        ],
        "ingredient_breakdown": [
            {"ingredient": "Refined Wheat Flour / Maida (58%)", "purpose": "Primary flour", "concern_level": "HIGH", "personalized_warning": "High glycemic index, lacks bran fiber."},
            {"ingredient": "Whole Wheat Flour / Atta (24%)", "purpose": "Secondary grain", "concern_level": "LOW", "personalized_warning": ""},
            {"ingredient": "Sugar (8g)", "purpose": "Sweetener", "concern_level": "MEDIUM", "personalized_warning": "Contributes to insulin resistance."},
            {"ingredient": "INS 150d (Caramel Colour IV)", "purpose": "Colorant", "concern_level": "HIGH", "personalized_warning": "Manufactured with ammonia/sulfites; trace 4-MEI carcinogen concern."},
            {"ingredient": "Palm Oil", "purpose": "Shortening", "concern_level": "HIGH", "personalized_warning": "High saturated fat."}
        ],
        "nutrition_card": {
            "serving_size": "100g",
            "calories_kcal": 265.0,
            "total_fat_g": 3.8,
            "saturated_fat_g": 2.1,
            "trans_fat_g": 0.0,
            "total_carbs_g": 51.0,
            "added_sugars_g": 8.0,
            "sodium_mg": 380.0,
            "breakdown": [
                {"nutrient": "Added Sugar", "amount_per_100g": "8.0g", "clinical_evaluation": "Elevated added sugar in daily staple"},
                {"nutrient": "Dietary Fiber", "amount_per_100g": "2.2g", "clinical_evaluation": "Low whole grain fiber content"}
            ]
        },
        "nutrient_integrity": {
            "fiber_type": "Dyed Refined Starch",
            "palm_oil_present": True,
            "hidden_sugars_flagged": ["Liquid Glucose"],
            "sodium_and_preservatives_risk": "Moderate"
        },
        "healthier_alternative": {
            "name": "The Health Factory 100% Whole Wheat Zero Maida Bread",
            "product_name": "The Health Factory 100% Whole Wheat Bread",
            "health_score": 86,
            "key_benefit": "0% Maida, 0% Chemical Preservatives, no Caramel Colour",
            "price_comparison": "~1.2x",
            "personalized_fit": "Genuine 100% whole grain fiber",
            "type": "CLEAN_COMMERCIAL",
            "delta_vs_scanned": "+48 pts",
            "direct_pdp_url": "https://www.zepto.com/pn/the-health-factory-zero-maida-bread/pvid/22334455",
            "is_direct_pdp": True,
            "pincode_available": True,
            "reason": "Certified 100% whole wheat, zero INS 150d dye."
        },
        "clean_alternatives": [
            {
                "name": "The Health Factory 100% Whole Wheat Zero Maida Bread",
                "product_name": "The Health Factory Zero Maida Bread",
                "health_score": 86,
                "key_benefit": "Zero Maida, zero artificial colour",
                "price_comparison": "~1.2x",
                "personalized_fit": "Genuine whole grain",
                "type": "CLEAN_COMMERCIAL",
                "delta_vs_scanned": "+48 pts",
                "direct_pdp_url": "https://www.zepto.com/pn/the-health-factory-zero-maida-bread/pvid/22334455",
                "is_direct_pdp": True,
                "pincode_available": True,
                "reason": "100% whole grain, zero artificial dyes."
            }
        ],
        "is_food_label": True,
        "label_type": "FULL_PANEL"
    },

    # 3. Moderate Score: 74/100 (D'lecta Mozzarella Cheese Block)
    "moderate": {
        "product_name": "D'lecta Mozzarella Cheese Block",
        "health_score": 74,
        "personalized_verdict": "SAFE FOR YOU",
        "simple_summary": "Authentic cow milk mozzarella with 24g bioavailable protein (PDCAAS 1.0) and zero chemical emulsifiers or artificial preservatives. Contains natural dairy fat (20.5g) and moderate sodium (640mg).",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "ingredient_breakdown": [
            {"ingredient": "Pasteurised Cow Milk & Skimmed Milk", "purpose": "Dairy base", "concern_level": "LOW", "personalized_warning": "Whole-food protein & calcium source."},
            {"ingredient": "Iodised Salt (Sodium 640mg)", "purpose": "Seasoning & preservation", "concern_level": "LOW", "personalized_warning": "Moderate sodium; monitor intake if managing hypertension."},
            {"ingredient": "Firming Agent (INS 509 - Calcium Chloride)", "purpose": "Natural mineral firming agent", "concern_level": "LOW", "personalized_warning": "Safe mineral firming salt."},
            {"ingredient": "Microbial Cultures & Vegetarian Rennet", "purpose": "Fermentation & coagulation", "concern_level": "LOW", "personalized_warning": "Safe vegetarian cultures."}
        ],
        "nutrition_card": {
            "serving_size": "100g",
            "calories_kcal": 284.0,
            "total_fat_g": 20.5,
            "saturated_fat_g": 12.9,
            "trans_fat_g": 0.7,
            "total_carbs_g": 0.5,
            "added_sugars_g": 0.0,
            "sodium_mg": 640.0,
            "breakdown": [
                {"nutrient": "Protein", "amount_per_100g": "24.0g", "clinical_evaluation": "High bioavailable dairy protein (PDCAAS 1.0)"},
                {"nutrient": "Added Sugar", "amount_per_100g": "0.0g", "clinical_evaluation": "Zero added sugar"},
                {"nutrient": "Saturated Fat", "amount_per_100g": "12.9g", "clinical_evaluation": "Intrinsic dairy fat; moderate density"},
                {"nutrient": "Sodium", "amount_per_100g": "640mg", "clinical_evaluation": "Moderate sodium; monitor if on low-salt diet"}
            ]
        },
        "nutrient_integrity": {
            "fiber_type": "None",
            "palm_oil_present": False,
            "hidden_sugars_flagged": [],
            "sodium_and_preservatives_risk": "Low"
        },
        "healthier_alternative": {
            "name": "Akshayakalpa Organic Artisan Mozzarella / Paneer",
            "product_name": "Akshayakalpa Organic Artisan Mozzarella",
            "health_score": 93,
            "key_benefit": "100% certified organic A2 whole milk, low sodium 120mg, zero preservatives",
            "price_comparison": "~1.2x",
            "personalized_fit": "Unprocessed organic A2 dairy",
            "type": "CLEAN_COMMERCIAL",
            "delta_vs_scanned": "+19 pts",
            "direct_pdp_url": "https://www.zepto.com/pn/akshayakalpa-artisan-organic-cheese/pvid/akshaya-ch-1",
            "is_direct_pdp": True,
            "pincode_available": True,
            "reason": "Pure curdled organic A2 whole milk with low sodium density."
        },
        "clean_alternatives": [
            {
                "name": "Akshayakalpa Organic Artisan Mozzarella / Paneer",
                "product_name": "Akshayakalpa Organic Artisan Mozzarella",
                "health_score": 93,
                "key_benefit": "100% certified organic A2 whole milk, low sodium 120mg, zero preservatives",
                "price_comparison": "~1.2x",
                "personalized_fit": "Unprocessed organic A2 dairy",
                "type": "CLEAN_COMMERCIAL",
                "delta_vs_scanned": "+19 pts",
                "direct_pdp_url": "https://www.zepto.com/pn/akshayakalpa-artisan-organic-cheese/pvid/akshaya-ch-1",
                "is_direct_pdp": True,
                "pincode_available": True,
                "reason": "Pure curdled organic A2 whole milk with low sodium density."
            },
            {
                "name": "Homemade Fresh Stretched Mozzarella / Hung Curd",
                "product_name": "Homemade Fresh Stretched Mozzarella",
                "health_score": 92,
                "key_benefit": "100% fresh whole milk, zero emulsifiers, zero added sodium",
                "price_comparison": "Inexpensive",
                "personalized_fit": "Pure fresh homemade dairy without commercial salts",
                "type": "HOMEMADE_RECIPE",
                "delta_vs_scanned": "+18 pts",
                "recipe_url": "https://www.youtube.com/results?search_query=how+to+make+fresh+mozzarella+at+home+healthy",
                "is_direct_pdp": False,
                "pincode_available": True,
                "reason": "100% natural, zero emulsifiers, zero preservatives."
            }
        ],
        "is_food_label": True,
        "label_type": "FULL_PANEL"
    },

    # 4. High Score: 78/100
    "high": {
        "product_name": "Epigamia Natural Unsweetened Greek Yogurt",
        "health_score": 78,
        "personalized_verdict": "SAFE FOR YOU",
        "simple_summary": "High protein natural dairy with zero added sugars, live active probiotic cultures, and natural trace dairy trans fat (0.1g, score 0 deduction).",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "ingredient_breakdown": [
            {"ingredient": "Pasteurized Double Toned Milk", "purpose": "Dairy base", "concern_level": "LOW", "personalized_warning": ""},
            {"ingredient": "Live Active Probiotic Cultures (S. thermophilus, L. bulgaricus)", "purpose": "Fermentation", "concern_level": "LOW", "personalized_warning": "Supports gut microbiome."}
        ],
        "nutrition_card": {
            "serving_size": "100g",
            "calories_kcal": 75.0,
            "total_fat_g": 3.0,
            "saturated_fat_g": 1.9,
            "trans_fat_g": 0.1,
            "total_carbs_g": 4.0,
            "added_sugars_g": 0.0,
            "sodium_mg": 45.0,
            "breakdown": [
                {"nutrient": "Protein", "amount_per_100g": "8.0g", "clinical_evaluation": "High bioavailable dairy protein (PDCAAS 1.0)"},
                {"nutrient": "Added Sugar", "amount_per_100g": "0.0g", "clinical_evaluation": "Zero added sugar"}
            ]
        },
        "nutrient_integrity": {
            "fiber_type": "None",
            "palm_oil_present": False,
            "hidden_sugars_flagged": [],
            "sodium_and_preservatives_risk": "Low"
        },
        "healthier_alternative": {
            "name": "Two Brothers Organic Farms A2 Cultured Dahi",
            "product_name": "Two Brothers A2 Cultured Dahi",
            "health_score": 93,
            "key_benefit": "Indigenous A2 cow whole milk, traditional clay-pot cultured",
            "price_comparison": "~1.4x",
            "personalized_fit": "Peak probiotic diversity and optimal gut absorption",
            "type": "CLEAN_COMMERCIAL",
            "delta_vs_scanned": "+15 pts",
            "direct_pdp_url": "https://www.zepto.com/pn/two-brothers-a2-dahi/pvid/44556677",
            "is_direct_pdp": True,
            "pincode_available": True,
            "reason": "100% organic pasture-raised A2 dairy."
        },
        "clean_alternatives": [
            {
                "name": "Two Brothers Organic Farms A2 Cultured Dahi",
                "product_name": "Two Brothers A2 Cultured Dahi",
                "health_score": 93,
                "key_benefit": "Traditional cultured A2 curd",
                "price_comparison": "~1.4x",
                "personalized_fit": "Gut microbiome support",
                "type": "CLEAN_COMMERCIAL",
                "delta_vs_scanned": "+15 pts",
                "direct_pdp_url": "https://www.zepto.com/pn/two-brothers-a2-dahi/pvid/44556677",
                "is_direct_pdp": True,
                "pincode_available": True,
                "reason": "Zero added sugar, zero thickeners."
            }
        ],
        "is_food_label": True,
        "label_type": "FULL_PANEL"
    },

    # 5. Very High Score: 95/100
    "very_high": {
        "product_name": "Organic Whole Unrefined Rolled Oats",
        "health_score": 95,
        "personalized_verdict": "SAFE FOR YOU",
        "simple_summary": "100% certified organic unrefined whole grain oats with 11g soluble beta-glucan fiber, zero added sugars, and zero additives.",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "ingredient_breakdown": [
            {"ingredient": "100% Organic Rolled Oats", "purpose": "Whole Grain", "concern_level": "LOW", "personalized_warning": "Low glycemic, lowers LDL cholesterol."}
        ],
        "nutrition_card": {
            "serving_size": "100g",
            "calories_kcal": 375.0,
            "total_fat_g": 6.5,
            "saturated_fat_g": 1.1,
            "trans_fat_g": 0.0,
            "total_carbs_g": 62.0,
            "added_sugars_g": 0.0,
            "sodium_mg": 5.0,
            "breakdown": [
                {"nutrient": "Dietary Fiber", "amount_per_100g": "11.0g", "clinical_evaluation": "Rich in beta-glucan heart-protective fiber"},
                {"nutrient": "Protein", "amount_per_100g": "13.5g", "clinical_evaluation": "High plant protein"}
            ]
        },
        "nutrient_integrity": {
            "fiber_type": "Natural Whole Grain Beta-Glucan",
            "palm_oil_present": False,
            "hidden_sugars_flagged": [],
            "sodium_and_preservatives_risk": "Low"
        },
        "healthier_alternative": {
            "name": "Natureland Organics Whole Steel Cut Oats",
            "product_name": "Natureland Organics Steel Cut Oats",
            "health_score": 98,
            "key_benefit": "Minimal processing, lowest glycemic index in grain category",
            "price_comparison": "Comparable",
            "personalized_fit": "Optimal for blood glucose stabilization",
            "type": "CLEAN_COMMERCIAL",
            "delta_vs_scanned": "+3 pts",
            "direct_pdp_url": "https://www.zepto.com/pn/natureland-steel-cut-oats/pvid/55667788",
            "is_direct_pdp": True,
            "pincode_available": True,
            "reason": "100% organic whole grain."
        },
        "clean_alternatives": [
            {
                "name": "Natureland Organics Whole Steel Cut Oats",
                "product_name": "Natureland Organics Steel Cut Oats",
                "health_score": 98,
                "key_benefit": "Lowest glycemic index",
                "price_comparison": "Comparable",
                "personalized_fit": "Peak whole food integrity",
                "type": "CLEAN_COMMERCIAL",
                "delta_vs_scanned": "+3 pts",
                "direct_pdp_url": "https://www.zepto.com/pn/natureland-steel-cut-oats/pvid/55667788",
                "is_direct_pdp": True,
                "pincode_available": True,
                "reason": "Unrefined whole grain."
            }
        ],
        "is_food_label": True,
        "label_type": "FULL_PANEL"
    }
}
