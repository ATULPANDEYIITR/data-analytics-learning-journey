#!/usr/bin/env python3
"""
SQL Performance Laboratory

This self-contained program models and analyzes PostgreSQL-style query
performance concepts without requiring a live database server.

It demonstrates:
- sequential scans
- index scans
- filtering efficiency
- composite and partial indexes
- selectivity
- join optimization
- nested-loop, hash-join, and merge-join reasoning
- query-plan interpretation
- estimated versus actual row counts
- predicate placement
- covering indexes
- common performance mistakes
- a small cost-based plan simulator

The program uses an e-commerce order workload because it naturally produces
high-cardinality identifiers, selective filters, date ranges, joins, and
aggregations that expose meaningful SQL performance differences.

The calculations are educational approximations. PostgreSQL's real planner
uses table statistics, histograms, correlation, visibility maps, cost
parameters, memory settings, parallelism, and many other factors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from math import ceil, log2
from random import Random
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Domain data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Customer:
    customer_id: int
    region: str
    tier: str


@dataclass(frozen=True)
class Order:
    order_id: int
    customer_id: int
    order_date: date
    status: str
    total_amount: float


@dataclass(frozen=True)
class Product:
    product_id: int
    category: str
    price: float


@dataclass(frozen=True)
class OrderItem:
    order_id: int
    product_id: int
    quantity: int


@dataclass
class IndexDefinition:
    name: str
    columns: tuple[str, ...]
    predicate: Optional[str] = None
    included_columns: tuple[str, ...] = ()


@dataclass
class PlanNode:
    node_type: str
    relation: str
    estimated_rows: int
    actual_rows: int
    startup_cost: float
    total_cost: float
    filter_rows_removed: int = 0
    children: list["PlanNode"] = field(default_factory=list)

    def print_tree(self, indent: int = 0) -> None:
        prefix = " " * indent
        print(
            f"{prefix}{self.node_type} on {self.relation}: "
            f"estimated={self.estimated_rows:,}, "
            f"actual={self.actual_rows:,}, "
            f"cost={self.startup_cost:.2f}..{self.total_cost:.2f}"
        )
        if self.filter_rows_removed:
            print(
                f"{prefix}  Rows Removed by Filter: "
                f"{self.filter_rows_removed:,}"
            )
        for child in self.children:
            child.print_tree(indent + 2)


# ---------------------------------------------------------------------------
# Synthetic workload generation
# ---------------------------------------------------------------------------

REGIONS = ("North", "South", "East", "West")
TIERS = ("standard", "silver", "gold", "enterprise")
STATUSES = ("pending", "paid", "shipped", "cancelled", "refunded")
CATEGORIES = ("hardware", "software", "networking", "security", "services")


def generate_workload(
    customer_count: int = 10_000,
    order_count: int = 100_000,
    product_count: int = 2_000,
    seed: int = 42,
) -> tuple[list[Customer], list[Order], list[Product], list[OrderItem]]:
    """Create a deterministic workload with realistic distributions."""
    rng = Random(seed)

    customers = [
        Customer(
            customer_id=customer_id,
            region=rng.choices(
                REGIONS,
                weights=(25, 30, 20, 25),
                k=1,
            )[0],
            tier=rng.choices(
                TIERS,
                weights=(55, 25, 15, 5),
                k=1,
            )[0],
        )
        for customer_id in range(1, customer_count + 1)
    ]

    products = [
        Product(
            product_id=product_id,
            category=rng.choice(CATEGORIES),
            price=round(rng.uniform(15, 5000), 2),
        )
        for product_id in range(1, product_count + 1)
    ]

    start_date = date(2026, 1, 1)
    orders: list[Order] = []

    for order_id in range(1, order_count + 1):
        order_date = start_date + timedelta(days=rng.randrange(273))
        customer_id = rng.randint(1, customer_count)

        # Paid and shipped orders dominate a production-like workload.
        status = rng.choices(
            STATUSES,
            weights=(5, 35, 45, 8, 7),
            k=1,
        )[0]

        amount = round(
            min(25000, max(10, rng.lognormvariate(5.2, 1.0))),
            2,
        )

        orders.append(
            Order(
                order_id=order_id,
                customer_id=customer_id,
                order_date=order_date,
                status=status,
                total_amount=amount,
            )
        )

    items: list[OrderItem] = []

    for order in orders:
        item_count = rng.randint(1, 5)
        for _ in range(item_count):
            items.append(
                OrderItem(
                    order_id=order.order_id,
                    product_id=rng.randint(1, product_count),
                    quantity=rng.randint(1, 4),
                )
            )

    return customers, orders, products, items


# ---------------------------------------------------------------------------
# Basic scan models
# ---------------------------------------------------------------------------

def sequential_scan(
    orders: Iterable[Order],
    predicate,
) -> tuple[list[Order], int]:
    """
    A sequential scan examines every row and evaluates the predicate.

    This is not inherently bad. It is often appropriate when a large fraction
    of a table qualifies, when the table is small, or when no useful index
    exists.
    """
    matches: list[Order] = []
    examined = 0

    for order in orders:
        examined += 1
        if predicate(order):
            matches.append(order)

    return matches, examined


def build_order_id_index(orders: Iterable[Order]) -> dict[int, Order]:
    """Represent a simple B-tree-like lookup structure for demonstration."""
    return {order.order_id: order for order in orders}


def build_customer_index(
    orders: Iterable[Order],
) -> dict[int, list[Order]]:
    """Represent an index on orders(customer_id)."""
    index: dict[int, list[Order]] = {}

    for order in orders:
        index.setdefault(order.customer_id, []).append(order)

    return index


def index_scan_by_customer(
    customer_index: dict[int, list[Order]],
    customer_id: int,
    predicate=None,
) -> tuple[list[Order], int]:
    """
    An index scan first narrows the candidate rows by customer_id.

    A second predicate may still be evaluated after the index lookup. This is
    important because using an index does not automatically mean every filter
    is performed by the index.
    """
    candidates = customer_index.get(customer_id, [])
    examined = 0
    matches: list[Order] = []

    for order in candidates:
        examined += 1
        if predicate is None or predicate(order):
            matches.append(order)

    return matches, examined


# ---------------------------------------------------------------------------
# Filtering efficiency
# ---------------------------------------------------------------------------

def filtering_demo(orders: list[Order]) -> None:
    print("\n=== Filtering Efficiency ===")

    target_status = "cancelled"
    target_date = date(2026, 9, 1)

    matches, examined = sequential_scan(
        orders,
        lambda order: (
            order.status == target_status
            and order.order_date >= target_date
        ),
    )

    print(f"Sequential scan examined: {examined:,} rows")
    print(f"Rows returned: {len(matches):,}")

    status_counts = {
        status: sum(order.status == status for order in orders)
        for status in STATUSES
    }

    print("Status distribution:")
    for status, count in status_counts.items():
        selectivity = count / len(orders)
        print(
            f"  {status:10} rows={count:7,} "
            f"selectivity={selectivity:6.2%}"
        )

    print(
        "\nA filter is efficient when the access path avoids examining "
        "large numbers of rows that will later be discarded."
    )


# ---------------------------------------------------------------------------
# Index design
# ---------------------------------------------------------------------------

def index_design_demo(orders: list[Order]) -> None:
    print("\n=== Index Design and Index Scans ===")

    customer_index = build_customer_index(orders)
    target_customer = 731

    customer_matches, examined = index_scan_by_customer(
        customer_index,
        target_customer,
    )

    print(
        f"Index lookup orders(customer_id={target_customer}) "
        f"examined {examined:,} candidate rows and returned "
        f"{len(customer_matches):,} rows."
    )

    recent_matches, recent_examined = index_scan_by_customer(
        customer_index,
        target_customer,
        lambda order: order.order_date >= date(2026, 9, 1),
    )

    print(
        f"Applying a second date filter returned {len(recent_matches):,} "
        f"rows after examining {recent_examined:,} indexed candidates."
    )

    print(
        "\nA composite index on (customer_id, order_date) can make the "
        "customer-plus-date predicate more selective because the date "
        "condition becomes part of the index access path."
    )


def composite_index_simulation(
    orders: list[Order],
) -> tuple[dict[tuple[int, date], list[Order]], int]:
    """
    Simulate the leading-key behavior of a composite index.

    A real B-tree index does not store a Python dictionary like this.
    The structure is intentionally simplified to make the access principle
    observable.
    """
    index: dict[tuple[int, date], list[Order]] = {}

    for order in orders:
        key = (order.customer_id, order.order_date)
        index.setdefault(key, []).append(order)

    target_customer = 731
    cutoff = date(2026, 9, 1)

    candidates = [
        rows
        for (customer_id, order_date), rows in index.items()
        if customer_id == target_customer and order_date >= cutoff
    ]

    examined = sum(len(rows) for rows in candidates)
    flattened = [order for rows in candidates for order in rows]

    return {(target_customer, cutoff): flattened}, examined


# ---------------------------------------------------------------------------
# Partial and covering index reasoning
# ---------------------------------------------------------------------------

def partial_index_demo(orders: list[Order]) -> None:
    print("\n=== Partial Index Reasoning ===")

    paid_orders = [order for order in orders if order.status == "paid"]

    print(f"Total orders: {len(orders):,}")
    print(f"Paid orders represented by partial index: {len(paid_orders):,}")

    print(
        "A PostgreSQL partial index such as "
        "CREATE INDEX ... ON orders(customer_id) "
        "WHERE status = 'paid' stores only qualifying rows."
    )

    customer_id = 731
    indexed_candidates = [
        order
        for order in paid_orders
        if order.customer_id == customer_id
    ]

    print(
        f"Partial-index candidates for paid customer "
        f"{customer_id}: {len(indexed_candidates):,}"
    )

    print(
        "A partial index is useful only when the query predicate implies "
        "the index predicate. A query for status='cancelled' cannot use "
        "an index whose entries contain only paid rows."
    )


def covering_index_demo(orders: list[Order]) -> None:
    print("\n=== Covering Index / Index-Only Scan Concept ===")

    print(
        "Suppose a report repeatedly asks for customer_id, order_date, "
        "and total_amount. An index on customer_id that INCLUDEs "
        "order_date and total_amount can provide those columns without "
        "fetching the heap tuple in favorable PostgreSQL visibility-map "
        "conditions."
    )

    target_customer = 731

    projected = [
        (
            order.customer_id,
            order.order_date,
            order.total_amount,
        )
        for order in orders
        if order.customer_id == target_customer
    ]

    print(
        f"Projected rows for customer {target_customer}: "
        f"{len(projected):,}"
    )


# ---------------------------------------------------------------------------
# Join algorithms
# ---------------------------------------------------------------------------

def nested_loop_join(
    customers: list[Customer],
    orders: list[Order],
) -> tuple[list[tuple[Customer, Order]], int]:
    """
    Naive nested-loop join.

    Complexity is O(N*M), which becomes expensive when both relations are
    large and no useful lookup structure exists.
    """
    output: list[tuple[Customer, Order]] = []
    comparisons = 0

    for customer in customers:
        for order in orders:
            comparisons += 1
            if order.customer_id == customer.customer_id:
                output.append((customer, order))

    return output, comparisons


def indexed_nested_loop_join(
    customers: list[Customer],
    customer_index: dict[int, list[Order]],
) -> tuple[list[tuple[Customer, Order]], int]:
    """
    Indexed nested-loop join.

    The outer relation drives the join while the inner relation is accessed
    through an index. The cost is approximately proportional to outer rows
    plus the number of matching inner rows, rather than outer*inner.
    """
    output: list[tuple[Customer, Order]] = []
    lookups = 0

    for customer in customers:
        lookups += 1
        for order in customer_index.get(customer.customer_id, []):
            output.append((customer, order))

    return output, lookups


def hash_join(
    customers: list[Customer],
    orders: list[Order],
) -> tuple[list[tuple[Customer, Order]], int]:
    """
    Hash join model.

    Build a hash table for the smaller input, then probe it using the other
    relation. Expected complexity is O(N+M) under normal hash behavior.
    """
    customer_map = {
        customer.customer_id: customer
        for customer in customers
    }

    output: list[tuple[Customer, Order]] = []
    probes = 0

    for order in orders:
        probes += 1
        customer = customer_map.get(order.customer_id)
        if customer is not None:
            output.append((customer, order))

    return output, probes


def join_optimization_demo(
    customers: list[Customer],
    orders: list[Order],
) -> None:
    print("\n=== Join Optimization ===")

    small_customers = customers[:100]
    small_orders = orders[:2_000]

    _, nested_comparisons = nested_loop_join(
        small_customers,
        small_orders,
    )

    order_index = build_customer_index(small_orders)

    _, indexed_lookups = indexed_nested_loop_join(
        small_customers,
        order_index,
    )

    _, hash_probes = hash_join(
        small_customers,
        small_orders,
    )

    print(
        f"Naive nested loop comparisons: {nested_comparisons:,}"
    )
    print(
        f"Indexed nested-loop lookups: {indexed_lookups:,}"
    )
    print(
        f"Hash join probes: {hash_probes:,}"
    )

    print(
        "\nThe PostgreSQL planner chooses among join strategies using "
        "estimated relation sizes, selectivity, available indexes, "
        "statistics, memory, and cost parameters."
    )


# ---------------------------------------------------------------------------
# Query-plan interpretation
# ---------------------------------------------------------------------------

def estimate_selectivity(
    total_rows: int,
    matching_rows: int,
) -> float:
    if total_rows <= 0:
        return 0.0
    return matching_rows / total_rows


def estimate_sequential_cost(
    rows: int,
    cpu_per_row: float = 0.01,
) -> float:
    return rows * cpu_per_row


def estimate_index_cost(
    table_rows: int,
    matching_rows: int,
    random_page_cost: float = 4.0,
    index_cpu_cost: float = 0.01,
) -> float:
    """
    Educational index cost approximation.

    PostgreSQL's real cost model is more sophisticated and does not reduce
    index access to this single formula.
    """
    if matching_rows == 0:
        return 0.0

    tree_height = max(1, ceil(log2(max(2, table_rows))))
    return (
        tree_height
        + matching_rows * random_page_cost * 0.05
        + matching_rows * index_cpu_cost
    )


def plan_comparison_demo(orders: list[Order]) -> None:
    print("\n=== Query Plan Cost Reasoning ===")

    total_rows = len(orders)
    target_customer = 731

    matching_rows = sum(
        order.customer_id == target_customer
        for order in orders
    )

    selectivity = estimate_selectivity(
        total_rows,
        matching_rows,
    )

    seq_cost = estimate_sequential_cost(total_rows)
    index_cost = estimate_index_cost(
        total_rows,
        matching_rows,
    )

    print(f"Table rows: {total_rows:,}")
    print(f"Matching rows: {matching_rows:,}")
    print(f"Estimated selectivity: {selectivity:.4%}")
    print(f"Approximate sequential cost: {seq_cost:.2f}")
    print(f"Approximate index cost: {index_cost:.2f}")

    if index_cost < seq_cost:
        print("Educational model favors an index access path.")
    else:
        print("Educational model favors sequential access.")

    plan = PlanNode(
        node_type="Index Scan",
        relation="orders",
        estimated_rows=matching_rows,
        actual_rows=matching_rows,
        startup_cost=1.5,
        total_cost=index_cost,
    )
    plan.print_tree()


def cardinality_mismatch_demo() -> None:
    print("\n=== Estimated vs Actual Cardinality ===")

    plan = PlanNode(
        node_type="Nested Loop",
        relation="orders + customers",
        estimated_rows=500,
        actual_rows=50_000,
        startup_cost=20.0,
        total_cost=2_000.0,
    )

    plan.print_tree()

    print(
        "\nA large estimated-versus-actual row mismatch can indicate stale "
        "statistics, data skew, correlated predicates, inadequate "
        "statistics targets, or assumptions that do not match the data."
    )


# ---------------------------------------------------------------------------
# Predicate and query-shape analysis
# ---------------------------------------------------------------------------

def query_shape_demo(orders: list[Order]) -> None:
    print("\n=== Predicate Shape and Filtering ===")

    cutoff = date(2026, 9, 1)

    sargable_matches = [
        order
        for order in orders
        if order.order_date >= cutoff
    ]

    non_sargable_style_matches = [
        order
        for order in orders
        if order.order_date.isoformat()[:7] == "2026-09"
    ]

    print(
        f"Range predicate rows: {len(sargable_matches):,}"
    )
    print(
        f"Expression-based month filtering rows: "
        f"{len(non_sargable_style_matches):,}"
    )

    print(
        "For a B-tree index on order_date, a direct range predicate such as "
        "order_date >= DATE '2026-09-01' AND order_date < DATE '2026-10-01' "
        "usually exposes an index-friendly search range."
    )

    print(
        "Wrapping an indexed column in an expression can prevent a normal "
        "index from being useful unless an appropriate expression index "
        "exists."
    )


# ---------------------------------------------------------------------------
# Index catalog
# ---------------------------------------------------------------------------

def print_index_catalog() -> None:
    print("\n=== Example Index Catalog ===")

    indexes = [
        IndexDefinition(
            name="orders_pkey",
            columns=("order_id",),
        ),
        IndexDefinition(
            name="idx_orders_customer_date",
            columns=("customer_id", "order_date"),
        ),
        IndexDefinition(
            name="idx_orders_paid_customer",
            columns=("customer_id",),
            predicate="status = 'paid'",
        ),
        IndexDefinition(
            name="idx_orders_customer_covering",
            columns=("customer_id",),
            included_columns=("order_date", "total_amount"),
        ),
    ]

    for index in indexes:
        description = f"{index.name}: ({', '.join(index.columns)})"
        if index.included_columns:
            description += (
                f" INCLUDE ({', '.join(index.included_columns)})"
            )
        if index.predicate:
            description += f" WHERE {index.predicate}"
        print(description)


# ---------------------------------------------------------------------------
# Practical diagnostics
# ---------------------------------------------------------------------------

def diagnostics_demo(orders: list[Order]) -> None:
    print("\n=== Practical Query Diagnostics ===")

    examples = [
        {
            "query_shape": "customer_id = constant",
            "index": "orders(customer_id)",
            "expected_access": "Index Scan or Bitmap Index/Heap Scan",
            "reason": "Selective equality predicate",
        },
        {
            "query_shape": "order_date >= start AND order_date < end",
            "index": "orders(order_date)",
            "expected_access": "Index Scan, Bitmap Scan, or Seq Scan",
            "reason": "Choice depends on selectivity and table characteristics",
        },
        {
            "query_shape": "status = 'paid'",
            "index": "partial index WHERE status='paid'",
            "expected_access": "Potentially small partial-index scan",
            "reason": "Index contains only rows relevant to the predicate",
        },
        {
            "query_shape": "customer_id = constant AND order_date >= cutoff",
            "index": "orders(customer_id, order_date)",
            "expected_access": "Composite index access",
            "reason": "Equality on leading key plus range on second key",
        },
    ]

    for item in examples:
        print(
            f"{item['query_shape']}\n"
            f"  index: {item['index']}\n"
            f"  likely access: {item['expected_access']}\n"
            f"  reason: {item['reason']}"
        )

    print(
        f"\nWorkload contains {len(orders):,} orders. "
        "Performance conclusions should be validated with EXPLAIN "
        "and EXPLAIN ANALYZE on the real PostgreSQL workload."
    )


# ---------------------------------------------------------------------------
# Common mistakes and safety checks
# ---------------------------------------------------------------------------

def common_mistakes_demo() -> None:
    print("\n=== Common SQL Performance Mistakes ===")

    mistakes = {
        "Index every column": (
            "Indexes consume storage, increase write cost, and create "
            "maintenance work. Indexes should serve real access patterns."
        ),
        "Assume an index is always faster": (
            "A sequential scan can be cheaper when a large percentage of "
            "rows qualifies or the table is small."
        ),
        "Ignore composite index order": (
            "B-tree indexes are ordered by their key sequence. "
            "An index on (customer_id, order_date) is not equivalent to "
            "(order_date, customer_id) for every query."
        ),
        "Optimize only the SELECT": (
            "Join cardinality, filtering before joins, aggregation volume, "
            "sorting, memory pressure, and data distribution can dominate."
        ),
        "Trust estimated rows blindly": (
            "Compare estimated and actual cardinalities using EXPLAIN "
            "ANALYZE and investigate substantial mismatches."
        ),
        "Benchmark without representative data": (
            "A plan that is good for a development table with 5,000 rows "
            "may be inappropriate for a production table with 500 million."
        ),
    }

    for mistake, explanation in mistakes.items():
        print(f"{mistake}: {explanation}")


# ---------------------------------------------------------------------------
# Mini workload benchmark
# ---------------------------------------------------------------------------

def benchmark_scan_strategies(orders: list[Order]) -> None:
    print("\n=== Scan Strategy Benchmark Model ===")

    targets = {
        "highly selective": lambda o: o.order_id == 75_000,
        "moderately selective": lambda o: o.customer_id == 731,
        "low selectivity": lambda o: o.status in {"paid", "shipped"},
    }

    customer_index = build_customer_index(orders)

    for label, predicate in targets.items():
        matches, examined = sequential_scan(orders, predicate)

        print(
            f"{label:20} "
            f"seq_examined={examined:7,} "
            f"rows={len(matches):7,}"
        )

    indexed_matches, indexed_examined = index_scan_by_customer(
        customer_index,
        731,
    )

    print(
        f"customer_id index   "
        f"index_candidates={indexed_examined:7,} "
        f"rows={len(indexed_matches):7,}"
    )

    print(
        "\nThe low-selectivity predicate is a useful reminder that an index "
        "can be less attractive when most of the table qualifies."
    )


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    print("SQL PERFORMANCE LABORATORY")
    print("=" * 72)
    print(
        "Workload: e-commerce orders, customers, products, and order items"
    )

    customers, orders, products, items = generate_workload()

    print(
        f"\nGenerated {len(customers):,} customers, "
        f"{len(orders):,} orders, "
        f"{len(products):,} products, "
        f"and {len(items):,} order items."
    )

    filtering_demo(orders)
    index_design_demo(orders)

    _, composite_examined = composite_index_simulation(orders)
    print(
        "\nComposite index simulation examined "
        f"{composite_examined:,} matching candidate rows."
    )

    partial_index_demo(orders)
    covering_index_demo(orders)
    join_optimization_demo(customers, orders)
    plan_comparison_demo(orders)
    cardinality_mismatch_demo()
    query_shape_demo(orders)
    print_index_catalog()
    diagnostics_demo(orders)
    common_mistakes_demo()
    benchmark_scan_strategies(orders)

    print("\n=== Production Validation Commands ===")
    print(
        "EXPLAIN (ANALYZE, BUFFERS) "
        "SELECT ...;"
    )
    print(
        "CREATE INDEX CONCURRENTLY idx_orders_customer_date "
        "ON orders(customer_id, order_date);"
    )
    print(
        "ANALYZE orders;"
    )
    print(
        "\nUse real execution plans and representative production-like "
        "data before accepting an index or join strategy."
    )


if __name__ == "__main__":
    main()
