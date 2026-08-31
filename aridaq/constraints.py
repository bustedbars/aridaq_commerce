from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryConstraints:
    """
    Constraints governing an inventory allocation.

    budget:
        Maximum amount available for purchasing inventory.

    minimum_purchase:
        Minimum number of units that may be purchased for a product.

    maximum_purchase:
        Maximum number of units that may be purchased for a product.
    """

    budget: float
    minimum_purchase: int = 0
    maximum_purchase: int = 100000


def validate_constraints(constraints: InventoryConstraints) -> None:
    """Validate the inventory constraints."""

    if constraints.budget <= 0:
        raise ValueError("Inventory budget must be greater than zero.")

    if constraints.minimum_purchase < 0:
        raise ValueError("minimum_purchase cannot be negative.")

    if constraints.maximum_purchase < 0:
        raise ValueError("maximum_purchase cannot be negative.")

    if constraints.maximum_purchase < constraints.minimum_purchase:
        raise ValueError(
            "maximum_purchase cannot be less than minimum_purchase."
        )


def validate_allocation(
    allocation: dict[str, int],
    costs: dict[str, float],
    constraints: InventoryConstraints,
) -> None:
    """
    Verify that a proposed allocation satisfies all constraints.
    """

    validate_constraints(constraints)

    total_cost = 0.0

    for product_id, quantity in allocation.items():

        if quantity < constraints.minimum_purchase:
            raise ValueError(
                f"{product_id}: allocation is below minimum purchase."
            )

        if quantity > constraints.maximum_purchase:
            raise ValueError(
                f"{product_id}: allocation exceeds maximum purchase."
            )

        if product_id not in costs:
            raise ValueError(
                f"{product_id}: cost information is missing."
            )

        if costs[product_id] < 0:
            raise ValueError(
                f"{product_id}: cost cannot be negative."
            )

        total_cost += quantity * costs[product_id]

    if total_cost > constraints.budget + 1e-9:
        raise ValueError(
            "Proposed allocation exceeds the available inventory budget."
        )


def calculate_remaining_budget(
    allocation: dict[str, int],
    costs: dict[str, float],
    budget: float,
) -> float:
    """Return the budget remaining after an allocation."""

    spent = sum(
        quantity * costs[product_id]
        for product_id, quantity in allocation.items()
    )

    return max(budget - spent, 0.0)