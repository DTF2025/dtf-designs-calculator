# Decal Pricing (2025) — Drop‑In Module

## What to do (Replit dev):
1. **Delete all existing decal & lamination pricing code** in the app.
2. Add these two files to your project root (or a pricing/ folder):
   - `decal_pricing.py`
   - `decal_pricing_config.json`
3. Wherever you build a decal quote, call:

```python
from decal_pricing import price_decal

result = price_decal(
    w_in=width_inches,
    h_in=height_inches,
    qty=quantity,
    material=ui_material_label,   # 'Gloss Vinyl' or 'Matte Vinyl'
    cut_type=ui_cut_label,        # 'Kiss-Cut' or 'Die-Cut'
    laminate=ui_lam_label         # 'None' | 'Gloss' | 'Matte' | 'UV'
)
# result is a dict ready to jsonify for the UI
```

## Pricing model (from `decal_pricing_config.json`)
- Base retail: **$11.00/sq ft**
- Material adj: **Gloss $0** • **Matte +$0.50**
- Cut adj: **Kiss +$0.75** • **Die +$1.50** (per sq ft)
- Laminate adj: **None $0** • **Gloss/Matte +$2.00** • **UV +$2.50**
- Quantity discounts (auto‑apply to customer total):  
  25:10% • 50:15% • 100:20% • 250:25% • 500:30% • 1000:40%
- Partner price = **customer −30%**
- **Order minimum total = $25**

## Normalization
- Material: 'Gloss Vinyl'→gloss; 'Matte Vinyl'→matte (default gloss)
- Cut: 'Kiss‑Cut'→kiss; 'Die‑Cut'→die (default kiss)
- Laminate: 'None'/'Gloss'/'Matte'/'UV' (default none)

## Validation tests
1) **4x4, qty 25, Gloss, Kiss, None**  
   - Area each: 0.4444 sq ft → total 11.1111  
   - Rate/sqft: 11 + 0 + 0.75 + 0 = **$11.75**  
   - Subtotal: 11.1111 × 11.75 = **$130.56**  
   - Qty discount 10% → **$117.50** customer total  
   - Unit: **$4.70** • Partner total: **$82.25**  
   - (If app shows way lower/higher, something else is still running.)

2) **4x4, qty 25, Gloss, Kiss, Gloss Lam**  
   - Rate/sqft: 11 + 0 + 0.75 + 2.00 = **$13.75**  
   - Subtotal: 11.1111 × 13.75 = **$152.78**  
   - After 10%: **$137.50** customer total • Unit **$5.50**

3) **4x4, qty 25, Gloss, Die, None**  
   - Rate/sqft: 11 + 0 + 1.50 + 0 = **$12.50**  
   - Subtotal: 11.1111 × 12.50 = **$138.89**  
   - After 10%: **$125.00** customer total • Unit **$5.00**

4) **6x6, qty 10, Matte, Die, UV**  
   - Area each: 0.25 • total 2.5  
   - Rate/sqft: 11 + 0.5 + 1.5 + 2.5 = **$15.50**  
   - Subtotal: **$38.75** → below min → **$25.00** total • Unit **$2.50**

## Notes
- Change any numbers in the JSON — no code edits needed.
- Rounding: money to 2 decimals; area retained at 4 for transparency.
