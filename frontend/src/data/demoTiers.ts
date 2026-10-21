import { LabelAnalysisResult } from "@/types";

export const LOCAL_DEMO_TIER_PRODUCTS: Record<string, LabelAnalysisResult> = {
  very_low: {
    product_name: "Crunchy Masala Potato Chips",
    health_score: 18,
    personalized_verdict: "AVOID (VIOLATES PROFILE)",
    simple_summary: "Ultra-processed deep-fried snack with 38% refined palm oil, intense sodium (750mg), and synthetic MSG (INS 621).",
    deceptive_claims_flagged: [
      "Made with Real Potatoes (Masks 38% Palm Olein)",
      "0% Cholesterol (Disguises 16.5g Saturated Palmitic Fat)"
    ],
    fssai_violations: [
      "Regulation 5(2)(b): Palm oil is 2nd heaviest ingredient, dominating nutritional profile.",
      "Exceeds FSSAI HFSS High Sodium & Saturated Fat threshold without mandatory warning label."
    ],
    ingredient_breakdown: [
      { ingredient: "Potatoes (52%)", purpose: "Primary vegetable base", concern_level: "LOW", personalized_warning: "" },
      { ingredient: "Palmolein Oil (38%)", purpose: "Cheap industrial frying fat", concern_level: "HIGH", personalized_warning: "Rich in palmitic acid; elevates arterial stiffness and LDL-C." },
      { ingredient: "Iodized Salt (Sodium 750mg)", purpose: "Flavor & preservation", concern_level: "HIGH", personalized_warning: "Severe blood pressure and renal spike hazard." },
      { ingredient: "INS 621 (MSG)", purpose: "Flavour Enhancer", concern_level: "MEDIUM", personalized_warning: "Triggers compulsive overeating and potential excitotoxicity." },
      { ingredient: "Maltodextrin", purpose: "Flavor binder & disguised filler", concern_level: "HIGH", personalized_warning: "GI 105-110, spikes blood sugar faster than pure table sugar." }
    ],
    nutrition_card: {
      serving_size: "100g",
      calories_kcal: 545.0,
      total_fat_g: 36.0,
      saturated_fat_g: 16.5,
      trans_fat_g: 0.4,
      total_carbs_g: 52.0,
      added_sugars_g: 4.0,
      sodium_mg: 750.0,
      breakdown: [
        { nutrient: "Calories", amount_per_100g: "545 kcal", daily_value_percent: "27%", clinical_evaluation: "Hyper-palatable, extreme energy density." },
        { nutrient: "Total Fat", amount_per_100g: "36.0g", daily_value_percent: "54%", clinical_evaluation: "Over half of total calories derived from cheap palm fat." },
        { nutrient: "Saturated Fat", amount_per_100g: "16.5g", daily_value_percent: "75%", clinical_evaluation: "Dramatically exceeds WHO single-meal safe upper allowance." },
        { nutrient: "Sodium", amount_per_100g: "750mg", daily_value_percent: "38%", clinical_evaluation: "Exceeds daily threshold; triggers fluid retention." },
        { nutrient: "Dietary Fiber", amount_per_100g: "1.2g", daily_value_percent: "4%", clinical_evaluation: "Stripped of protective dietary fiber." }
      ]
    },
    nutrient_integrity: {
      protein: {
        declared_protein_g: 5.2,
        usable_protein_g: 2.1,
        pdcaas_score: 0.4,
        primary_sources: ["Potato Starch"],
        protein_to_calorie_percent: 3.8,
        amino_spiking_risk: false
      },
      fiber_type: "Stripped Refined Starch",
      palm_oil_present: true,
      hidden_sugars_flagged: ["Maltodextrin"],
      sodium_and_preservatives_risk: "High",
      claims_matrix: [
        { claim: "Made with Real Farm Potatoes", status: "MISLEADING", explanation: "Masks 38% refined industrial palm olein." },
        { claim: "0% Cholesterol", status: "DECEPTIVE", explanation: "All plant oils lack cholesterol; distracts from 16.5g saturated fat." }
      ]
    },
    healthier_alternative: {
      name: "Slow-Roasted Salt & Pepper Foxnuts (Makhana)",
      product_name: "Farmley Slow-Roasted Makhana",
      health_score: 88,
      key_benefit: "Zero palm oil, roasted in cold-pressed olive oil, 8g natural fiber",
      price_comparison: "Comparable (~₹120/100g)",
      personalized_fit: "Low glycemic load, heart safe, zero INS additives",
      type: "CLEAN_COMMERCIAL",
      delta_vs_scanned: "+70 pts",
      direct_pdp_url: "https://www.zepto.com/pn/farmley-roasted-makhana/pvid/11223344",
      is_direct_pdp: true,
      pincode_available: true,
      reason: "100% whole grain puffed lotus seeds with zero seed oil frying."
    },
    clean_alternatives: [
      {
        name: "Farmley Slow-Roasted Salt & Pepper Makhana",
        product_name: "Farmley Slow-Roasted Makhana",
        health_score: 88,
        key_benefit: "Zero palm oil, 8g plant protein, low glycemic",
        price_comparison: "Comparable",
        personalized_fit: "Heart safe and diabetic friendly",
        type: "CLEAN_COMMERCIAL",
        delta_vs_scanned: "+70 pts",
        direct_pdp_url: "https://www.zepto.com/pn/farmley-roasted-makhana/pvid/11223344",
        is_direct_pdp: true,
        pincode_available: true,
        reason: "100% puffed lotus seed with no industrial frying."
      },
      {
        name: "Homemade Crispy Air-Fried Sweet Potato Chips",
        product_name: "Air-Fried Sweet Potato Chips",
        health_score: 94,
        key_benefit: "Zero industrial frying oil, high beta-carotene",
        price_comparison: "Inexpensive (~₹30/serving)",
        personalized_fit: "Zero chemical emulsifiers, natural potassium & fiber",
        type: "HOMEMADE_RECIPE",
        delta_vs_scanned: "+76 pts",
        recipe_url: "https://www.youtube.com/results?search_query=how+to+make+crispy+air+fryer+sweet+potato+chips+healthy",
        is_direct_pdp: false,
        pincode_available: true,
        reason: "100% whole vegetable, zero additives, baked or air-fried."
      }
    ],
    is_food_label: true,
    label_type: "FULL_PANEL"
  },

  low: {
    product_name: "Commercial Whole Wheat 'Brown Bread'",
    health_score: 38,
    personalized_verdict: "CAUTION",
    simple_summary: "Dyed refined flour masquerading as healthy whole wheat. Uses Maida as primary grain and INS 150d Caramel Colour IV for dark appearance.",
    deceptive_claims_flagged: [
      "100% Whole Wheat Claim on front (Ingredients state Refined Wheat Flour 58%)",
      "Zero Trans Fat (Hides 8g added sugar and shortening)"
    ],
    fssai_violations: [
      "FSSAI 2023 Bread Amendment: Product fails the 75% whole wheat threshold for Atta Bread.",
      "Regulation 5(2)(b): Maida listed ahead of Whole Wheat."
    ],
    ingredient_breakdown: [
      { ingredient: "Refined Wheat Flour / Maida (58%)", purpose: "Primary bulk grain", concern_level: "HIGH", personalized_warning: "High glycemic index, stripped of bran fiber." },
      { ingredient: "Whole Wheat Flour / Atta (24%)", purpose: "Secondary grain", concern_level: "LOW", personalized_warning: "" },
      { ingredient: "Sugar (8g)", purpose: "Yeast activator & sweetener", concern_level: "MEDIUM", personalized_warning: "Contributes to insulin resistance." },
      { ingredient: "INS 150d (Caramel Colour IV)", purpose: "Brown dye", concern_level: "HIGH", personalized_warning: "Manufactured with ammonia/sulfites; trace 4-MEI carcinogen concern." },
      { ingredient: "Palm Oil", purpose: "Dough conditioner", concern_level: "HIGH", personalized_warning: "High saturated fat." }
    ],
    nutrition_card: {
      serving_size: "100g",
      calories_kcal: 265.0,
      total_fat_g: 3.8,
      saturated_fat_g: 2.1,
      trans_fat_g: 0.0,
      total_carbs_g: 51.0,
      added_sugars_g: 8.0,
      sodium_mg: 380.0,
      breakdown: [
        { nutrient: "Carbohydrates", amount_per_100g: "51.0g", daily_value_percent: "18%", clinical_evaluation: "Predominantly refined wheat starch." },
        { nutrient: "Added Sugar", amount_per_100g: "8.0g", daily_value_percent: "16%", clinical_evaluation: "Excessive sugar for daily breakfast staple." },
        { nutrient: "Dietary Fiber", amount_per_100g: "2.2g", daily_value_percent: "8%", clinical_evaluation: "Low bran fiber due to 58% maida formulation." }
      ]
    },
    nutrient_integrity: {
      protein: {
        declared_protein_g: 7.8,
        usable_protein_g: 2.7,
        pdcaas_score: 0.35,
        primary_sources: ["Wheat Gluten"],
        protein_to_calorie_percent: 11.7,
        amino_spiking_risk: false
      },
      fiber_type: "Dyed Refined Starch",
      palm_oil_present: true,
      hidden_sugars_flagged: ["Liquid Glucose"],
      sodium_and_preservatives_risk: "Moderate",
      claims_matrix: [
        { claim: "Whole Wheat Goodness", status: "DECEPTIVE", explanation: "Over half of flour content is white maida dyed brown." }
      ]
    },
    healthier_alternative: {
      name: "The Health Factory 100% Whole Wheat Zero Maida Bread",
      product_name: "The Health Factory Zero Maida Bread",
      health_score: 86,
      key_benefit: "0% Maida, 0% Chemical Preservatives, no INS 150d caramel dye",
      price_comparison: "~1.2x (₹60)",
      personalized_fit: "Genuine 100% whole grain fiber, low glycemic",
      type: "CLEAN_COMMERCIAL",
      delta_vs_scanned: "+48 pts",
      direct_pdp_url: "https://www.zepto.com/pn/the-health-factory-zero-maida-bread/pvid/22334455",
      is_direct_pdp: true,
      pincode_available: true,
      reason: "Certified 100% whole grain flour without artificial coloring."
    },
    clean_alternatives: [
      {
        name: "The Health Factory 100% Whole Wheat Zero Maida Bread",
        product_name: "The Health Factory Zero Maida Bread",
        health_score: 86,
        key_benefit: "Zero Maida, zero chemical dye",
        price_comparison: "~1.2x",
        personalized_fit: "Clean whole grain",
        type: "CLEAN_COMMERCIAL",
        delta_vs_scanned: "+48 pts",
        direct_pdp_url: "https://www.zepto.com/pn/the-health-factory-zero-maida-bread/pvid/22334455",
        is_direct_pdp: true,
        pincode_available: true,
        reason: "100% whole grain, zero artificial dyes."
      }
    ],
    is_food_label: true,
    label_type: "FULL_PANEL"
  },

  moderate: {
    product_name: "D'lecta Mozzarella Cheese Block",
    health_score: 58,
    personalized_verdict: "CAUTION",
    simple_summary: "Commercial processed cheese block with 18g saturated fat per 100g, sodium 650mg, and chemical emulsifiers (INS 331, INS 452).",
    deceptive_claims_flagged: [
      "Good Source of Calcium (Downplays 18g Saturated Fat and chemical phosphates)"
    ],
    fssai_violations: [
      "FSSAI Regulation 2.1.1: Uses emulsifying salts without bold front-of-pack sodium alert."
    ],
    ingredient_breakdown: [
      { ingredient: "Pasteurized Cow Milk", purpose: "Dairy base", concern_level: "LOW", personalized_warning: "" },
      { ingredient: "Common Salt (Sodium 650mg)", purpose: "Preservative/flavor", concern_level: "HIGH", personalized_warning: "Elevates blood pressure; fluid retention risk." },
      { ingredient: "Emulsifiers (INS 331, INS 452)", purpose: "Melting stabilizer", concern_level: "MEDIUM", personalized_warning: "Phosphate additives linked to arterial calcification." },
      { ingredient: "Microbial Rennet", purpose: "Coagulant", concern_level: "LOW", personalized_warning: "" }
    ],
    nutrition_card: {
      serving_size: "100g",
      calories_kcal: 310.0,
      total_fat_g: 24.0,
      saturated_fat_g: 18.0,
      trans_fat_g: 0.5,
      total_carbs_g: 2.5,
      added_sugars_g: 0.0,
      sodium_mg: 650.0,
      breakdown: [
        { nutrient: "Saturated Fat", amount_per_100g: "18.0g", daily_value_percent: "82%", clinical_evaluation: "Very high saturated fat; exceeds recommended allowance." },
        { nutrient: "Sodium", amount_per_100g: "650mg", daily_value_percent: "33%", clinical_evaluation: "Elevated sodium." },
        { nutrient: "Protein", amount_per_100g: "22.0g", daily_value_percent: "44%", clinical_evaluation: "High milk protein with high bioavailability." }
      ]
    },
    nutrient_integrity: {
      protein: {
        declared_protein_g: 22.0,
        usable_protein_g: 22.0,
        pdcaas_score: 1.0,
        primary_sources: ["Pasteurized Cow Milk"],
        protein_to_calorie_percent: 28.3,
        amino_spiking_risk: false
      },
      fiber_type: "None",
      palm_oil_present: false,
      hidden_sugars_flagged: [],
      sodium_and_preservatives_risk: "Moderate",
      claims_matrix: [
        { claim: "High Protein Dairy", status: "VERIFIED", explanation: "Protein is authentic, but accompanied by 18g saturated fat." }
      ]
    },
    healthier_alternative: {
      name: "Organic A2 Gir Cow Artisanal Paneer",
      product_name: "Organic A2 Gir Cow Paneer",
      health_score: 88,
      key_benefit: "Zero emulsifying salts (INS 331/452), zero synthetic preservatives, 18g bioavailable protein",
      price_comparison: "~1.3x (₹140/200g)",
      personalized_fit: "Unprocessed whole dairy with easy-to-digest A2 beta-casein",
      type: "CLEAN_COMMERCIAL",
      delta_vs_scanned: "+30 pts",
      direct_pdp_url: "https://www.zepto.com/pn/organic-a2-paneer/pvid/33445566",
      is_direct_pdp: true,
      pincode_available: true,
      reason: "Pure curdled A2 whole milk without chemical stabilizers."
    },
    clean_alternatives: [
      {
        name: "Organic A2 Gir Cow Artisanal Paneer",
        product_name: "Organic A2 Gir Cow Paneer",
        health_score: 88,
        key_benefit: "Zero chemical emulsifiers, zero preservatives",
        price_comparison: "~1.3x",
        personalized_fit: "Clean unprocessed dairy",
        type: "CLEAN_COMMERCIAL",
        delta_vs_scanned: "+30 pts",
        direct_pdp_url: "https://www.zepto.com/pn/organic-a2-paneer/pvid/33445566",
        is_direct_pdp: true,
        pincode_available: true,
        reason: "100% natural A2 dairy, zero chemical salts."
      },
      {
        name: "Homemade Fresh Stretched Mozzarella / Hung Curd",
        product_name: "Homemade Fresh Stretched Mozzarella",
        health_score: 92,
        key_benefit: "100% fresh whole milk, zero emulsifiers, zero added sodium",
        price_comparison: "Inexpensive (~₹50)",
        personalized_fit: "Eliminates all industrial phosphates",
        type: "HOMEMADE_RECIPE",
        delta_vs_scanned: "+34 pts",
        recipe_url: "https://www.youtube.com/results?search_query=how+to+make+fresh+mozzarella+at+home+healthy",
        is_direct_pdp: false,
        pincode_available: true,
        reason: "100% natural, zero emulsifiers (INS 331/452), zero synthetic preservatives."
      }
    ],
    is_food_label: true,
    label_type: "FULL_PANEL"
  },

  high: {
    product_name: "Epigamia Natural Unsweetened Greek Yogurt",
    health_score: 78,
    personalized_verdict: "SAFE FOR YOU",
    simple_summary: "High protein natural dairy with zero added sugars, live active probiotic cultures, and natural trace dairy trans fat (0.1g, score 0 deduction).",
    deceptive_claims_flagged: [],
    fssai_violations: [],
    ingredient_breakdown: [
      { ingredient: "Pasteurized Double Toned Milk", purpose: "Dairy base", concern_level: "LOW", personalized_warning: "" },
      { ingredient: "Live Active Probiotic Cultures (S. thermophilus, L. bulgaricus)", purpose: "Fermentation", concern_level: "LOW", personalized_warning: "Supports gut microbiome." }
    ],
    nutrition_card: {
      serving_size: "100g",
      calories_kcal: 75.0,
      total_fat_g: 3.0,
      saturated_fat_g: 1.9,
      trans_fat_g: 0.1,
      total_carbs_g: 4.0,
      added_sugars_g: 0.0,
      sodium_mg: 45.0,
      breakdown: [
        { nutrient: "Protein", amount_per_100g: "8.0g", daily_value_percent: "16%", clinical_evaluation: "High bioavailable dairy protein (PDCAAS 1.0)." },
        { nutrient: "Added Sugar", amount_per_100g: "0.0g", daily_value_percent: "0%", clinical_evaluation: "Zero added sugar." },
        { nutrient: "Sodium", amount_per_100g: "45.0mg", daily_value_percent: "2%", clinical_evaluation: "Naturally low sodium." }
      ]
    },
    nutrient_integrity: {
      protein: {
        declared_protein_g: 8.0,
        usable_protein_g: 8.0,
        pdcaas_score: 1.0,
        primary_sources: ["Pasteurized Double Toned Milk"],
        protein_to_calorie_percent: 42.6,
        amino_spiking_risk: false
      },
      fiber_type: "None",
      palm_oil_present: false,
      hidden_sugars_flagged: [],
      sodium_and_preservatives_risk: "Low",
      claims_matrix: [
        { claim: "No Added Sugar", status: "VERIFIED", explanation: "Contains only natural milk lactose." }
      ]
    },
    healthier_alternative: {
      name: "Two Brothers Organic Farms A2 Cultured Dahi",
      product_name: "Two Brothers A2 Cultured Dahi",
      health_score: 93,
      key_benefit: "Indigenous A2 cow whole milk, traditional clay-pot cultured",
      price_comparison: "~1.4x",
      personalized_fit: "Peak probiotic diversity and optimal gut absorption",
      type: "CLEAN_COMMERCIAL",
      delta_vs_scanned: "+15 pts",
      direct_pdp_url: "https://www.zepto.com/pn/two-brothers-a2-dahi/pvid/44556677",
      is_direct_pdp: true,
      pincode_available: true,
      reason: "100% organic pasture-raised A2 dairy."
    },
    clean_alternatives: [
      {
        name: "Two Brothers Organic Farms A2 Cultured Dahi",
        product_name: "Two Brothers A2 Cultured Dahi",
        health_score: 93,
        key_benefit: "Traditional cultured A2 curd",
        price_comparison: "~1.4x",
        personalized_fit: "Gut microbiome support",
        type: "CLEAN_COMMERCIAL",
        delta_vs_scanned: "+15 pts",
        direct_pdp_url: "https://www.zepto.com/pn/two-brothers-a2-dahi/pvid/44556677",
        is_direct_pdp: true,
        pincode_available: true,
        reason: "Zero added sugar, zero thickeners."
      }
    ],
    is_food_label: true,
    label_type: "FULL_PANEL"
  },

  very_high: {
    product_name: "Organic Whole Unrefined Rolled Oats",
    health_score: 95,
    personalized_verdict: "SAFE FOR YOU",
    simple_summary: "100% certified organic unrefined whole grain oats with 11g soluble beta-glucan fiber, zero added sugars, and zero additives.",
    deceptive_claims_flagged: [],
    fssai_violations: [],
    ingredient_breakdown: [
      { ingredient: "100% Organic Rolled Oats", purpose: "Whole Grain", concern_level: "LOW", personalized_warning: "Low glycemic, lowers LDL cholesterol." }
    ],
    nutrition_card: {
      serving_size: "100g",
      calories_kcal: 375.0,
      total_fat_g: 6.5,
      saturated_fat_g: 1.1,
      trans_fat_g: 0.0,
      total_carbs_g: 62.0,
      added_sugars_g: 0.0,
      sodium_mg: 5.0,
      breakdown: [
        { nutrient: "Dietary Fiber", amount_per_100g: "11.0g", daily_value_percent: "44%", clinical_evaluation: "Rich in beta-glucan heart-protective soluble fiber." },
        { nutrient: "Protein", amount_per_100g: "13.5g", daily_value_percent: "27%", clinical_evaluation: "Wholesome natural plant protein." },
        { nutrient: "Added Sugar", amount_per_100g: "0.0g", daily_value_percent: "0%", clinical_evaluation: "Zero refined sugars." }
      ]
    },
    nutrient_integrity: {
      protein: {
        declared_protein_g: 13.5,
        usable_protein_g: 8.1,
        pdcaas_score: 0.6,
        primary_sources: ["100% Organic Rolled Oats"],
        protein_to_calorie_percent: 14.4,
        amino_spiking_risk: false
      },
      fiber_type: "Natural Whole Grain Beta-Glucan",
      palm_oil_present: false,
      hidden_sugars_flagged: [],
      sodium_and_preservatives_risk: "Low",
      claims_matrix: [
        { claim: "100% Whole Grain", status: "VERIFIED", explanation: "Unprocessed whole grain cereal with intact germ and bran." }
      ]
    },
    healthier_alternative: {
      name: "Natureland Organics Whole Steel Cut Oats",
      product_name: "Natureland Organics Steel Cut Oats",
      health_score: 98,
      key_benefit: "Minimal processing, lowest glycemic index in grain category",
      price_comparison: "Comparable (~₹90/500g)",
      personalized_fit: "Optimal for blood glucose stabilization",
      type: "CLEAN_COMMERCIAL",
      delta_vs_scanned: "+3 pts",
      direct_pdp_url: "https://www.zepto.com/pn/natureland-steel-cut-oats/pvid/55667788",
      is_direct_pdp: true,
      pincode_available: true,
      reason: "100% organic whole grain."
    },
    clean_alternatives: [
      {
        name: "Natureland Organics Whole Steel Cut Oats",
        product_name: "Natureland Organics Steel Cut Oats",
        health_score: 98,
        key_benefit: "Lowest glycemic index",
        price_comparison: "Comparable",
        personalized_fit: "Peak whole food integrity",
        type: "CLEAN_COMMERCIAL",
        delta_vs_scanned: "+3 pts",
        direct_pdp_url: "https://www.zepto.com/pn/natureland-steel-cut-oats/pvid/55667788",
        is_direct_pdp: true,
        pincode_available: true,
        reason: "Unrefined whole grain."
      }
    ],
    is_food_label: true,
    label_type: "FULL_PANEL"
  }
};
