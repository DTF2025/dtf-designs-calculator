"""
DTF Designs Centralized Pricing Engine
Implements retail pricing + employee true cost + margin guard system
Per tech brief specifications by Mitch
"""

import json
import math
import os
# Decal pricing will be implemented inline

# Configuration file paths
RETAIL_PATH = os.environ.get("RETAIL_CONFIG", "./config/retail_pricing.json")
DECAL_COST_PATH = os.environ.get("DECALS_COST_CONFIG", "./config/employee_true_cost_decals.json")
BANNER_COST_PATH = os.environ.get("BANNERS_COST_CONFIG", "./config/employee_true_cost_banners.json")
POSTER_COST_PATH = os.environ.get("POSTERS_COST_CONFIG", "./config/employee_true_cost_posters.json")

# Load all configuration files
with open(RETAIL_PATH) as f:
    RETAIL = json.load(f)

# DECAL_COSTS removed - using new decals_pricing system

with open(BANNER_COST_PATH) as f:
    BANNER_COSTS = json.load(f)

with open(POSTER_COST_PATH) as f:
    POSTER_COSTS = json.load(f)

# ========== HELPER FUNCTIONS ==========

def _ladder_rate(ladder, qty: int) -> float:
    for lo, hi, rate in ladder:
        if lo <= qty <= hi:
            return rate
    return ladder[-1][2]

# Legacy decal pricing functions removed - using new 2025 system

def _waste_buffer(area, buffer_tiers):
    """Apply waste buffer based on area tiers"""
    for tier in buffer_tiers:
        if area >= tier["min"] and area <= tier["max"]:
            return area + tier["add"]
    return area

def _small_piece_fee(width_in, height_in, fees):
    """Calculate small piece fee based on minimum edge"""
    min_edge = min(width_in, height_in)
    if min_edge < 1.0:
        return fees["under_1in"]
    elif min_edge < 2.0:
        return fees["under_2in"]
    return 0.0

# ========== RETAIL PRICING FUNCTIONS ==========

# OLD decal_price_retail function DELETED - using decal_price() instead

def banner_price_retail(width_ft, height_ft, qty, material="alpha", 
                       reinforced_corners=False, wind_slits=False, 
                       pole_pockets_pairs=0, double_sided=False, rush=False,
                       include_waste=True):
    """
    Retail banner pricing per Mitch specifications:
    - Area with waste buffer applied
    - Ladder rate + material adder
    - Per-banner minimum bump if material requires it
    - Job minimum applies to whole job
    - Add-ons applied per banner, then multipliers
    """
    area_ft2 = width_ft * height_ft
    billable_area = _waste_buffer(area_ft2, RETAIL["waste_buffers"]["banners"]) if include_waste else area_ft2
    
    # Base rate + material adder
    base_rate = _ladder_rate(RETAIL["banners"]["ladder_per_sqft"], qty)
    material_adder = RETAIL["banners"]["materials"][material]["adder_per_sqft"]
    rate = base_rate + material_adder
    
    per_banner = billable_area * rate
    
    # Material-specific per-banner minimum (if any) - NOT tied to job minimum
    # This is separate from job minimum which applies to total job only
    
    subtotal = per_banner * qty
    
    # Apply job minimum to whole job
    subtotal = max(subtotal, RETAIL["job_minimums"]["banners"])
    
    # Add-ons per banner
    addons = RETAIL["banners"]["addons"]
    per_banner_addons = 0.0
    if reinforced_corners:
        per_banner_addons += addons["reinforced_corners"]
    if wind_slits:
        per_banner_addons += addons["wind_slits"]
    if pole_pockets_pairs > 0:
        per_banner_addons += addons["pole_pockets_pair"] * pole_pockets_pairs
    
    subtotal += per_banner_addons * qty
    
    # Multipliers
    if double_sided:
        subtotal *= addons["double_sided_mult"]
    if rush:
        subtotal *= (1.0 + addons["rush_pct"])
    
    return round(subtotal / qty, 2), round(subtotal, 2)

