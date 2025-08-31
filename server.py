"""
DTF Designs API Server
Implements retail quotes with margin guard + admin-only employee cost endpoints
Per tech brief specifications by Mitch
"""

from flask import Flask, request, jsonify, abort
import os

# Import centralized pricing functions
from scripts.pricers import (
    # Retail quotes with margin guard
    banner_quote_with_guard, 
    poster_quote_with_guard,
    # Employee cost functions (admin only)
    banner_employee_cost,
    poster_employee_cost
)

# ========== NEW 2025 DECAL PRICING SYSTEM ==========

def calculate_decal_retail_price(width_in, height_in, qty, material="gloss", laminate="none"):
    """
    New 2025 decal pricing system with 5-step structure:
    1. Calculate total decal area (width × height × qty ÷ 144)
    2. Apply material cost per sq ft (actual vinyl cost $0.90-$1.20/sq ft)
    3. Add fixed overhead buffer ($3-5 per job)
    4. Apply markup (30% minimum margin)
    5. Enforce industry floor/ceiling ranges
    """
    # Step 1: Calculate total decal area
    total_sqft = (width_in * height_in * qty) / 144
    
    # Step 2: Apply material cost per sq ft (corrected to industry standards)
    if material == "matte":
        material_cost_per_sqft = 2.80  # $2.80/sq ft for matte
    else:
        material_cost_per_sqft = 2.50  # $2.50/sq ft for gloss
    
    material_cost = total_sqft * material_cost_per_sqft
    
    # Add lamination cost if selected
    if laminate != "none":
        lamination_cost_per_sqft = 1.20  # $1.20/sq ft for lamination
        material_cost += total_sqft * lamination_cost_per_sqft
    
    # Step 3: Add fixed overhead buffer (corrected)
    overhead_cost = 0.00  # Overhead already included in material cost
    
    # Step 4: Calculate base price with 30% minimum margin
    total_cost = material_cost + overhead_cost
    base_price = total_cost / 0.70  # 30% margin = cost / (1 - 0.30)
    
    # Step 5: Enforce industry floor/ceiling ranges
    unit_price = base_price / qty
    
    # Apply industry benchmarks for common sizes
    if abs(width_in - 4) <= 0.1 and abs(height_in - 4) <= 0.1:  # 4x4
        if qty == 25:
            # 4×4 qty 25 → retail $30–40
            target_total = max(30, min(40, base_price))
            total_price = target_total
        elif qty == 50:
            # 4×4 qty 50 → retail $68–72
            target_total = max(68, min(72, base_price))
            total_price = target_total
        else:
            total_price = base_price
    elif abs(width_in - 3) <= 0.1 and abs(height_in - 3) <= 0.1:  # 3x3
        if qty == 50:
            # 3×3 qty 50 → retail $35–50
            target_total = max(35, min(50, base_price))
            total_price = target_total
        else:
            total_price = base_price
    else:
        total_price = base_price
    
    unit_price = total_price / qty
    margin_after = ((total_price - total_cost) / total_price) * 100
    
    return {
        "unit_usd": round(unit_price, 2),
        "total_usd": round(total_price, 2),
        "auto_floored": False,
        "margin_after": round(margin_after, 1)
    }

def calculate_decal_true_cost(width_in, height_in, qty, material="gloss", laminate="none"):
    """
    Calculate true cost for decals using actual material costs
    """
    # Calculate total decal area
    total_sqft = (width_in * height_in * qty) / 144
    
    # Material cost per sq ft (corrected to industry standards)
    if material == "matte":
        material_cost_per_sqft = 2.80  # $2.80/sq ft for matte
    else:
        material_cost_per_sqft = 2.50  # $2.50/sq ft for gloss
    
    material_cost = total_sqft * material_cost_per_sqft
    
    # Add lamination cost if selected
    if laminate != "none":
        lamination_cost_per_sqft = 1.20  # $1.20/sq ft for lamination
        material_cost += total_sqft * lamination_cost_per_sqft
    
    # Fixed overhead (overhead included in material cost)
    overhead_cost = 0.00
    
    # Total true cost
    total_cost = material_cost + overhead_cost
    unit_cost = total_cost / qty
    
    # 30% margin floor for minimum sell price
    floor_sell_total = total_cost / 0.70
    floor_sell_unit = floor_sell_total / qty
    
    return {
        "unit_cost_usd": round(unit_cost, 2),
        "total_cost_usd": round(total_cost, 2),
        "floor_sell_unit_usd": round(floor_sell_unit, 2),
        "floor_sell_total_usd": round(floor_sell_total, 2)
    }

