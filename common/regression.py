import numpy as np
def calculate_trend(data, window=None):
    """
    Calculate linear trend of time series data.
    
    Parameters:
    - data: array-like time series
    - window: optional window for calculating trend
    
    Returns:
    - slope, intercept
    """
    if window is not None and len(data) > window:
        data = data[-window:]
    
    # Create x-axis (time index)
    x = np.arange(len(data))
    y = np.asarray(data)
    
    # Clean data
    mask = np.isfinite(y)
    if np.sum(mask) < 2:  # Need at least 2 points
        return np.nan, np.nan
    
    x_clean = x[mask]
    y_clean = y[mask]
    
    try:
        coefficients = np.polyfit(x_clean, y_clean, 1)
        return coefficients[0], coefficients[1]  # slope, intercept
    except:
        return np.nan, np.nan
    
if __name__ == "__main__":
    # Example usage
    data = [1, 2, 3, 4, 5, np.nan, 7, 8]
    slope, intercept = calculate_trend(data)
    print(f"Slope: {slope}, Intercept: {intercept}")

