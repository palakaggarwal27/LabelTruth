import { PresetProduct } from '@/types';

export const FALLBACK_PRESET_PRODUCTS: PresetProduct[] = [
  {
    id: "brown-bread",
    title: "Commercial Brown Bread",
    subtitle: "English Oven Brown Bread (Appendix C)",
    description: "Dark brown appearance implying whole grain nutrition, but refined maida is ingredient #1 with only 5% atta and dyed with INS 150d.",
    sample_result: {
      product_name: "English Oven Brown Bread",
      health_score: 38,
      personalized_verdict: "CAUTION",
      simple_summary: "This product markets itself as healthy brown bread, but the primary ingredient is refined wheat flour (Maida). Whole wheat Atta constitutes only 5%, and the brown hue is created artificially via Caramel Colour (INS 150d).",
      deceptive_claims_flagged: [
        "Front-of-pack implies whole grain brown bread, but 95% of grain is not whole wheat.",
        "Uses Class II Preservative 282 and chemical improvers 1100."
      ],
      fssai_violations: [
        "Exploits FSSAI Brown Bread threshold loophole: Wheat Flour (Maida) listed before Wheat Atta (5%) violating consumer expectation of whole grains.",
        "Artificial aesthetic darkening using INS 150d Caramel Colour to simulate bran content."
      ],
      ingredient_breakdown: [
        {
          ingredient: "Wheat Flour (Maida)",
          purpose: "Refined Flour base",
          concern_level: "HIGH",
          personalized_warning: "Refined carbs spike blood glucose rapidly; not suitable for diabetics or insulin resistance."
        },
        {
          ingredient: "Water",
          purpose: "Moisture base",
          concern_level: "LOW",
          personalized_warning: "Safe."
        },
        {
          ingredient: "Wheat Atta (5%)",
          purpose: "Whole grain flour token",
          concern_level: "LOW",
          personalized_warning: "Only 5% actual whole grain."
        },
        {
          ingredient: "Edible Vegetable Oil (Palm)",
          purpose: "Fat source / Shelf stabilizer",
          concern_level: "HIGH",
          personalized_warning: "High saturated fats, promotes atherogenic lipid profile."
        },
        {
          ingredient: "Caramel Colour (INS 150d)",
          purpose: "Synthetic Dark Colorant",
          concern_level: "HIGH",
          personalized_warning: "Ammonia process produces 4-MEI, classified as potentially carcinogenic."
        }
      ],
      nutrition_card: {
        serving_size: "100g",
        calories_kcal: 260.0,
        total_fat_g: 3.5,
        saturated_fat_g: 1.8,
        trans_fat_g: 0.0,
        total_carbs_g: 50.0,
        added_sugars_g: 7.2,
        sodium_mg: 450.0,
        breakdown: [
          {
            nutrient: "Energy",
            amount_per_100g: "260 kcal",
            daily_value_percent: "13%",
            clinical_evaluation: "Moderate energy density from refined wheat starch."
          },
          {
            nutrient: "Added Sugars",
            amount_per_100g: "7.2g",
            daily_value_percent: "14%",
            clinical_evaluation: "Added sugar used for yeast activation and shelf caramelization."
          },
          {
            nutrient: "Sodium",
            amount_per_100g: "450mg",
            daily_value_percent: "22%",
            clinical_evaluation: "Elevated sodium per 2-slice serving, requires monitoring for hypertension."
          }
        ]
      },
      nutrient_integrity: {
        protein: {
          declared_protein_g: 7.8,
          usable_protein_g: 2.1,
          pdcaas_score: 0.28,
          primary_sources: ["Wheat Gluten", "Wheat Flour"],
          protein_to_calorie_percent: 12.0,
          amino_spiking_risk: false
        },
        fiber_type: "Refined with trace bran",
        palm_oil_present: true,
        hidden_sugars_flagged: ["Liquid Glucose", "Invert Sugar Syrup"],
        sodium_and_preservatives_risk: "Moderate",
        claims_matrix: [
          {
            claim: "100% Brown Bread",
            status: "DECEPTIVE",
            explanation: "Coloured with INS 150d Caramel Colour IV, only 5% Atta."
          }
        ]
      },
      healthier_alternative: {
        name: "The Health Factory Zero Maida Bread",
        key_benefit: "100% Whole Wheat flour, zero Palm Oil, zero INS 150d",
        price_comparison: "1.2x of conventional bread",
        personalized_fit: "Contains whole grains and natural wheat germ."
      },
      clean_alternatives: [
        {
          name: "The Health Factory Zero Maida Bread",
          key_benefit: "100% Whole Wheat flour, zero Palm Oil, zero INS 150d",
          price_comparison: "1.2x of conventional bread",
          personalized_fit: "Contains whole grains and natural wheat germ."
        },
        {
          name: "Organic Whole Wheat Sourdough",
          key_benefit: "Wild fermented, low glycemic index, zero added industrial yeast",
          price_comparison: "1.5x of commercial bread",
          personalized_fit: "Improved digestibility and sustained satiety."
        }
      ],
      is_food_label: true,
      label_type: "FULL_PANEL"
    }
  },
  {
    id: "diet-coke",
    title: "Zero-Sugar Carbonated Beverage",
    subtitle: "Diet Coke / Coke Zero (Appendix C)",
    description: "Marketed as zero calorie and diabetes-friendly, but packed with intense artificial sweeteners (INS 950 Acesulfame K, INS 951 Aspartame).",
    sample_result: {
      product_name: "Diet Coke / Coke Zero",
      health_score: 24,
      personalized_verdict: "CAUTION",
      simple_summary: "Contains zero actual calories, but relies on artificial non-nutritive sweeteners and orthophosphoric acid which disrupts gut microbiome and insulin sensitivity.",
      deceptive_claims_flagged: [
        "Front-of-pack claims zero sugar, but triggers sweet taste receptors promoting metabolic confusion.",
        "Uses INS 150d synthetic caramel colour."
      ],
      fssai_violations: [
        "FSSAI requires warning that artificial sweeteners are not recommended for children."
      ],
      ingredient_breakdown: [
        {
          ingredient: "Carbonated Water",
          purpose: "Effervescent base",
          concern_level: "LOW",
          personalized_warning: "Safe."
        },
        {
          ingredient: "Acidity Regulator (INS 338)",
          purpose: "Orthophosphoric acid",
          concern_level: "MEDIUM",
          personalized_warning: "Excess phosphoric acid leaches bone calcium."
        },
        {
          ingredient: "Colour (INS 150d)",
          purpose: "Caramel Colour IV",
          concern_level: "HIGH",
          personalized_warning: "Contains 4-MEI carcinogen contaminant."
        },
        {
          ingredient: "Sweetener (INS 951 Aspartame)",
          purpose: "Intense Artificial Sweetener",
          concern_level: "HIGH",
          personalized_warning: "Contains phenylalanine; hazardous for PKU patients."
        }
      ],
      nutrition_card: {
        serving_size: "100ml",
        calories_kcal: 0.2,
        total_fat_g: 0.0,
        saturated_fat_g: 0.0,
        trans_fat_g: 0.0,
        total_carbs_g: 0.0,
        added_sugars_g: 0.0,
        sodium_mg: 12.0,
        breakdown: [
          {
            nutrient: "Energy",
            amount_per_100g: "0.2 kcal",
            daily_value_percent: "0%",
            clinical_evaluation: "Calorically inert, chemically sweetened."
          }
        ]
      },
      nutrient_integrity: {
        protein: {
          declared_protein_g: 0.0,
          usable_protein_g: 0.0,
          pdcaas_score: 0.0,
          primary_sources: [],
          protein_to_calorie_percent: 0.0,
          amino_spiking_risk: false
        },
        fiber_type: "Zero Fiber",
        palm_oil_present: false,
        hidden_sugars_flagged: ["INS 951 (Aspartame)", "INS 950 (Acesulfame Potassium)"],
        sodium_and_preservatives_risk: "Low",
        claims_matrix: [
          {
            claim: "Zero Calories & Sugar Free",
            status: "MISLEADING",
            explanation: "Calorie-free via synthetic non-nutritive chemical sweeteners."
          }
        ]
      },
      healthier_alternative: {
        name: "Raw Pressery Tender Coconut Water",
        key_benefit: "100% natural electrolytes, zero artificial sweeteners, zero synthetic colour",
        price_comparison: "1.3x of canned soda",
        personalized_fit: "Clean hydration with zero chemical additives."
      },
      clean_alternatives: [
        {
          name: "Raw Pressery Tender Coconut Water",
          key_benefit: "100% natural electrolytes, zero artificial sweeteners, zero synthetic colour",
          price_comparison: "1.3x of canned soda",
          personalized_fit: "Clean hydration with zero chemical additives."
        }
      ],
      is_food_label: true,
      label_type: "FULL_PANEL"
    }
  }
];
