"""
DTF Designs - 2025 Decal Pricing System
Complete rewrite based on new pricing configuration and CSV lookup tables.
"""

import json
import csv
import os
import math


def load_pricing_config():
    """Load the 2025 pricing configuration."""
    config_path = os.path.join('config', 'decal_pricing_2025.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def load_csv_table(table_name):
    """Load a CSV pricing table and return as dictionary."""
    table_path = os.path.join('tables', f'{table_name}.csv')
    pricing_data = {}
    
    if not os.path.exists(table_path):
        return pricing_data
        
    with open(table_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            size = row['size']
            pricing_data[size] = {}
            for qty_str in ['10', '25', '50', '100', '250', '500']:
                if qty_str in row:
                    pricing_data[size][int(qty_str)] = float(row[qty_str])
    
    return pricing_data


def get_csv_price_lookup(width, height, qty, cut_type, laminate):
    """
    Look up price in CSV tables for popular sizes.
    Returns None if size/qty not found in tables.
    """
    # Determine size category and format
    size_str = f"{int(width)}x{int(height)}"
    area = width * height
    
    # Determine which table to use
    table_name = None
    
    # Check if it's a bumper sticker (typically 3x11.5, 4x11, 4x12)
    if (width == 3 and height == 11.5) or (width == 4 and height in [11, 12]):
        if cut_type == 'kiss' and not laminate:
            table_name = 'bumper_kiss'
        elif cut_type == 'die' and not laminate:
            table_name = 'bumper_die'
        elif cut_type == 'kiss' and laminate:
            table_name = 'bumper_kiss_lam'
    
    # Check if it's a square
    elif width == height:
        if cut_type == 'kiss' and not laminate:
            table_name = 'popular_squares_kiss'
        elif cut_type == 'die' and not laminate:
            table_name = 'popular_squares_die'
        elif cut_type == 'kiss' and laminate:
            table_name = 'popular_squares_kiss_lam'
    
    # Check if it's a rectangle
    else:
        if cut_type == 'kiss' and not laminate:
            table_name = 'popular_rectangles_kiss'
        elif cut_type == 'die' and not laminate:
            table_name = 'popular_rectangles_die'
        elif cut_type == 'kiss' and laminate:
            table_name = 'popular_rectangles_kiss_lam'
    
    if not table_name:
        return None
    
    # Load the table
    pricing_data = load_csv_table(table_name)
    
    # Check if size exists in table
    if size_str not in pricing_data:
        return None
    
    size_pricing = pricing_data[size_str]
    
    # Find the exact quantity or closest higher quantity
    available_qtys = sorted(size_pricing.keys())
    selected_qty = None
    
    for avail_qty in available_qtys:
        if qty <= avail_qty:
            selected_qty = avail_qty
            break
    
    if selected_qty is None:
        # Use highest quantity tier
        selected_qty = max(available_qtys)
    
    unit_price = size_pricing[selected_qty]
    total_price = unit_price * qty
    
    return unit_price, total_price


def calculate_decal_price_2025(width, height, qty, material='gloss', cut_type='kiss', laminate=None):
    """
    Calculate decal pricing using 2025 system.
    First tries CSV lookup for popular sizes, falls back to configuration-based calculation.
    
    Args:
        width (float): Width in inches
        height (float): Height in inches  
        qty (int): Quantity
        material (str): 'gloss' or 'matte'
        cut_type (str): 'kiss' or 'die'
        laminate (str): None, 'gloss', or 'matte'
    
    Returns:
        tuple: (unit_price, total_price)
    """
    config = load_pricing_config()
    
    # First try CSV lookup for popular sizes
    has_laminate = laminate is not None and laminate != '' and laminate != 'none'
    csv_result = get_csv_price_lookup(width, height, qty, cut_type, has_laminate)
    
    if csv_result:
        unit_price, total_price = csv_result
        
        # Apply rounding rules from config
        unit_price = round_to_increment(unit_price, config['rounding']['unit_to'])
        total_price = round_to_increment(total_price, config['rounding']['total_to'])
        
        # Apply minimum job price
        if total_price < config['retail_job_minimum']:
            total_price = config['retail_job_minimum']
            unit_price = total_price / qty
        
        return unit_price, total_price
    
    # Fallback to configuration-based calculation
    return calculate_decal_price_from_config(width, height, qty, material, cut_type, laminate, config)


def calculate_decal_price_from_config(width, height, qty, material, cut_type, laminate, config):
    """
    Calculate decal pricing using JSON configuration for non-standard sizes.
    """
    area_sqft = (width * height) / 144.0  # Convert sq inches to sq feet
    total_area = area_sqft * qty
    
    # Find the pricing tier based on total area
    base_rate = None
    for tier in config['tiers_by_tba_sqft']:
        if total_area < tier['lt']:
            base_rate = tier['rate_sqft']
            break
    
    if base_rate is None:
        # Use the last tier (highest quantity)
        base_rate = config['tiers_by_tba_sqft'][-1]['rate_sqft']
    
    # Calculate base price per square foot
    price_per_sqft = base_rate
    
    # Add cut type adder
    if cut_type == 'die':
        price_per_sqft += config['adders_sqft']['die_cut']
    
    # Add laminate adder
    has_laminate = laminate is not None and laminate != '' and laminate != 'none'
    if has_laminate:
        price_per_sqft += config['adders_sqft']['laminate_gloss']
    
    # Calculate unit price
    unit_price = price_per_sqft * area_sqft
    
    # Apply small piece fee
    min_side = min(width, height)
    for fee_rule in config['small_piece_fee_each']:
        if min_side < fee_rule['min_side_in_lt']:
            unit_price += fee_rule['fee']
            break
    
    # Calculate total
    total_price = unit_price * qty
    
    # Apply rounding rules
    unit_price = round_to_increment(unit_price, config['rounding']['unit_to'])
    total_price = round_to_increment(total_price, config['rounding']['total_to'])
    
    # Apply minimum job price
    if total_price < config['retail_job_minimum']:
        total_price = config['retail_job_minimum']
        unit_price = total_price / qty
    
    return unit_price, total_price


def calculate_decal_true_cost_2025(width, height, qty, material='gloss', cut_type='kiss', laminate=None):
    """
    Calculate true cost using 2025 configuration.
    
    Returns:
        float: Total true cost
    """
    config = load_pricing_config()
    true_cost_config = config['true_cost']
    
    area_sqft = (width * height) / 144.0
    
    # Base material cost
    material_cost_sqft = true_cost_config['base_sqft'].get(material, true_cost_config['base_sqft']['gloss'])
    material_cost = material_cost_sqft * area_sqft * qty
    
    # Cut cost
    cut_cost_sqft = true_cost_config['cut_sqft'].get(cut_type, true_cost_config['cut_sqft']['kiss'])
    cut_cost = cut_cost_sqft * area_sqft * qty
    
    # Laminate cost
    laminate_cost = 0
    has_laminate = laminate is not None and laminate != '' and laminate != 'none'
    if has_laminate:
        laminate_cost = true_cost_config['laminate_sqft'] * area_sqft * qty
    
    # Fixed per job cost
    fixed_cost = true_cost_config['fixed_per_job']
    
    total_cost = material_cost + cut_cost + laminate_cost + fixed_cost
    
    return total_cost


def round_to_increment(value, increment):
    """Round value to the nearest increment."""
    return round(value / increment) * increment


def get_partner_price_2025(retail_price):
    """Calculate partner price with 30% discount."""
    config = load_pricing_config()
    return retail_price * (1 - config['partner_discount'])


# Wrapper functions to maintain compatibility with existing code
def decal_price_2025(width, height, qty, material='gloss', cut='kiss', lam=None):
    """
    Wrapper for backward compatibility.
    Maps old parameter names to new function.
    """
    # Map old 'cut' parameter to 'cut_type'
    cut_type = cut
    
    # Map old 'lam' parameter to 'laminate'  
    laminate = lam
    
    return calculate_decal_price_2025(width, height, qty, material, cut_type, laminate)


def true_cost_decal_2025(width, height, qty, material='gloss', cut='kiss', lam=None):
    """
    Wrapper for backward compatibility.
    Maps old parameter names to new function.
    """
    cut_type = cut
    laminate = lam
    
    return calculate_decal_true_cost_2025(width, height, qty, material, cut_type, laminate)