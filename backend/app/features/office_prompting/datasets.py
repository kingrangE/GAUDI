"""Synthetic relational dataset family for the office-prompting evaluation.

Three related CSV-shaped tables (customers / orders / products) are generated in
Python from a fixed seed, so every process produces byte-identical data. The
candidate sees ALL of it; the LLM receives all of it too (plus the candidate's
prompt). Problems (`problems.py`) require joining across these tables, so the
answer cannot be hand-computed from any single table.

Each table has >=200 rows and >=5 columns. IDs are zero-padded strings so the
generic ``{ids: [...]}`` extraction schema works uniformly across tables.
"""

import random

SEED = 20260624

# --- generation parameters ---------------------------------------------------
_N_CUSTOMERS = 240
_N_PRODUCTS = 200
_N_ORDERS = 600

_REGIONS = ("Seoul", "Busan", "Incheon", "Daegu", "Gwangju")
_SEGMENTS = ("consumer", "smb", "enterprise")
_CATEGORIES = ("가전", "가구", "의류", "식품", "도서")
_ORDER_STATUSES = ("paid", "paid", "paid", "cancelled", "refunded")  # weighted toward paid
_SUPPLIERS = ("한빛유통", "대성무역", "서일물산", "코어상사", "미래교역")

# Column order per table (stable rendering for CSV + UI).
COLUMNS: dict[str, list[str]] = {
    "customers": ["customer_id", "name", "region", "segment", "signup_date", "is_active"],
    "products": ["product_id", "name", "category", "price", "cost", "supplier"],
    "orders": ["order_id", "customer_id", "product_id", "quantity", "order_date", "status"],
}


def _date(rng: random.Random, year_choices: tuple[int, ...]) -> str:
    year = rng.choice(year_choices)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def _build() -> dict[str, list[dict]]:
    rng = random.Random(SEED)

    customers: list[dict] = []
    for i in range(1, _N_CUSTOMERS + 1):
        customers.append(
            {
                "customer_id": f"C{i:03d}",
                "name": f"고객{i:03d}",
                "region": rng.choice(_REGIONS),
                "segment": rng.choice(_SEGMENTS),
                "signup_date": _date(rng, (2022, 2023, 2024)),
                "is_active": rng.random() < 0.85,
            }
        )

    products: list[dict] = []
    for i in range(1, _N_PRODUCTS + 1):
        price = rng.randint(5, 120) * 1000  # 5,000 ~ 120,000
        cost = int(price * rng.uniform(0.45, 0.8))
        products.append(
            {
                "product_id": f"P{i:03d}",
                "name": f"상품{i:03d}",
                "category": rng.choice(_CATEGORIES),
                "price": price,
                "cost": cost,
                "supplier": rng.choice(_SUPPLIERS),
            }
        )

    customer_ids = [c["customer_id"] for c in customers]
    product_ids = [p["product_id"] for p in products]
    orders: list[dict] = []
    for i in range(1, _N_ORDERS + 1):
        orders.append(
            {
                "order_id": f"O{i:04d}",
                "customer_id": rng.choice(customer_ids),
                "product_id": rng.choice(product_ids),
                "quantity": rng.randint(1, 5),
                "order_date": _date(rng, (2023, 2024, 2024, 2024)),  # most in 2024
                "status": rng.choice(_ORDER_STATUSES),
            }
        )

    return {"customers": customers, "products": products, "orders": orders}


DATASETS: dict[str, list[dict]] = _build()
CUSTOMERS: list[dict] = DATASETS["customers"]
PRODUCTS: list[dict] = DATASETS["products"]
ORDERS: list[dict] = DATASETS["orders"]


def to_csv_text(name: str) -> str:
    """Render one table as compact CSV text (header + rows)."""
    cols = COLUMNS[name]
    lines = [",".join(cols)]
    for row in DATASETS[name]:
        lines.append(",".join(str(row[c]) for c in cols))
    return "\n".join(lines)


def datasets_csv_bundle() -> str:
    """All three tables as one text block with section headers, for the LLM."""
    return "\n\n".join(f"### {name}\n{to_csv_text(name)}" for name in COLUMNS)


def rows_by_ids(table: str, ids: list[str]) -> list[dict]:
    """Look up full rows for the given ids, preserving the table's row order."""
    id_col = COLUMNS[table][0]
    wanted = set(ids)
    return [row for row in DATASETS[table] if row[id_col] in wanted]


def existing_ids(table: str) -> set[str]:
    """All valid ids in a table (used to drop hallucinated ids before scoring)."""
    id_col = COLUMNS[table][0]
    return {row[id_col] for row in DATASETS[table]}
