import { PresetProduct } from '@/types';
import { LOCAL_DEMO_TIER_PRODUCTS } from './demoTiers';

export const FALLBACK_PRESET_PRODUCTS: PresetProduct[] = [
  {
    id: "chips-18",
    title: "Lay's India's Magic Masala Chips",
    subtitle: "Ultra-Processed Fried Snack · High Sodium & Palm Oil",
    description: "Ultra-processed fried potato snack formulated with 38% refined industrial palmolein oil, excessive sodium (750mg), and synthetic MSG (INS 621).",
    sample_result: LOCAL_DEMO_TIER_PRODUCTS.very_low
  },
  {
    id: "bread-38",
    title: "English Oven Brown Bread",
    subtitle: "Maida Disguised with Caramel Colour IV",
    description: "Marketed as wholesome brown bread, but formulated with 58% refined maida and dyed dark with INS 150d Caramel Colour IV to simulate bran.",
    sample_result: LOCAL_DEMO_TIER_PRODUCTS.low
  },
  {
    id: "cheese-74",
    title: "D'lecta Mozzarella Cheese Block",
    subtitle: "Natural Cow Milk Cheese · 24g Protein",
    description: "Authentic cow milk mozzarella with 24g bioavailable protein (PDCAAS 1.0) and zero chemical emulsifiers or artificial preservatives. Natural dairy fat and moderate sodium (640mg).",
    sample_result: LOCAL_DEMO_TIER_PRODUCTS.moderate
  },
  {
    id: "yogurt-78",
    title: "Epigamia Natural Greek Yogurt",
    subtitle: "Probiotic Unsweetened High-Protein Dairy",
    description: "High-protein unsweetened dairy with 8g bioavailable protein (PDCAAS 1.0), live active probiotic cultures, and zero added cane sugar.",
    sample_result: LOCAL_DEMO_TIER_PRODUCTS.high
  },
  {
    id: "oats-95",
    title: "Organic Whole Rolled Oats",
    subtitle: "100% Unrefined Whole Grain · Rich in Beta-Glucan",
    description: "100% certified whole grain unrefined rolled oats with 11g soluble beta-glucan fiber, zero added sugar, zero sodium, and zero preservatives.",
    sample_result: LOCAL_DEMO_TIER_PRODUCTS.very_high
  }
];
