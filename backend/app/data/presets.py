PRESET_PRODUCTS = [
    {
        "id": "brown-bread",
        "title": "Commercial Brown Bread",
        "subtitle": "English Oven Brown Bread (Appendix C)",
        "description": "Dark brown appearance implying whole grain nutrition, but refined maida is ingredient #1 with only 5% atta and dyed with INS 150d.",
        "sample_result": {
            "product_name": "English Oven Brown Bread",
            "health_score": 38,
            "personalized_verdict": "CAUTION",
            "simple_summary": "This product markets itself as healthy brown bread, but the primary ingredient is refined wheat flour (Maida). Whole wheat Atta constitutes only 5%, and the brown hue is created artificially via Caramel Colour (INS 150d).",
            "deceptive_claims_flagged": [
                "Front-of-pack implies whole grain brown bread, but 95% of grain is not whole wheat.",
                "Uses Class II Preservative 282 and chemical improvers 1100."
            ],
            "fssai_violations": [
                "Exploits FSSAI Brown Bread threshold loophole: Wheat Flour (Maida) listed before Wheat Atta (5%) violating consumer expectation of whole grains.",
                "Artificial aesthetic darkening using INS 150d Caramel Colour to simulate bran content."
            ],
            "ingredient_breakdown": [
                {
                    "ingredient": "Wheat Flour (Maida)",
                    "purpose": "Refined Flour base",
                    "concern_level": "HIGH",
                    "personalized_warning": "Refined carbs spike blood glucose rapidly; not suitable for diabetics or insulin resistance."
                },
                {
                    "ingredient": "Water",
                    "purpose": "Moisture base",
                    "concern_level": "LOW",
                    "personalized_warning": "Safe."
                },
                {
                    "ingredient": "Yeast",
                    "purpose": "Fermentation leavening",
                    "concern_level": "LOW",
                    "personalized_warning": "Safe."
                },
                {
                    "ingredient": "Wheat Atta (5%)",
                    "purpose": "Whole grain flour token",
                    "concern_level": "LOW",
                    "personalized_warning": "Only 5% actual whole grain."
                },
                {
                    "ingredient": "Edible Vegetable Oil (Palm)",
                    "purpose": "Fat source / Shelf stabilizer",
                    "concern_level": "HIGH",
                    "personalized_warning": "High saturated fats, promotes atherogenic lipid profile."
                },
                {
                    "ingredient": "Caramel Colour (INS 150d)",
                    "purpose": "Synthetic Dark Colorant",
                    "concern_level": "HIGH",
                    "personalized_warning": "Ammonia process produces 4-MEI, classified as potentially carcinogenic."
                },
                {
                    "ingredient": "Class II Preservative (282)",
                    "purpose": "Calcium Propionate mold inhibitor",
                    "concern_level": "LOW",
                    "personalized_warning": "Approved preservative; potential migraine sensitivity in children."
                }
            ],
            "healthier_alternative": {
                "name": "100% Whole Wheat Sourdough / Stoneground Atta Bread (e.g., The Baker's Dozen)",
                "key_benefit": "Zero maida, zero added caramel colour, made with traditional fermentation for low GI.",
                "price_comparison": "~1.3x typical commercial bread price (approx Rs 65 vs Rs 50).",
                "personalized_fit": "High soluble fiber and true whole grain bran; much safer for blood sugar and heart health."
            }
        }
    },
    {
        "id": "frozen-dessert",
        "title": "Chocolate Brownie Frozen Dessert",
        "subtitle": "Kwality Walls Confectionery (Appendix C)",
        "description": "Marketed in the ice cream cabinet, but formulated with 10.2% edible vegetable oil (palm oil) and liquid glucose instead of dairy milk fat.",
        "sample_result": {
            "product_name": "Kwality Walls Chocolate Brownie Frozen Dessert",
            "health_score": 24,
            "personalized_verdict": "AVOID (VIOLATES PROFILE)",
            "simple_summary": "This product is legally classified as a Frozen Dessert made with 10.2% Edible Vegetable Oil (Palm Oil), not real ice cream made from milk fat. It contains multiple hidden sugars including Maltodextrin and Liquid Glucose.",
            "deceptive_claims_flagged": [
                "Sold in ice cream parlors and cooling cabinets, confusing 70.6% of surveyed consumers.",
                "Sugar splitting across Liquid Glucose, Maltodextrin, and Sucrose hides ultra-high sugar density."
            ],
            "fssai_violations": [
                "FSSAI Regulation 2.1.7: Disqualified from using the term 'Ice Cream' due to substitution of dairy fat with hydrogenated vegetable oil.",
                "Carries INS 150d, INS 122, INS 133, and INS 102 synthetic dyes."
            ],
            "ingredient_breakdown": [
                {
                    "ingredient": "Water & Sugar",
                    "purpose": "Sweetened base",
                    "concern_level": "HIGH",
                    "personalized_warning": "Severe glycemic load."
                },
                {
                    "ingredient": "Palm Oil (10.2% Edible Veg Oil)",
                    "purpose": "Dairy fat replacement",
                    "concern_level": "HIGH",
                    "personalized_warning": "High saturated palmitic acid, adverse for cardiovascular and liver health."
                },
                {
                    "ingredient": "Maltodextrin",
                    "purpose": "Thickener & bulking agent",
                    "concern_level": "HIGH",
                    "personalized_warning": "Glycemic Index 105-110, severely hazardous for diabetes and pre-diabetes."
                },
                {
                    "ingredient": "Liquid Glucose",
                    "purpose": "Corn-derived sweet syrup",
                    "concern_level": "HIGH",
                    "personalized_warning": "Triggers rapid blood glucose surges."
                },
                {
                    "ingredient": "Food Colours (INS 150d, E122, E133, E102)",
                    "purpose": "Synthetic food dyes",
                    "concern_level": "HIGH",
                    "personalized_warning": "Tartrazine (E102) and Carmoisine (E122) linked to pediatric hyperactivity and sensitivities."
                }
            ],
            "healthier_alternative": {
                "name": "Amul Real Milk Ice Cream or Go Zero Zero-Sugar Real Dairy Tub",
                "key_benefit": "Made with 100% pure milk cream fat, zero vegetable oils, zero artificial azo dyes.",
                "price_comparison": "Equal or slightly lower price (Amul Rs 40-50 per cup).",
                "personalized_fit": "Natural dairy fats provide satiety without industrial hydrogenated trans-fat risk."
            }
        }
    },
    {
        "id": "real-juice",
        "title": "Packaged Real Fruit Juice",
        "subtitle": "Real Fruit Power Mixed Fruit (Appendix C)",
        "description": "Features splashy images of cut fruits on front, but contains only 12.03% mixed fruit concentrate, with water and added sugar filling the rest.",
        "sample_result": {
            "product_name": "Real Fruit Power Mixed Fruit Nectar",
            "health_score": 32,
            "personalized_verdict": "CAUTION",
            "simple_summary": "Despite the front imagery of freshly sliced orchard fruits, this drink contains only 12.03% reconstituted fruit concentrate. The bulk of the beverage is filtered water, added cane sugar, and synthetic acidity regulators.",
            "deceptive_claims_flagged": [
                "Front displays luscious slices of apple, orange, guava, but fruit content is only ~12%.",
                "Claims 'Healthy is Happy' while delivering approx 11-13g sugars per 100ml with no fruit dietary fiber."
            ],
            "fssai_violations": [
                "Bypasses Japanese AUPMR standard which prohibits sliced fruit images unless 100% juice.",
                "Strips natural cellular pectin and insoluble fiber, converting fruit fructose into liver-taxing liquid sugar."
            ],
            "ingredient_breakdown": [
                {
                    "ingredient": "Water",
                    "purpose": "Main solvent",
                    "concern_level": "LOW",
                    "personalized_warning": "Neutral."
                },
                {
                    "ingredient": "Mixed Fruit Concentrate (12.03%)",
                    "purpose": "Reconstituted juice base",
                    "concern_level": "LOW",
                    "personalized_warning": "Only 12% actual fruit portion."
                },
                {
                    "ingredient": "Sugar",
                    "purpose": "Added sweetening",
                    "concern_level": "HIGH",
                    "personalized_warning": "Liquid sucrose consumed without fiber leads to instant insulin spike."
                },
                {
                    "ingredient": "Acidity Regulator (INS 330)",
                    "purpose": "Citric acid preservative",
                    "concern_level": "LOW",
                    "personalized_warning": "Synthetic mold-fermented citric acid; minor tooth enamel concern."
                },
                {
                    "ingredient": "Natural Colour (INS 160a(ii)) & Flavours",
                    "purpose": "Aesthetic hue and aroma",
                    "concern_level": "LOW",
                    "personalized_warning": "Generally recognized as safe."
                }
            ],
            "healthier_alternative": {
                "name": "Cold-Pressed Raw Whole Fruit Juice (e.g., Raw Pressery) or Fresh Tender Coconut Water",
                "key_benefit": "Zero added table sugar, unheated enzyme preservation, natural electrolytes.",
                "price_comparison": "~1.5x (approx Rs 70-80 per bottle vs Rs 40 for packaged concentrate).",
                "personalized_fit": "Prevents fatty liver fructose shock and eliminates chemical preservatives."
            }
        }
    }
]