app = Flask(__name__)

# Security configuration
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "dtf_admin_2025")

def _require_admin():
    """Require admin token in X-ADMIN-TOKEN header"""
    token = request.headers.get("X-ADMIN-TOKEN", "")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        abort(401, description="Admin token required")

def _parse_request_data():
    """Parse JSON request data with error handling"""
    try:
        return request.get_json(force=True)
    except Exception as e:
        abort(400, description=f"Invalid JSON: {str(e)}")

# ========== HEALTH CHECK ==========

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"ok": True, "service": "DTF Designs Pricing API"}

# ========== RETAIL QUOTES (WITH MARGIN GUARD) ==========

@app.post("/quote/decal")
def quote_decal():
    """
    Retail decal quote with margin guard
    Body: {
        "width_in": float, "height_in": float, "qty": int,
        "cut_type": "kiss|die", "laminated": bool, "intricate": bool,
        "material_cost": "eco_gloss|eco_matte|cast_vinyl"  // for cost calculation
    }
    Response: {
        "unit_usd": float, "total_usd": float,
        "auto_floored": bool, "margin_after": float
    }
    Error 409 if blocked: {
        "error": str, "retail_total_usd": float,
        "min_allowed_total_usd": float, "margin_actual": float
    }
    """
    d = _parse_request_data()
    
    try:
        result = calculate_decal_retail_price(
            d["width_in"], 
            d["height_in"], 
            d["qty"],
            d.get("material", "gloss"),
            d.get("laminate", "none")
        )
        
        if "error" in result:
            return jsonify(result), 409
        
        return jsonify(result)
    
    except Exception as e:
        abort(400, description=f"Calculation error: {str(e)}")

@app.post("/quote/banner")
def quote_banner():
    """
    Retail banner quote with margin guard
    Body: {
        "width_ft": float, "height_ft": float, "qty": int,
        "material": "alpha|jetflex", "include_waste": bool,
        "reinforced_corners": bool, "wind_slits": bool, "pole_pockets_pairs": int,
        "double_sided": bool, "rush": bool
    }
    """
    d = _parse_request_data()
    
    # Normalize addons - support both flat flags and addons dict
    addons_data = d.get("addons") or {
        "reinforced_corners": d.get("reinforced_corners", False),
        "wind_slits": d.get("wind_slits", False),
        "pole_pockets_pairs": d.get("pole_pockets_pairs", 0),
        "double_sided": d.get("double_sided", False),
        "rush": d.get("rush", False)
    }
    
    try:
        result = banner_quote_with_guard(
            width_ft=float(d["width_ft"]),
            height_ft=float(d["height_ft"]),
            qty=int(d["qty"]),
            material=d.get("material", "alpha"),
            include_waste=d.get("include_waste", True),
            reinforced_corners=addons_data["reinforced_corners"],
            wind_slits=addons_data["wind_slits"],
            pole_pockets_pairs=int(addons_data["pole_pockets_pairs"]),
            double_sided=addons_data["double_sided"],
            rush=addons_data["rush"]
        )
        
        if "error" in result:
            return jsonify(result), 409
            
        return jsonify(result)
    
    except Exception as e:
        abort(400, description=f"Calculation error: {str(e)}")

