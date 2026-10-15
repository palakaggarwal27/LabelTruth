# Verified statistics extracted from research PDF (MSIT HVE Report) and 51-respondent primary survey

SURVEY_METRICS = {
    'sample_size': 51,
    'location': 'Delhi-NCR, India',
    'key_stats': [
        {
            'stat': '82.4%',
            'title': 'Rely on Front Claims or Legacy',
            'description': '31.4% are driven by front buzzwords (No Added Sugar, High Protein) and 51.0% by legacy brand trust. Only 13.7% turn the pack over to read ingredients.',
            'source': 'Primary Survey Q1 & Appendix A'
        },
        {
            'stat': '47.1%',
            'title': 'Completely Blind to Jargon',
            'description': 'Nearly half of urban consumers cannot identify terms like Maltodextrin, INS 150d, HFCS, or RDA %, finding them akin to indecipherable laboratory jargon.',
            'source': 'Primary Survey Q5 & MSIT Report Sec 3.2'
        },
        {
            'stat': '52.9%',
            'title': 'Unaware of Weight Order Principle',
            'description': 'More than half do not know FSSAI Regulation 5(2)(b) mandates ingredients in descending order of weight. Most assume alphabetical or random placement.',
            'source': 'Primary Survey Q6 & FSSAI 2020 Reg 5(2)(b)'
        },
        {
            'stat': '68.6%',
            'title': 'Misled by Sugar-Free Marketing',
            'description': '23.5% believe Sugar-Free is completely safe for diabetics, while 21.6% believe it uses safe fruit juice, unaware of high-GI bulking agents like Maltodextrin (GI 105-110).',
            'source': 'Primary Survey Q4 & MSIT Report Sec 2.3.1'
        },
        {
            'stat': '70.6%',
            'title': 'Frozen Dessert Mistaken for Ice Cream',
            'description': 'Chose Kwality Walls as their preferred ice cream brand despite it being legally a Frozen Dessert containing up to 10.2% edible vegetable/palm oil.',
            'source': 'Primary Survey Q9 & FSSAI Reg 2.1.7'
        },
        {
            'stat': '92.2%',
            'title': 'Want FSSAI Front Warning Labels',
            'description': '66.7% would stop buying junk food or switch to a green alternative if a Red Dot / Stop Sign was enforced, while 25.5% would exercise higher caution.',
            'source': 'Primary Survey Q8 & Supreme Court / FOPL Mandate'
        }
    ],
    'fssai_regulations': [
        {
            'regulation': 'Regulation 5(2)(b)',
            'name': 'Descending Weight Order Rule',
            'description': 'Ingredients must be declared in descending order of incoming weight at manufacture. Industry bypass: Splitting sugars across maltodextrin, liquid glucose, and invert syrup to push refined sugar lower down the label.'
        },
        {
            'regulation': 'Regulation 2.1.7',
            'name': 'Ice Cream vs. Frozen Dessert Standard',
            'description': 'Ice cream MUST be formulated exclusively with milk fat. Any substitution with vegetable oils (palm oil) must carry the prominent declaration Frozen Dessert.'
        },
        {
            'regulation': '2023 Amendment',
            'name': 'Whole Wheat (Atta) Threshold',
            'description': 'Requires at least 75% whole wheat for Whole Wheat Bread, but only 50% for Brown Bread. Brands use INS 150d (Caramel Colour IV) to dye Maida brown and market it as wholesome.'
        },
        {
            'regulation': 'AUPMR Visual Standard (Benchmark)',
            'name': 'Fruit Juice Honesty Standard',
            'description': 'In contrast to Japanese AUPMR where sliced fruit images require 100% fruit juice, Indian juices display vibrant sliced fruits while containing as little as 12% reconstituted fruit concentrate.'
        }
    ],
    'harmful_ins_codes': [
        {
            'code': 'INS 150d',
            'name': 'Caramel Colour IV',
            'function': 'Colorant / Darkening agent',
            'risk': 'Ammonia-processed; contains 4-MEI (4-methylimidazole), an animal carcinogen and suspected human carcinogen.'
        },
        {
            'code': 'INS 621',
            'name': 'Monosodium Glutamate (MSG)',
            'function': 'Flavor Enhancer',
            'risk': 'Excitotoxin linked to headaches, metabolic disruptions, and intense cravings.'
        },
        {
            'code': 'INS 211',
            'name': 'Sodium Benzoate',
            'function': 'Chemical Preservative',
            'risk': 'Combines with Ascorbic Acid (Vitamin C) under light and heat to synthesize carcinogenic Benzene.'
        },
        {
            'code': 'INS 102',
            'name': 'Tartrazine (Yellow 5)',
            'function': 'Synthetic Azo Dye',
            'risk': 'Strongly associated with hyperactivity and ADHD symptoms in children, plus bronchial asthma triggers.'
        },
        {
            'code': 'INS 320',
            'name': 'BHA (Butylated Hydroxyanisole)',
            'function': 'Antioxidant / Fat Stabilizer',
            'risk': 'Endocrine disruptor classified as reasonably anticipated to be a human carcinogen.'
        }
    ]
}
