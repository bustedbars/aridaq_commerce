from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectiveWeights:
    """
    Controls the relative importance of each optimization component.

    All weights must be non-negative.
    """

    profit: float = 1.0
    demand: float = 1.0
    stock_coverage: float = 0.5
    stock_risk: float = 0.75


def validate_weights(weights: ObjectiveWeights) -> None:
    """Ensure objective weights are valid."""

    values = {
        "profit": weights.profit,
        "demand": weights.demand,
        "stock_coverage": weights.stock_coverage,
        "stock_risk": weights.stock_risk,
    }

    for name, value in values.items():
        if value < 0:
            raise ValueError(
                f"Objective weight '{name}' cannot be negative."
            )

    if sum(values.values()) == 0:
        raise ValueError(
            "At least one objective weight must be greater than zero."
        )


def calculate_product_value(
    unit_margin: float,
    daily_sales_rate: float,
    current_stock: float,
    lead_time_demand: float,
    weights: ObjectiveWeights,
) -> float:
    """
    Calculate a normalized optimization value for a product.

    Higher values indicate stronger priority for additional
    inventory, subject to the constraints handled elsewhere.

    This is deliberately transparent rather than a black-box
    prediction model.
    """

    validate_weights(weights)

    # Profit contribution.
    profit_component = max(unit_margin, 0.0)

    # Demand contribution.
    demand_component = max(daily_sales_rate, 0.0)

    # Current inventory position.
    inventory_gap = max(
        lead_time_demand - current_stock,
        0.0,
    )

    stock_coverage_component = inventory_gap

    # Risk of carrying too little stock.
    stock_risk_component = (
        inventory_gap / max(lead_time_demand, 1.0)
    )

    value = (
        weights.profit * profit_component
        + weights.demand * demand_component
        + weights.stock_coverage * stock_coverage_component
        + weights.stock_risk * stock_risk_component
    )

    return float(value)