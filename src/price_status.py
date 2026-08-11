def calculate_price_status(current_price, forecasted_price, discount_threshold=1.1, precision=2):
    """
    Determine the status of current price relative to forecasted price.

    Args:
        current_price (float): The current market price
        forecasted_price (float): The forecasted or target price
        discount_threshold (float): Higher value means more discounting (default is 1.1)
        precision (int): Decimal places for equality comparison.

        Discount threshold interpretation:
        # 1.1 means 10% discount, 1.2 means 20% discount, 2 means 50% discount, 
        # 4 means 75% discount, 10 means 90% discount
    Returns:
        str: 'premium', 'at par', or 'discount'
    """

    if not isinstance(current_price, (int, float)) or not isinstance(forecasted_price, (int, float)):
        raise ValueError("Prices must be numeric values")

    # Round for comparison
    current_rounded = round(current_price, precision)
    forecast_rounded = round(forecasted_price, precision)

    # Discount check first (lower price is better)
    if current_price < forecasted_price / discount_threshold:
        return "discount"

    # Equality check
    if current_rounded == forecast_rounded:
        return "at par"

    # Premium check
    if current_rounded > forecast_rounded:
        return "premium"

    # If slightly below forecast but not enough for discount
    return "at par"

if __name__ == "__main__":
    # Example usage
    current = 95.0
    forecast = 100.0
    discount = 2 # 50% discount threshold
    status = calculate_price_status(current, forecast, discount_threshold = discount)
    print(f"Current Price: {current}, Forecasted Price: {forecast}, Status: {status}")