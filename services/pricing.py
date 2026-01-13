"""Pricing service for calculating cleaning costs."""

from typing import Literal


def calculate_cleaning_price(
    cleaning_type: Literal["maintenance", "deep", "post_renovation"],
    property_type: Literal["apartment", "house"],
    area_m2: float
) -> dict[str, float | int]:
    """Calculate cleaning price based on type, property, and area.
    
    Formula:
    - Base price per m² depends on cleaning type
    - Property type multiplier (house costs more than apartment)
    - Area multiplier (larger areas get discount)
    
    Args:
        cleaning_type: Type of cleaning (maintenance, deep, post_renovation)
        property_type: Type of property (apartment, house)
        area_m2: Area in square meters
        
    Returns:
        Dictionary with pricing details:
        - base_price_per_m2: Base price per square meter
        - area_m2: Area in square meters
        - property_multiplier: Property type multiplier
        - price_before_discount: Price before area discount
        - discount_percent: Discount percentage (0-15)
        - discount_amount: Discount amount in UAH
        - final_price: Final price after discount
    """
    # Base prices per m² for different cleaning types (in UAH)
    base_prices = {
        "maintenance": 50.0,      # Підтримуюче - cheapest
        "deep": 80.0,              # Генеральне - standard
        "post_renovation": 120.0  # Після ремонту - most expensive
    }
    
    # Property type multipliers
    property_multipliers = {
        "apartment": 1.0,   # Base multiplier
        "house": 1.3        # Houses are 30% more expensive
    }
    
    # Area discount tiers (larger areas get better rates)
    if area_m2 <= 50:
        area_multiplier = 1.0      # No discount for small areas
        discount_percent = 0
    elif area_m2 <= 100:
        area_multiplier = 0.95    # 5% discount
        discount_percent = 5
    elif area_m2 <= 150:
        area_multiplier = 0.90    # 10% discount
        discount_percent = 10
    else:
        area_multiplier = 0.85    # 15% discount for large areas
        discount_percent = 15
    
    # Calculate base price
    base_price_per_m2 = base_prices[cleaning_type]
    
    # Apply multipliers
    property_multiplier = property_multipliers[property_type]
    
    # Calculate price before discount
    price_before_discount = base_price_per_m2 * area_m2 * property_multiplier
    
    # Calculate final price with discount
    final_price = price_before_discount * area_multiplier
    
    # Calculate discount amount
    discount_amount = price_before_discount - final_price
    
    return {
        "base_price_per_m2": round(base_price_per_m2, 2),
        "area_m2": round(area_m2, 2),
        "property_multiplier": property_multiplier,
        "price_before_discount": round(price_before_discount, 2),
        "discount_percent": discount_percent,
        "discount_amount": round(discount_amount, 2),
        "final_price": round(final_price, 2)
    }

