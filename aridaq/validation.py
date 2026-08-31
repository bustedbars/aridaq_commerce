from typing import Iterable

REQUIRED_COLUMNS = {
    "product_id",
    "product_name",
    "category",
    "cost_price",
    "selling_price",
    "current_stock",
    "units_sold",
    "days_observed",
    "lead_time_days",
    "min_stock",
    "max_stock",
}


def validate_columns(columns: Iterable[str]) -> None:
    """
    Validate that an incoming store dataset contains
    every field required by Aridaq Commerce.
    """
    provided = set(columns)
    missing = REQUIRED_COLUMNS - provided

    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(
            f"Missing required columns: {missing_list}"
        )


def validate_values(rows) -> None:
    """
    Validate basic business and inventory constraints.
    """
    for row_number, row in enumerate(rows, start=1):
        if row["cost_price"] < 0:
            raise ValueError(
                f"Row {row_number}: cost_price cannot be negative."
            )

        if row["selling_price"] < 0:
            raise ValueError(
                f"Row {row_number}: selling_price cannot be negative."
            )

        if row["selling_price"] < row["cost_price"]:
            raise ValueError(
                f"Row {row_number}: selling_price is below cost_price."
            )

        if row["current_stock"] < 0:
            raise ValueError(
                f"Row {row_number}: current_stock cannot be negative."
            )

        if row["units_sold"] < 0:
            raise ValueError(
                f"Row {row_number}: units_sold cannot be negative."
            )

        if row["days_observed"] <= 0:
            raise ValueError(
                f"Row {row_number}: days_observed must be greater than zero."
            )

        if row["lead_time_days"] < 0:
            raise ValueError(
                f"Row {row_number}: lead_time_days cannot be negative."
            )

        if row["min_stock"] < 0:
            raise ValueError(
                f"Row {row_number}: min_stock cannot be negative."
            )

        if row["max_stock"] < row["min_stock"]:
            raise ValueError(
                f"Row {row_number}: max_stock cannot be below min_stock."
            )