def poster_price_retail(width_in, height_in, qty, material="matte", 
                       lamination=False, mounting=None, tubepack=False, rush=False):
    """
    Retail poster pricing per Mitch specifications:
    - Area with waste buffer
    - Ladder rate + material adder
    - Lamination, mounting, tubepack adders per piece
    - Job minimum applies to whole job
    - Rush percentage multiplier
    """
    a = (width_in * height_in) / 144.0  # sqft per piece
    billable_area = _waste_buffer(a, RETAIL["waste_buffers"]["posters"])
    
    # Base rate + material adder
    base_rate = _ladder_rate(RETAIL["posters"]["ladder_per_sqft"], qty)
    material_adder = RETAIL["posters"]["materials"][material]["adder_per_sqft"]
    rate = base_rate + material_adder
    
    per_piece = billable_area * rate
    
    # Add-ons per piece
    if lamination:
        per_piece += billable_area * RETAIL["posters"]["lamination_per_sqft"]
    if mounting:
        per_piece += billable_area * RETAIL["posters"]["mounting_per_sqft"][mounting]
    if tubepack:
        per_piece += RETAIL["posters"]["tubepack_each"]
    
    subtotal = per_piece * qty
    
    # Apply job minimum
    subtotal = max(subtotal, RETAIL["job_minimums"]["posters"])
    
    # Rush multiplier
    if rush:
        subtotal *= (1.0 + RETAIL["posters"]["rush_pct"])
    
    return round(subtotal / qty, 2), round(subtotal, 2)

# ========== EMPLOYEE TRUE COST FUNCTIONS ==========

# decal_cost_true removed - using new decals_pricing.true_cost function

def banner_cost_true(width_ft, height_ft, qty, material="alpha",
                    reinforced_corners=False, wind_slits=False,
                    pole_pockets_pairs=0, double_sided=False, rush=False):
    """
    True cost calculation for banners (employee only)
    """
    area_ft2 = width_ft * height_ft
    
    # Base costs per sqft 
    material_cost = BANNER_COSTS["materials_cost_per_sqft"][material]
    ink_cost = BANNER_COSTS["ink_cost_per_sqft"]
    overhead_cost = BANNER_COSTS["machine_overhead_per_sqft"]
    finishing_cost = BANNER_COSTS["finishing_cost_per_sqft"]
    
    per_banner_cost = area_ft2 * (material_cost + ink_cost + overhead_cost + finishing_cost)
    
    # Fixed finishing cost per banner
    per_banner_cost += BANNER_COSTS["finishing_fixed_per_banner"]
    
    # Add-on costs
    addons = BANNER_COSTS["addons_cost"]
    if reinforced_corners:
        per_banner_cost += addons["reinforced_corners"]
    if wind_slits:
        per_banner_cost += addons["wind_slits"]
    if pole_pockets_pairs > 0:
        per_banner_cost += addons["pole_pockets_pair"] * pole_pockets_pairs
    
    # Double-sided extra cost (ink + overhead + finishing for second side)
    if double_sided:
        per_banner_cost += area_ft2 * BANNER_COSTS.get("second_side_extra_per_sqft", 0.525)
    
    # Total for quantity
    variable_total = per_banner_cost * qty
    
    # Fixed costs per job
    fixed_total = BANNER_COSTS["setup_cost_per_job"] + BANNER_COSTS["packaging_cost_per_job"]
    
    total_cost = variable_total + fixed_total
    return round(total_cost / qty, 2), round(total_cost, 2)

