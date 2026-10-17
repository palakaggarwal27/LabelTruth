# Verified dual-survey dataset: N=51 Primary Survey + N=23,491+ National Macro Study (LocalCircles / FSSAI data)

SURVEY_METRICS = {
    'sample_size': 51,
    'national_sample_size': 23491,
    'location': 'Pan-India & Delhi-NCR, India',
    'key_stats': [
        {
            'stat': '82.4%',
            'title': 'Rely on Front Claims or Legacy',
            'description': '31.4% are driven by front buzzwords (No Added Sugar, High Protein) and 51.0% by legacy brand trust. Only 13.7% turn the pack over to read ingredients.',
            'source': 'Primary Survey Q1 & Appendix A (N=51)'
        },
        {
            'stat': '47.1%',
            'title': 'Completely Blind to Jargon',
            'description': 'Nearly half of urban consumers cannot identify terms like Maltodextrin, INS 150d, HFCS, or RDA %, finding them akin to indecipherable laboratory jargon.',
            'source': 'Primary Survey Q5 & MSIT Report Sec 3.2 (N=51)'
        },
        {
            'stat': '52.9%',
            'title': 'Unaware of Weight Order Principle',
            'description': 'More than half do not know FSSAI Regulation 5(2)(b) mandates ingredients in descending order of weight. Most assume alphabetical or random placement.',
            'source': 'Primary Survey Q6 & FSSAI 2020 Reg 5(2)(b) (N=51)'
        },
        {
            'stat': '68.6%',
            'title': 'Misled by Sugar-Free Marketing',
            'description': '23.5% believe Sugar-Free is completely safe for diabetics, while 21.6% believe it uses safe fruit juice, unaware of high-GI bulking agents like Maltodextrin (GI 105-110).',
            'source': 'Primary Survey Q4 & MSIT Report Sec 2.3.1 (N=51)'
        },
        {
            'stat': '70.6%',
            'title': 'Frozen Dessert Mistaken for Ice Cream',
            'description': 'Chose Kwality Walls as their preferred ice cream brand despite it being legally a Frozen Dessert containing up to 10.2% edible vegetable/palm oil.',
            'source': 'Primary Survey Q9 & FSSAI Reg 2.1.7 (N=51)'
        },
        {
            'stat': '92.2%',
            'title': 'Want FSSAI Front Warning Labels',
            'description': '66.7% would stop buying junk food or switch to a green alternative if a Red Dot / Stop Sign was enforced, while 25.5% would exercise higher caution.',
            'source': 'Primary Survey Q8 & Supreme Court / FOPL Mandate (N=51)'
        }
    ],
    'national_stats': [
        {
            'stat': '88.0%',
            'title': 'Demand Large Front Warning Labels',
            'description': '88% of 23,491+ surveyed Indian consumers demand prominent front warning labels on packaged ultra-processed foods displaying high salt, sugar, or saturated fat.',
            'source': 'National Macro Study (LocalCircles N=23,491+)'
        },
        {
            'stat': '80.0%',
            'title': 'Demand Single-Nutrient Overreach Alerts',
            'description': '8 out of 10 consumers state that exceeding the maximum daily threshold for even ONE critical nutrient (e.g. sodium or saturated fat) must trigger a red warning.',
            'source': 'National Macro Study (LocalCircles N=23,491+)'
        },
        {
            'stat': '90.0%',
            'title': 'Demand Total Sugar/Fat Standard',
            'description': '90% of citizens demand that regulation evaluate Total Sugar and Total Saturated Fat instead of loophole claims like "No Added Sugar" or "Zero Cholesterol".',
            'source': 'National Macro Study (LocalCircles N=23,491+)'
        },
        {
            'stat': '76.5%',
            'title': 'Misled by Negative-Nutrient Omission',
            'description': 'Over 3 in 4 consumers are actively deceived when brands omit high sodium and palm oil while aggressively advertising "0% Trans Fat".',
            'source': 'National Consumer Protection Report'
        }
    ],
    'fssai_regulations': [
        {
            'regulation': 'Regulation 5(2)(b)',
            'name': 'Descending Weight Order Principle',
            'description': 'Ingredients must appear in descending order of incoming weight at time of manufacture. Dominant ingredient is always #1.',
            'impact': 'Prevents brands from claiming a product is "Whole Grain" or "Hazelnut" when sugar and maida constitute over 60% of product mass.',
            'loophole_exposed': 'Splitting sugars across maltodextrin, invert syrup, liquid glucose, and dextrose to artificially push sugar down the list.'
        },
        {
            'regulation': 'Regulation 2.1.7',
            'name': 'Ice Cream vs. Frozen Dessert Standard',
            'description': 'Real ice cream MUST use 100% dairy milk fat. Any substitution with vegetable oils (palm oil) is legally a Frozen Dessert.',
            'impact': 'Protects cardiovascular health against high palmitic acid saturated fats in desserts marketed to children.',
            'loophole_exposed': 'Using phonetic branding like "Creme", "Rich & Creamy", and parlor displays without disclosing vegetable fat.'
        },
        {
            'regulation': '2023 Amendment',
            'name': 'Whole Wheat (Atta) Threshold',
            'description': 'Bread must contain >=75% whole wheat to be labeled Whole Wheat Bread, but Brown Bread requires only 50%.',
            'impact': 'Helps consumers distinguish genuine whole wheat grains from dyed white flour.',
            'loophole_exposed': 'Adding INS 150d (Caramel Colour IV) to dye 100% Maida dark brown, misleading buyers into thinking it is wholesome atta.'
        },
        {
            'regulation': 'Regulation 4(1)',
            'name': 'Front-of-Pack Labelling (FOPL) Mandate',
            'description': 'Mandates clear thresholds for High in Fat, Sugar, and Salt (HFSS) with visual traffic light or warning star indicators.',
            'impact': 'Allows immediate 3-second comprehension for consumers, elderly individuals, and parents.',
            'loophole_exposed': 'Hiding behind complicated Per Serving and RDA percentages based on tiny unrealistic 15g portion sizes.'
        }
    ],
    'harmful_ins_codes': [
        {
            'code': 'Maltodextrin',
            'name': 'High-GI Bulking Carbohydrate',
            'function': 'Bulking agent, texturizer, disguised filler',
            'risk': 'Glycemic Index of 105-110 (higher than table sugar at 65). Causes extreme blood sugar surges and insulin spiking.',
            'disease_contraindications': ['Type-2 Diabetes', 'Pre-diabetes', 'PCOS', 'Insulin Resistance', 'Fatty Liver (NAFLD)']
        },
        {
            'code': 'INS 150d',
            'name': 'Caramel Colour IV (Sulfite Ammonia)',
            'function': 'Synthetic brown dye used in colas, brown breads, and sauces',
            'risk': 'Manufactured using ammonia and sulfites, creating trace 4-Methylimidazole (4-MEI), a suspected carcinogen.',
            'disease_contraindications': ['General Health Concern', 'Asthma', 'Sulfite Sensitivity']
        },
        {
            'code': 'Palm Oil',
            'name': 'Refined Palm / Palmolein Fat',
            'function': 'Cheap emulsified frying and bulking fat',
            'risk': 'Contains >50% palmitic acid (saturated fat). Increases arterial stiffness, LDL-C, and hepatic lipid accumulation.',
            'disease_contraindications': ['Hypertension (High BP)', 'Cardiovascular Disease', 'High Cholesterol', 'Fatty Liver (NAFLD)']
        },
        {
            'code': 'INS 621 / 627 / 631',
            'name': 'MSG & Disodium Guanylate / Inosinate',
            'function': 'Hyper-palatable synthetic umami flavor boosters',
            'risk': 'Triggers rapid overconsumption and high sodium intake, causing headaches and flushing in sensitive individuals.',
            'disease_contraindications': ['Hypertension (High BP)', 'Chronic Kidney Disease', 'Hyperuricemia (Gout)']
        },
        {
            'code': 'Polydextrose / Inulin Isolates',
            'name': 'Synthetic Fiber Concentrates',
            'function': 'Industrial fiber booster to mask low whole-grain content',
            'risk': 'Lacks the micronutrient and mineral benefits of whole grains; causes severe bloating and gastrointestinal distress.',
            'disease_contraindications': ['IBS', 'Digestive Sensitivity', 'SIBO']
        },
        {
            'code': 'Ethylene Oxide (EtO)',
            'name': 'Pesticide & Sterilizing Residue',
            'function': 'Agricultural fumigant found in spices and processed mixes',
            'risk': 'Group 1 carcinogen banned by international food agencies; linked to lymphoid and breast malignancies.',
            'disease_contraindications': ['Carcinogen Risk', 'Cellular Toxicity']
        }
    ]
}
