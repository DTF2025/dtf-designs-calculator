import math

# Professional Banner Pricing Configuration - Canton, OH (+100mi)
BANNER_CONFIG = {
    "generated": "2025-08-30",
    "region": "Canton, OH (+100mi)",
    "units": "feet",
    "min_job_usd": 35.0,
    "waste_buffer": [
        {
            "min_sqft": 0.0,
            "max_sqft": 14.999,
            "add_sqft": 1.0
        },
        {
            "min_sqft": 15.0,
            "max_sqft": 30.0,
            "add_sqft": 1.5
        },
        {
            "min_sqft": 30.001,
            "max_sqft": None,
            "add_sqft": 2.0
        }
    ],
    "rate_per_sqft_by_qty": [
        {
            "qty_min": 1,
            "qty_max": 4,
            "rate": 5.75
        },
        {
            "qty_min": 5,
            "qty_max": 9,
            "rate": 5.25
        },
        {
            "qty_min": 10,
            "qty_max": 24,
            "rate": 4.85
        },
        {
            "qty_min": 25,
            "qty_max": 49,
            "rate": 4.5
        },
        {
            "qty_min": 50,
            "qty_max": 99,
            "rate": 4.30
        },
        {
            "qty_min": 100,
            "qty_max": None,
            "rate": 4.15
        }
    ],
    "materials": {
        "alpha": {
            "display_name": "ALPHA Premium Matte Frontlit Banner 13oz",
            "adder_per_sqft": 0.0,
            "per_banner_min_bump": 0.0
        },
        "jetflex": {
            "display_name": "JetFlex® FL Gloss White 13oz",
            "adder_per_sqft": 0.25,
            "per_banner_min_bump": 5.0
        }
    },
    "addons": {
        "rush_pct": 0.25,
        "reinforced_corners_usd": 6.0,
        "wind_slits_usd": 10.0,
        "pole_pockets_pair_usd": 10.0,
        "double_sided_multiplier": 1.8
    }
}

def _waste_added(area):
    """Calculate waste buffer based on area"""
    for r in BANNER_CONFIG["waste_buffer"]:
        lo = r["min_sqft"]
        hi_val = r["max_sqft"]
        if (area >= lo) and (hi_val is None or area <= hi_val):
            return area + r["add_sqft"]
    return area

def _rate_for_qty(qty):
    """Get pricing rate based on quantity"""
    for band in BANNER_CONFIG["rate_per_sqft_by_qty"]:
        lo, hi = band["qty_min"], band["qty_max"]
        if (qty >= lo) and (hi is None or qty <= hi):
            return band["rate"]
    return BANNER_CONFIG["rate_per_sqft_by_qty"][-1]["rate"]

def calculate_banner_price(width_ft, height_ft, qty, material="alpha", include_waste=True, rounded=True,
                          rush=False, reinforced_corners=False, wind_slits=False, pole_pockets_pairs=0, double_sided=False):
    """
    Professional banner pricing calculation
    """
    if material not in BANNER_CONFIG["materials"]:
        raise ValueError(f"Media not found: {material}. Available materials: {list(BANNER_CONFIG['materials'].keys())}")
    
    mat = BANNER_CONFIG["materials"][material]
    area = width_ft * height_ft
    billable = _waste_added(area) if include_waste else area
    base_rate = _rate_for_qty(qty)
    rate = base_rate + mat["adder_per_sqft"]

    price_each = billable * rate
    price_each = max(price_each, BANNER_CONFIG["min_job_usd"])

    # Add-on costs
    addons = BANNER_CONFIG["addons"]
    add_cost = 0.0
    if reinforced_corners: 
        add_cost += addons["reinforced_corners_usd"]
    if wind_slits: 
        add_cost += addons["wind_slits_usd"]
    if pole_pockets_pairs and pole_pockets_pairs > 0:
        add_cost += addons["pole_pockets_pair_usd"] * int(pole_pockets_pairs)
    price_each += add_cost

    # Apply multipliers
    if double_sided:
        price_each *= addons["double_sided_multiplier"]

    if rush:
        price_each *= (1.0 + addons["rush_pct"])

    return math.floor(price_each + 0.5) if rounded else round(price_each, 2)

def get_banner_materials():
    """Get available banner materials"""
    return [(key, data["display_name"]) for key, data in BANNER_CONFIG["materials"].items()]

def calculate_partner_banner_price(retail_price):
    """Partner gets 30% off retail pricing"""
    return round(retail_price * 0.70, 2)

def calculate_employee_banner_cost(width_ft, height_ft, qty, material="alpha"):
    """Employee true cost (NO waste, NO job minimum)."""
    area = (width_ft or 0) * (height_ft or 0)
    per_sqft = 0.80 if material == "alpha" else 0.86  # JetFlex example
    fixed = 0.60 + 4.00  # finishing fixed + setup+packaging
    cost_each = area * per_sqft + fixed
    return round(cost_each, 2)