def poster_cost_true(width_in, height_in, qty, material="matte",
                    lamination=False, mounting=None, tubepack=False):
    """
    True cost calculation for posters (employee only)
    """
    a = (width_in * height_in) / 144.0  # sqft per piece
    
    # Base costs per sqft
    paper_cost = POSTER_COSTS["paper_cost_per_sqft"][material]
    ink_cost = POSTER_COSTS["ink_cost_per_sqft"]
    overhead_cost = POSTER_COSTS["machine_overhead_per_sqft"]
    
    per_piece_cost = a * (paper_cost + ink_cost + overhead_cost)
    
    # Add-on costs
    if lamination:
        per_piece_cost += a * POSTER_COSTS["lamination_cost_per_sqft"]
    if mounting:
        per_piece_cost += a * POSTER_COSTS["mounting_cost_per_sqft"][mounting]
    if tubepack:
        per_piece_cost += POSTER_COSTS["tubepack_each"]
    
    # Total for quantity
    variable_total = per_piece_cost * qty
    
    # Fixed costs per job
    fixed_total = POSTER_COSTS["setup_cost_per_job"] + POSTER_COSTS["packaging_cost_per_job"]
    
    total_cost = variable_total + fixed_total
    return round(total_cost / qty, 2), round(total_cost, 2)

# ========== MARGIN GUARD SYSTEM ==========

def calculate_margin_guard(retail_total, cost_total, min_margin_pct=None, mode=None):
    """
    Margin guard system implementation
    
    Args:
        retail_total: Total retail price
        cost_total: True cost total
        min_margin_pct: Minimum margin percentage (defaults to config)
        mode: "AUTO_FLOOR" or "BLOCK" (defaults to config)
    
    Returns:
        dict with guard results
    """
    if min_margin_pct is None:
        min_margin_pct = RETAIL["min_margin_floor_pct"]
    if mode is None:
        mode = RETAIL["floor_mode"]
    
    # Calculate actual margin
    actual_margin = (retail_total - cost_total) / retail_total if retail_total > 0 else 0.0
    
    # Check if margin is acceptable
    is_acceptable = actual_margin >= min_margin_pct
    
    if is_acceptable:
        return {
            "approved": True,
            "auto_floored": False,
            "final_total": retail_total,
            "actual_margin": actual_margin,
            "cost_total": cost_total
        }
    
    # Calculate floor price
    floor_total = cost_total / (1.0 - min_margin_pct)
    
    if mode == "AUTO_FLOOR":
        return {
            "approved": True,
            "auto_floored": True,
            "final_total": round(floor_total, 2),
            "actual_margin": min_margin_pct,
            "cost_total": cost_total,
            "original_retail": retail_total
        }
    
    elif mode == "BLOCK":
        return {
            "approved": False,
            "blocked": True,
            "retail_total": retail_total,
            "min_allowed_total": round(floor_total, 2),
            "actual_margin": actual_margin,
            "required_margin": min_margin_pct,
            "cost_total": cost_total
        }
    
    else:
        raise ValueError(f"Invalid floor_mode: {mode}")

# ========== INTEGRATED PRICING FUNCTIONS (WITH GUARD) ==========

# decal_quote_with_guard removed - using new decals_pricing.quote function

def banner_quote_with_guard(width_ft, height_ft, qty, material="alpha", 
                           reinforced_corners=False, wind_slits=False,
                           pole_pockets_pairs=0, double_sided=False, rush=False,
                           include_waste=True):
    """Get banner retail quote with margin guard applied"""
    # Calculate retail price
    unit_retail, total_retail = banner_price_retail(width_ft, height_ft, qty, material,
                                                   reinforced_corners, wind_slits, 
                                                   pole_pockets_pairs, double_sided, rush,
                                                   include_waste)
    
    # Calculate true cost (no rush in cost calculation)
    unit_cost, total_cost = banner_cost_true(width_ft, height_ft, qty, material,
                                           reinforced_corners, wind_slits,
                                           pole_pockets_pairs, double_sided)
    
    # Apply margin guard
    guard_result = calculate_margin_guard(total_retail, total_cost)
    
    # Build response
    result = {
        "unit_usd": round(guard_result["final_total"] / qty, 2),
        "total_usd": guard_result["final_total"],
        "auto_floored": guard_result.get("auto_floored", False),
        "margin_after": guard_result["actual_margin"]
    }
    
    if not guard_result["approved"]:
        result.update({
            "error": "Quote below minimum margin",
            "retail_total_usd": guard_result["retail_total"],
            "min_allowed_total_usd": guard_result["min_allowed_total"],
            "margin_actual": guard_result["actual_margin"]
        })
    
    return result

