from dataclasses import dataclass

import pandas as pd

from aridaq.constraints import (
    InventoryConstraints,
    validate_allocation,
)
from aridaq.objective import (
    ObjectiveWeights,
    calculate_product_value,
)


@dataclass(frozen=True)
class AllocationResult:
    """Final result returned by the optimizer."""

    allocation: dict[str, int]
    total_cost: float
    remaining_budget: float
    objective_value: float


def _calculate_priority(
    row: pd.Series,
    weights: ObjectiveWeights,
) -> float:
    """
    Calculate the optimization priority for one product.
    """

    return calculate_product_value(
        unit_margin=float(row["unit_margin"]),
        daily_sales_rate=float(row["daily_sales_rate"]),
        current_stock=float(row["current_stock"]),
        lead_time_demand=float(row["lead_time_demand"]),
        weights=weights,
    )


def optimize_inventory(
    data: pd.DataFrame,
    constraints: InventoryConstraints,
    weights: ObjectiveWeights | None = None,
) -> AllocationResult:
    """
    Allocate inventory budget across products.

    The optimizer uses a marginal-value greedy strategy:

    1. Calculate each product's optimization priority.
    2. Rank products by priority relative to purchase cost.
    3. Allocate units while respecting:
       - available budget
       - product maximums
       - inventory constraints

    This provides a fast deterministic baseline for Aridaq Commerce.
    """

    if data.empty:
        raise ValueError("Cannot optimize an empty dataset.")

    if weights is None:
        weights = ObjectiveWeights()

    required_columns = {
        "product_id",
        "cost_price",
        "unit_margin",
        "daily_sales_rate",
        "current_stock",
        "lead_time_demand",
        "max_stock",
    }

    missing = required_columns - set(data.columns)

    if missing:
        raise ValueError(
            "Optimizer is missing required columns: "
            + ", ".join(sorted(missing))
        )

    # Work on a copy so the original dataset is never modified.
    working = data.copy()

    # Calculate priority.
    working["priority"] = working.apply(
        lambda row: _calculate_priority(row, weights),
        axis=1,
    )

    # Convert priority into value per unit of purchase cost.
    working["value_per_cost"] = (
        working["priority"]
        / working["cost_price"].replace(0, float("nan"))
    )

    # Products with zero cost are handled separately.
    working["value_per_cost"] = (
        working["value_per_cost"]
        .replace([float("inf"), -float("inf")], float("nan"))
        .fillna(0.0)
    )

    # Rank highest-value opportunities first.
    working = working.sort_values(
        by="value_per_cost",
        ascending=False,
    )

    allocation: dict[str, int] = {}
    costs: dict[str, float] = {}

    remaining_budget = float(constraints.budget)

    for _, row in working.iterrows():

        product_id = str(row["product_id"])
        unit_cost = float(row["cost_price"])

        costs[product_id] = unit_cost

        if unit_cost <= 0:
            allocation[product_id] = 0
            continue

        # Never purchase beyond the product's maximum stock.
        stock_gap = max(
            float(row["max_stock"]) -
            float(row["current_stock"]),
            0.0,
        )

        maximum_units = int(stock_gap)

        # Respect global optimizer limit.
        maximum_units = min(
            maximum_units,
            constraints.maximum_purchase,
        )

        if maximum_units <= 0:
            allocation[product_id] = 0
            continue

        # Purchase as many units as the remaining budget permits.
        affordable_units = int(
            remaining_budget // unit_cost
        )

        units_to_purchase = min(
            maximum_units,
            affordable_units,
        )

        # Do not force a purchase when there isn't enough budget
        # for the configured minimum.
        if units_to_purchase < constraints.minimum_purchase:
            units_to_purchase = 0

        allocation[product_id] = units_to_purchase

        remaining_budget -= (
            units_to_purchase * unit_cost
        )

        if remaining_budget <= 0:
            remaining_budget = 0.0
            break

    # Ensure every product has an allocation entry.
    for product_id in data["product_id"].astype(str):
        allocation.setdefault(product_id, 0)

        if product_id not in costs:
            matching_rows = data[
                data["product_id"].astype(str) == product_id
            ]

            costs[product_id] = float(
                matching_rows.iloc[0]["cost_price"]
            )

    # Validate the final allocation.
    validate_allocation(
        allocation=allocation,
        costs=costs,
        constraints=constraints,
    )

    total_cost = sum(
        allocation[product_id] * costs[product_id]
        for product_id in allocation
    )

    objective_value = 0.0

    for _, row in working.iterrows():

        product_id = str(row["product_id"])

        objective_value += (
            allocation[product_id]
            * float(row["priority"])
        )

    return AllocationResult(
        allocation=allocation,
        total_cost=float(total_cost),
        remaining_budget=float(
            constraints.budget - total_cost
        ),
        objective_value=float(objective_value),
    )