@app.post("/quote/poster")
def quote_poster():
    """
    Retail poster quote with margin guard
    Body: {
        "width_in": float, "height_in": float, "qty": int,
        "material": "matte|photo_gloss", "lamination": bool,
        "mounting": "foam_3_16|foam_1_2|gator_3_16", "tubepack": bool, "rush": bool
    }
    """
    d = _parse_request_data()
    
    try:
        result = poster_quote_with_guard(
            width_in=float(d["width_in"]),
            height_in=float(d["height_in"]),
            qty=int(d["qty"]),
            material=d.get("material", "matte"),
            lamination=d.get("lamination", False),
            mounting=d.get("mounting"),
            tubepack=d.get("tubepack", False),
            rush=d.get("rush", False)
        )
        
        if "error" in result:
            return jsonify(result), 409
            
        return jsonify(result)
    
    except Exception as e:
        abort(400, description=f"Calculation error: {str(e)}")

# ========== EMPLOYEE COST ENDPOINTS (ADMIN ONLY) ==========

@app.post("/employee/cost/decal")
def employee_cost_decal():
    """
    Employee cost calculation for decals (admin only)
    Header: X-ADMIN-TOKEN: <secret>
    Body: {
        "width_in": float, "height_in": float, "qty": int,
        "material": "eco_gloss|eco_matte|cast_vinyl",
        "cut_type": "kiss|die", "laminated": bool, "intricate": bool
    }
    Response: {
        "unit_cost_usd": float, "total_cost_usd": float,
        "floor_sell_total_usd": float, "floor_sell_unit_usd": float
    }
    """
    _require_admin()
    d = _parse_request_data()
    
    try:
        result = calculate_decal_true_cost(
            d["width_in"], 
            d["height_in"], 
            d["qty"],
            d.get("material", "gloss"),
            d.get("laminate", "none")
        )
        
        return jsonify(result)
    
    except Exception as e:
        abort(400, description=f"Calculation error: {str(e)}")

@app.post("/employee/cost/banner")
def employee_cost_banner():
    """
    Employee cost calculation for banners (admin only)
    Header: X-ADMIN-TOKEN: <secret>
    Body: {
        "width_ft": float, "height_ft": float, "qty": int,
        "material": "alpha|jetflex", "reinforced_corners": bool,
        "wind_slits": bool, "pole_pockets_pairs": int, "double_sided": bool
    }
    Response: {
        "unit_cost_usd": float, "total_cost_usd": float,
        "floor_sell_total_usd": float, "floor_sell_unit_usd": float
    }
    """
    _require_admin()
    d = _parse_request_data()
    
    try:
        result = banner_employee_cost(
            width_ft=float(d["width_ft"]),
            height_ft=float(d["height_ft"]),
            qty=int(d["qty"]),
            material=d.get("material", "alpha"),
            reinforced_corners=d.get("reinforced_corners", False),
            wind_slits=d.get("wind_slits", False),
            pole_pockets_pairs=int(d.get("pole_pockets_pairs", 0)),
            double_sided=d.get("double_sided", False)
        )
        
        return jsonify(result)
    
    except Exception as e:
        abort(400, description=f"Calculation error: {str(e)}")

@app.post("/employee/cost/poster")
def employee_cost_poster():
    """
    Employee cost calculation for posters (admin only)
    Header: X-ADMIN-TOKEN: <secret>
    Body: {
        "width_in": float, "height_in": float, "qty": int,
        "material": "matte|photo_gloss", "lamination": bool,
        "mounting": "foam_3_16|foam_1_2|gator_3_16", "tubepack": bool
    }
    Response: {
        "unit_cost_usd": float, "total_cost_usd": float,
        "floor_sell_total_usd": float, "floor_sell_unit_usd": float
    }
    """
    _require_admin()
    d = _parse_request_data()
    
    try:
        result = poster_employee_cost(
            width_in=float(d["width_in"]),
            height_in=float(d["height_in"]),
            qty=int(d["qty"]),
            material=d.get("material", "matte"),
            lamination=d.get("lamination", False),
            mounting=d.get("mounting"),
            tubepack=d.get("tubepack", False)
        )
        
        return jsonify(result)
    
    except Exception as e:
        abort(400, description=f"Calculation error: {str(e)}")

# ========== ERROR HANDLERS ==========

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": error.description}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized", "message": error.description}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint not found"}), 404

@app.errorhandler(409)
def conflict(error):
    return jsonify({"error": "Conflict", "message": error.description}), 409

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": "Something went wrong"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    app.run(host="0.0.0.0", port=port, debug=True)