def poster_quote_with_guard(width_in, height_in, qty, material="matte",
                           lamination=False, mounting=None, tubepack=False, rush=False):
    """Get poster retail quote with margin guard applied"""
    # Calculate retail price
    unit_retail, total_retail = poster_price_retail(width_in, height_in, qty, material,
                                                   lamination, mounting, tubepack, rush)
    
    # Calculate true cost (no rush in cost calculation)
    unit_cost, total_cost = poster_cost_true(width_in, height_in, qty, material,
                                           lamination, mounting, tubepack)
    
    # Apply margin guard
    guard_result = calculate_margin_guard(total_retail, total_cost)
    
    # Build response
    result = {
        "unit_usd": round(guard_result["final_total"] / qty, 2),
        "total_usd": guard_result["final_total"],
        "auto_floored": guard_result.get("auto_floored", False),
        "margin_after": guard_result["actual_margin"]
    }
    
    if not guard_result["approved"]:
        result.update({
            "error": "Quote below minimum margin",
            "retail_total_usd": guard_result["retail_total"],
            "min_allowed_total_usd": guard_result["min_allowed_total"],
            "margin_actual": guard_result["actual_margin"]
        })
    
    return result

# ========== EMPLOYEE COST ENDPOINTS (ADMIN ONLY) ==========

# decal_employee_cost removed - using new decals_pricing.true_cost function

def banner_employee_cost(width_ft, height_ft, qty, material="alpha",
                        reinforced_corners=False, wind_slits=False,
                        pole_pockets_pairs=0, double_sided=False):
    """Employee cost endpoint - returns cost + floor sell prices"""
    unit_cost, total_cost = banner_cost_true(width_ft, height_ft, qty, material,
                                           reinforced_corners, wind_slits,
                                           pole_pockets_pairs, double_sided)
    
    floor_margin = BANNER_COSTS["floor_margin_pct"]
    floor_sell_total = total_cost / (1.0 - floor_margin)
    floor_sell_unit = floor_sell_total / qty
    
    return {
        "unit_cost_usd": unit_cost,
        "total_cost_usd": total_cost,
        "floor_sell_total_usd": round(floor_sell_total, 2),
        "floor_sell_unit_usd": round(floor_sell_unit, 2)
    }

def poster_employee_cost(width_in, height_in, qty, material="matte",
                        lamination=False, mounting=None, tubepack=False):
    """Employee cost endpoint - returns cost + floor sell prices"""
    unit_cost, total_cost = poster_cost_true(width_in, height_in, qty, material,
                                           lamination, mounting, tubepack)
    
    floor_margin = POSTER_COSTS["floor_margin_pct"]
    floor_sell_total = total_cost / (1.0 - floor_margin)
    floor_sell_unit = floor_sell_total / qty
    
    return {
        "unit_cost_usd": unit_cost,
        "total_cost_usd": total_cost,
        "floor_sell_total_usd": round(floor_sell_total, 2),
        "floor_sell_unit_usd": round(floor_sell_unit, 2)
    }

# ========== LEGACY FUNCTION ALIASES (FOR BACKWARDS COMPATIBILITY) ==========

# Maintain compatibility with existing code
def banner_price(*args, **kwargs):
    """Legacy alias - use banner_price_retail instead"""
    return banner_price_retail(*args, **kwargs)

# Legacy decal_price removed - using new decal_price function above

def poster_price(*args, **kwargs):
    """Legacy alias - use poster_price_retail instead"""
    return poster_price_retail(*args, **kwargs)

# Legacy true_cost_decal removed - using new true_cost_decal function above

def floor_from_cost(total_cost, floor_pct=None):
    """Calculate floor price from cost"""
    if floor_pct is None:
        floor_pct = RETAIL["min_margin_floor_pct"]
    return round(total_cost / (1.0 - float(floor_pct)), 2)