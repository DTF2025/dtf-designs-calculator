import json

# Embedded pricing configuration
CONFIG = {
    "equip_overhead_per_sqft": 0.32,
    "grommet_cost_each": 0.09788,
    "tape_cost_per_ft": 0.36978,
    "ink_cost_per_ml": 0.71,
    "cleaning_allowance_ml": 0.05,
    "labor_rate_per_hr": 13.0,
    "setup_fee_default": 25.0,
    
    "coverage_ml_per_sqft": {"Light": 0.8, "Medium": 1.2, "Heavy": 1.6},
    "customer_types": {"retail": 0.0, "wholesale": 0.30, "partner": 0.30},
    
    "retail_rate_per_type": {
        "banner": 8.0,
        "laminate": 3.0
    },
    
    "media_catalog": [
        {"id": "BANNER_UF_13OZ_54x164", "name": "Ultraflex JetFlex FL Gloss 13oz", "type": "banner", "raw_cost_per_sqft": 0.2286},
        {"id": "LAM_AVERY_1360Z_54x150", "name": "Avery DOL 1360Z Gloss Laminate", "type": "laminate", "raw_cost_per_sqft": 0.7595},
        {"id": "LAM_AVERY_1460Z_54x150", "name": "Avery DOL 1460Z Matte Laminate", "type": "laminate", "raw_cost_per_sqft": 0.7895},
        {"id": "LAM_3M_8548G_54x150", "name": "3M 8548G Gloss Overlaminate", "type": "laminate", "raw_cost_per_sqft": 0.8295}
    ],
    
    "catalog": [
        {
            "category": "Decals",
            "calc_type": "area_psf",
            "finishing": {"banner_hems_grommets": True, "laminate_option": True}
        },
        {
            "category": "Yard Signs",
            "calc_type": "per_unit",
            "items": [
                {
                    "sku": "YS_18x24_4mm",
                    "name": "Coroplast Yard Sign 18x24 (Double-Sided)",
                    "blank_cost_each": 2.25,
                    "print_cost_each": 2.50,
                    "stake_cost_each": 0.45,
                    "default_retail_each": 14.00
                }
            ]
        },
        {
            "category": "Apparel",
            "calc_type": "apparel_tier",
            "items": [
                {"garment": "T-Shirt", "tiers": {"1-5": 25, "6-10": 22, "11-20": 19, "21-50": 17, "51-100": 16, "101+": 14}},
                {"garment": "Tank Top", "tiers": {"1-5": 23, "6-10": 20, "11-20": 18, "21-50": 16, "51-100": 15, "101+": 13}},
                {"garment": "Long-Sleeve Tee", "tiers": {"1-5": 30, "6-10": 27, "11-20": 24, "21-50": 22, "51-100": 20, "101+": 18}},
                {"garment": "Crewneck Sweat", "tiers": {"1-5": 35, "6-10": 32, "11-20": 29, "21-50": 27, "51-100": 25, "101+": 23}},
                {"garment": "Pullover Hoodie", "tiers": {"1-5": 38, "6-10": 35, "11-20": 31, "21-50": 29, "51-100": 27, "101+": 25}},
                {"garment": "Zip Hoodie", "tiers": {"1-5": 42, "6-10": 37, "11-20": 33, "21-50": 31, "51-100": 29, "101+": 27}}
            ],
            "extra_rules": {
                "extra_placement": 4.0,
                "rush_multiplier": 1.20,
                "size_addons": {"2XL": 2, "3XL": 3, "4XL": 4, "5XL": 5}
            }
        }
    ]
}

# Helper functions
def get_media_by_name(name):
    """Find media item by name"""
    for media in CONFIG["media_catalog"]:
        if media["name"] == name:
            return media
    return None

def get_category_config(category):
    """Get configuration for a specific category"""
    for cat in CONFIG["catalog"]:
        if cat["category"] == category:
            return cat
    return None

def get_apparel_tier_price(garment, qty):
    """Get price for apparel based on quantity tier"""
    apparel_config = get_category_config("Apparel")
    if not apparel_config:
        return 0
    
    for item in apparel_config["items"]:
        if item["garment"] == garment:
            tiers = item["tiers"]
            if qty >= 101:
                return tiers["101+"]
            elif qty >= 51:
                return tiers["51-100"]
            elif qty >= 21:
                return tiers["21-50"]
            elif qty >= 11:
                return tiers["11-20"]
            elif qty >= 6:
                return tiers["6-10"]
            else:
                return tiers["1-5"]
    return 0
